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


def find_sheet_info(vehicle_name, spreadsheet_id, initial_range, range_adjustment, range_type, service):
    sheet = service.spreadsheets()
    all_vehicle_names = sheet.values().get(spreadsheetId=str(spreadsheet_id), range=str(initial_range)).execute() # finds all vehicle names in spreadsheet + other info
    vehicle_list = all_vehicle_names.get('values', []) # gets the values, or names of vehicles, from the results

    range_num = 0 # the (row number - row_adjustment) the vehicle will be found on
    formatted_vehicle_name = re.sub("-","", str(vehicle_name)) # removes dashes from vehicle name
    formatted_vehicle_name = re.sub("\s","",formatted_vehicle_name) # removes spaces from vehicle name

    for i in range(0, len(vehicle_list) - 1): # BUG: will find the first string that has the vehicle name, but might select wrong one (i.e. user searches for Roosevelt, but if Roosevelt Valor is first in the spreadsheet it'll pick that)
        formatted_vehicle_list_member = re.sub("-","", str(vehicle_list[i])) # removes dashes from vehicle name of current vehicle from list
        formatted_vehicle_list_member = re.sub("\s","", formatted_vehicle_list_member) # removes spaces from vehicle name of current vehicle from list
        if formatted_vehicle_name.lower() == str(formatted_vehicle_list_member).lower(): # if the car we want is found as an EXACT MATCH, set the range num to the row it's in and stop
            range_num = i + range_adjustment # adjusts for title rows of sheet
            break
        if formatted_vehicle_name.lower() in str(formatted_vehicle_list_member).lower(): # if the car we want is found as a partial match, set the range num to the row it's in
            range_num = i + range_adjustment # adjusts for title rows of sheet

    if(range_num == 0): # case of failing to find vehicle name in sheet
        return "ERROR: Vehicle not found in spreadsheet #" + str(range_type)
    else: # if successful, get and save that vehicle's information
        new_range = "" # will hold range to get specific vehicle info for this sheet
        if(range_type == 1):
            new_range = 'A' + str(range_num) + ':E' + str(range_num)
        elif(range_type == 2):
            new_range = 'Overall (Lap Time)!' + 'B' + str(range_num)
        elif(range_type == 3):
            new_range = 'Overall (Top Speed)!' + 'B' + str(range_num)
        elif(range_type == 4):
            new_range = 'Key Vehicle Info!' + 'C' + str(range_num) + ':L' + str(range_num)
        else:
            print("FAILED AT SETTING RANGE TYPE")
            return "FAILED AT SETTING RANGE TYPE"
        # Call the Sheets API
        sheet = service.spreadsheets()
        print("GOT HERE!")
        result = sheet.values().get(spreadsheetId=str(spreadsheet_id), range=str(new_range)).execute()
        print("GOT HERE AFTER!")
        temp_values = result.get('values', [])
        values = [] # final result will be put here
        if(range_type == 1):
            for row in temp_values: # gets the vehicle name, class, lap time, top speed, and image
                values.append('%s' % (row[0]))
                values.append('%s' % (row[1]))
                values.append('%s' % (row[2]))
                values.append('%s' % (row[3]))
                values.append('%s' % (row[4]))
        elif(range_type == 2 or range_type == 3):
            for row in temp_values: # gets vehicle lap time position in class for 2, or vehicle top speed position in class for 3
                values.append('%s' % (row[0]))
        elif(range_type == 4):
            for row in temp_values: # gets vehicle price, drivetrain, and # of seats
                values.append('%s' % (row[0]))
                values.append('%s' % (row[1]))
                values.append('%s' % (row[9]))
        else:
            print("FAILED AT SETTING RANGE TYPE")
            return "FAILED AT SETTING RANGE TYPE"

        return values



def main(vehicle_name):
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

    initial_range = 'A2:A1000' # used for the first range depending on the sheet to find the vehicle name in the sheet
    range_adjustment = 2 # must be 2 for my sheet to accomodate for title, 4 for all Broughy sheets
    # range type 1 = my sheet. 2 = brough, overall lap time. 3 = brough, overall top speed. 4 = brough, key vehicle info.
    return_me = find_sheet_info(vehicle_name, MY_SPREADSHEET_ID, initial_range, range_adjustment, 1, service) # either set to string error, or an array of some vehicle data (my sheet)
    if(return_me == "ERROR: Vehicle not found in spreadsheet #1"): # if failed finding vehicle in 1st sheet, stop
        print(return_me)
        return return_me
    else: # if successful with first sheet, continue
        range_adjustment = 4 # 4 for Broughy's sheets
        initial_range = 'Overall (Lap Time)!D4:D1000'
        output = find_sheet_info(vehicle_name, BROUGHYS_SPREADSHEET_ID, initial_range, range_adjustment, 2, service) # find lap time position data
        if(output == "ERROR: Vehicle not found in spreadsheet #2"): # if failed finding vehicle in 2nd sheet, stop
            print(output)
            return output
        else: # adds data to final product
            for data_point in output:
                return_me.append(data_point)
        
        initial_range = 'Overall (Top Speed)!D4:D1000'
        output = find_sheet_info(vehicle_name, BROUGHYS_SPREADSHEET_ID, initial_range, range_adjustment, 3, service) # find top speed poition data
        if(output == "ERROR: Vehicle not found in spreadsheet #3"): # if failed finding vehicle in 3rd sheet, stop
            print(output)
            return output
        else: # adds data to final product
            for data_point in output:
                return_me.append(data_point)
        
        initial_range = 'Key Vehicle Info!B4:B1000'
        output = find_sheet_info(vehicle_name, BROUGHYS_SPREADSHEET_ID, initial_range, range_adjustment, 4, service) # find price, drivetrain, # of seats
        if(output == "ERROR: Vehicle not found in spreadsheet #4"): # if failed finding vehicle in 4th sheet, stop
            print(output)
            return output
        else: # adds data to final product
            for data_point in output:
                return_me.append(data_point)
        
        print("FINAL PRODUCT:")
        print(return_me)
        return return_me


if __name__ == '__main__':
    main()