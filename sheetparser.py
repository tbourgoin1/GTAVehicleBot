from __future__ import print_function
import pickle
import os.path
import re
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
MY_SPREADSHEET_ID = '1jjIrthDyrqKeMkXzo2HnYKIzTbmOiSMDCh6n8BkTN54'
BROUGHYS_SPREADSHEET_ID = '1nQND3ikiLzS3Ij9kuV-rVkRtoYetb79c52JWyafb4m4'
RANGE = ''

def main(vehicle_name):
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
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







    # logic to find vehicle name in spreadsheet HERE
    sheet = service.spreadsheets()
    all_vehicle_names = sheet.values().get(spreadsheetId=MY_SPREADSHEET_ID, range='A2:A1000').execute() # looks at the entire A column (contains vehicle names). omits empties
    vehicle_list = all_vehicle_names.get('values', [])

    range_num = 0
    formatted_vehicle_name = re.sub("-","", str(vehicle_name)) # removes dashes from vehicle name
    formatted_vehicle_name = re.sub("\s","",formatted_vehicle_name) # removes spaces from vehicle name

    for i in range(0, len(vehicle_list) - 1): # BUG: will find the first string that has the vehicle name, but might select wrong one (i.e. user searches for Roosevelt, but if Roosevelt Valor is first in the spreadsheet it'll pick that)
        formatted_vehicle_list_member = re.sub("-","", str(vehicle_list[i])) # removes dashes from vehicle name of current vehicle from list
        formatted_vehicle_list_member = re.sub("\s","", formatted_vehicle_list_member) # removes spaces from vehicle name of current vehicle from list
        if formatted_vehicle_name.lower() == str(formatted_vehicle_list_member).lower(): # if the car we want is found as an EXACT MATCH, set the range num to the row it's in and stop
            range_num = i + 2
            print("ELLOE")
            break
        if formatted_vehicle_name.lower() in str(formatted_vehicle_list_member).lower(): # if the car we want is found as a partial match, set the range num to the row it's in
            range_num = i + 2
            print(formatted_vehicle_name.lower())
            print(str(formatted_vehicle_list_member).lower())

    if(range_num == 0):
        return "ERROR: Vehicle not found in 1st spreadsheet"
    else:
        RANGE = 'A' + str(range_num) + ':E' + str(range_num) # sets up new range
        # Call the Sheets API
        result = sheet.values().get(spreadsheetId=MY_SPREADSHEET_ID, range=RANGE).execute()
        temp_values = result.get('values', [])
        values = []
        for row in temp_values: # gets the vehicle name, class, lap time, top speed, and image
            values.append('%s' % (row[0]))
            values.append('%s' % (row[1]))
            values.append('%s' % (row[2]))
            values.append('%s' % (row[3]))
            values.append('%s' % (row[4]))

        if not values:
            print('No data found.')
            return "No data found in first spreadsheet."







        RANGE = '' # reset range to now start looking at Broughy's spreadsheet for lap time pos in class
        # FIND LAP TIME POSITION IN CLASS
        sheet = service.spreadsheets()
        all_vehicle_names = sheet.values().get(spreadsheetId=BROUGHYS_SPREADSHEET_ID, range='Overall (Lap Time)!D4:D1000').execute()
        vehicle_list = all_vehicle_names.get('values', [])
        range_num = 0

        for i in range(0, len(vehicle_list) - 1): # BUG: will find the first string that has the vehicle name, but might select wrong one (i.e. user searches for Roosevelt, but if Roosevelt Valor is first in the spreadsheet it'll pick that)
            formatted_vehicle_list_member = re.sub("-","", str(vehicle_list[i])) # removes dashes from vehicle name of current vehicle from list
            formatted_vehicle_list_member = re.sub("\s","", formatted_vehicle_list_member) # removes spaces from vehicle name of current vehicle from list
            if formatted_vehicle_name.lower() == str(formatted_vehicle_list_member).lower(): # if the car we want is found as an EXACT MATCH, set the range num to the row it's in and stop
                range_num = i + 4    
                break
            if formatted_vehicle_name.lower() in str(formatted_vehicle_list_member).lower(): # if the car we want is found as a partial match, set the range num to the row it's in
                range_num = i + 4

        if(range_num == 0):
            return "ERROR: Vehicle not found in 2nd spreadsheet"

        RANGE = 'Overall (Lap Time)!' + 'B' + str(range_num) # sets up new range
        result = sheet.values().get(spreadsheetId=BROUGHYS_SPREADSHEET_ID, range=RANGE).execute()
        temp_values = result.get('values', [])
        for row in temp_values:
            values.append('%s' % (row[0]))





        RANGE = '' # reset range to now start looking at Broughy's spreadsheet for top speed pos in class
        # FIND TOP SPEED POSITION IN CLASS
        all_vehicle_names = sheet.values().get(spreadsheetId=BROUGHYS_SPREADSHEET_ID, range='Overall (Top Speed)!D4:D1000').execute()
        vehicle_list = all_vehicle_names.get('values', [])
        range_num = 0

        for i in range(0, len(vehicle_list) - 1): # BUG: will find the first string that has the vehicle name, but might select wrong one (i.e. user searches for Roosevelt, but if Roosevelt Valor is first in the spreadsheet it'll pick that)
            formatted_vehicle_list_member = re.sub("-","", str(vehicle_list[i])) # removes dashes from vehicle name of current vehicle from list
            formatted_vehicle_list_member = re.sub("\s","", formatted_vehicle_list_member) # removes spaces from vehicle name of current vehicle from list
            if formatted_vehicle_name.lower() == str(formatted_vehicle_list_member).lower(): # if the car we want is found as an EXACT MATCH, set the range num to the row it's in and stop
                range_num = i + 4    
                break
            if formatted_vehicle_name.lower() in str(formatted_vehicle_list_member).lower(): # if the car we want is found as a partial match, set the range num to the row it's in
                range_num = i + 4

        if(range_num == 0):
            return "ERROR: Vehicle not found in 3rd spreadsheet"

        RANGE = 'Overall (Top Speed)!' + 'B' + str(range_num) # sets up new range
        result = sheet.values().get(spreadsheetId=BROUGHYS_SPREADSHEET_ID, range=RANGE).execute()
        temp_values = result.get('values', [])
        for row in temp_values:
            values.append('%s' % (row[0]))







        RANGE = '' # reset range to now start looking at Broughy's spreadsheet for price, drivetrain, and # of seats
        # FIND PRICE, DRIVETRAIN, AND # OF SEATS
        all_vehicle_names = sheet.values().get(spreadsheetId=BROUGHYS_SPREADSHEET_ID, range='Key Vehicle Info!B4:B1000').execute()
        vehicle_list = all_vehicle_names.get('values', [])
        range_num = 0

        for i in range(0, len(vehicle_list) - 1): # BUG: will find the first string that has the vehicle name, but might select wrong one (i.e. user searches for Roosevelt, but if Roosevelt Valor is first in the spreadsheet it'll pick that)
            formatted_vehicle_list_member = re.sub("-","", str(vehicle_list[i])) # removes dashes from vehicle name of current vehicle from list
            formatted_vehicle_list_member = re.sub("\s","", formatted_vehicle_list_member) # removes spaces from vehicle name of current vehicle from list
            if formatted_vehicle_name.lower() == str(formatted_vehicle_list_member).lower(): # if the car we want is found as an EXACT MATCH, set the range num to the row it's in and stop
                range_num = i + 4    
                break
            if formatted_vehicle_name.lower() in str(formatted_vehicle_list_member).lower(): # if the car we want is found as a partial match, set the range num to the row it's in
                range_num = i + 4

        if(range_num == 0):
            return "ERROR: Vehicle not found in 4th spreadsheet"

        RANGE = 'Key Vehicle Info!' + 'C' + str(range_num) + ':L' + str(range_num) # sets up new range
        result = sheet.values().get(spreadsheetId=BROUGHYS_SPREADSHEET_ID, range=RANGE).execute()
        result.get('values', []) # gets the top speed position in class
        temp_values = result.get('values', [])
        for row in temp_values:
            values.append('%s' % (row[0]))
            values.append('%s' % (row[1]))
            values.append('%s' % (row[9]))


        print(values)
        return values

if __name__ == '__main__':
    main()