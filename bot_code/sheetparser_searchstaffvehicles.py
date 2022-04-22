from __future__ import print_function
import pickle
import os.path
import re
import special_vehicle_name_cases
import sheetparser
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from fastDamerauLevenshtein import damerauLevenshtein

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

MY_SPREADSHEET_ID = '1jjIrthDyrqKeMkXzo2HnYKIzTbmOiSMDCh6n8BkTN54'

TEMP_VALUES_SIZE = 12 # number of columns

# FIND SHEET INFO
def main(staff_member, vehicle):
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
    sheet = service.spreadsheets()
    

    range_adjustment = 2 # must be 2 for garages sheets for title
    sheet_range = staff_member + ' Garages!B2:B1000' # skip header row
    sheet = service.spreadsheets()
    result = sheetparser.find_sheet_info(vehicle, MY_SPREADSHEET_ID, sheet_range, range_adjustment, service, 'staffvehicle')
    if("ERROR: Vehicle not found" in result or "TRY AGAIN: I have suggestions" in result):
        return result # returns error msg + vehicle suggestions for bot.py
    final_range = staff_member + ' Garages!' + 'A' + str(result[0]) + ':L' + str(result[0]) # construct range for sheet call
    result = sheet.values().get(spreadsheetId=str(MY_SPREADSHEET_ID), range=str(final_range)).execute() # get exact car details
    temp_values = result.get('values', [])
    values = [] # final values returned to bot.py
    for val in temp_values[0]: # if something not filled in, incomplete. other handling above so that'll fire first
        if not re.search('[a-zA-Z0-9]', str(val)): 
            return "VEHICLE DATA INCOMPLETE!"
    for row in temp_values: # puts all data into array
        for i in range(len(row)):
            values.append('%s' % row[i])
    
    values.append(staff_member) # append staff name to end
    return values

if __name__ == '__main__':
    main()