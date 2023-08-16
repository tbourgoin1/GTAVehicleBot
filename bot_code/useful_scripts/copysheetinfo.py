import psycopg2 # db connection
from psycopg2.extras import RealDictCursor, execute_values
from urllib.parse import urlparse
#from distutils import command
import pickle
import os.path
import re
from typing import final
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from fastDamerauLevenshtein import damerauLevenshtein

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

MY_SPREADSHEET_ID = '1jjIrthDyrqKeMkXzo2HnYKIzTbmOiSMDCh6n8BkTN54'

creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('sheets', 'v4', credentials=creds)
range = 'Vehicle Data!A2:O1000'

sheet = service.spreadsheets()
result = sheet.values().get(spreadsheetId=str(MY_SPREADSHEET_ID), range=str(range)).execute()
values = result.get('values', [])
#print(values)

dbc = urlparse(os.getenv("DATABASE_URL"))
HOST_NAME = 'localhost' # change between localhost and dbc.hostname depending on if dev or prod, respectively
con = psycopg2.connect(
    dbname=dbc.path.lstrip('/'), user=dbc.username, password=dbc.password, host=HOST_NAME, port=dbc.port, sslmode='disable', cursor_factory=RealDictCursor
)
cursor = con.cursor()
con.autocommit = True

cursor.execute('''SELECT EXISTS (
                    SELECT FROM pg_tables
                    WHERE tablename = 'sheetinfo'
        );''')
var = cursor.fetchone()['exists']
if var:
    cursor.execute("DROP TABLE sheetinfo;")

print("creating temp update table...")
temptable = '''CREATE TABLE sheetinfo (
                    modelid varchar(50),
                    custvideo varchar(50),
                    dlc varchar(100),
                    othernotes varchar(500));'''
print("creating temp sheet table")
cursor.execute(temptable)

cursor.execute('SELECT modelid, name, custvideo, dlc, othernotes FROM vehicleinfo;')

vehicleinfo = cursor.fetchall()
updated_info = [] # array of dicts

for row in values:
    row_name = re.sub("\W","",str(row[0]).strip().lower())
    if row_name != '$':
        for vehicle in vehicleinfo:
            if row_name == re.sub("\W","",str(vehicle['name']).strip().lower()): # found vehicle in sheet
                if row[6] == 'N/A':
                    row[6] = ''
                if row[13] == '-':
                    row[13] = "Base Game (2013)"
                othernotes = None
                try:
                    othernotes = row[14]
                except IndexError: # if no other notes, the arr will be too short. manually add none
                    wow = 1
                dict = {
                    'modelid' : vehicle['modelid'],
                    'custvideo' : row[6],
                    'dlc' : row[13],
                    'othernotes' : othernotes
                }
                updated_info.append(dict)
                break

# put updated vehicles into temp update table
columns = updated_info[0].keys()
query = "INSERT INTO sheetinfo ({}) VALUES %s".format(','.join(columns))
# puts dict values (car info) into a list of lists as a list
values = [[value for value in veh.values()] for veh in updated_info]
print("inserting into sheet table...")
execute_values(cursor, query, values)

ree = cursor.execute('''UPDATE vehicleinfo v
                            SET custvideo = vsheet.custvideo,
                                dlc = vsheet.dlc,
                                othernotes = vsheet.othernotes
                            FROM sheetinfo vsheet
                            WHERE v.modelid = vsheet.modelid;''')