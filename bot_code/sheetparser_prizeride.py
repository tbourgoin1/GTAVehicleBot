from __future__ import print_function
from calendar import c
from distutils import command
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
MY_SPREADSHEET_ID = '1jjIrthDyrqKeMkXzo2HnYKIzTbmOiSMDCh6n8BkTN54'
SHEETID = 1704002095 # check URL of sheet for gid=

def main(command_name, vehicle_name, current_or_future, image_link):
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

    initial_range = 'Prize Ride!A2:C100'
    sheet = service.spreadsheets()
    sheet_result = sheet.values().get(spreadsheetId=str(MY_SPREADSHEET_ID), range=str(initial_range)).execute() # finds all vehicle names in spreadsheet + other info
    prizeride_data = sheet_result.get('values', []) # gets the values, or names of vehicles, from the results
    
    if(command_name == 'prizerideupdate'):
        # modify current vehicle
        range_adj = 2 # adjust for zero based loops below and sheet title row
        if current_or_future == "Change Current":
            cur_range = 0
            del_future_range = 0
            is_car_in_future = False
            for i in range(0, len(prizeride_data) - 1):
                if prizeride_data[i][2] == 'Current':
                    cur_range = i + range_adj
                elif str(prizeride_data[i][0]).lower() == str(vehicle_name).lower():
                    del_future_range = i + range_adj
                    is_car_in_future = True
            final_range = 'Prize Ride!A' + str(cur_range) + ':B' + str(cur_range) # only change vehicle name and image link, not cur/future
            values = [
                [vehicle_name, image_link]
            ]
            body = {
                'majorDimension': 'ROWS',
                'values' : values
            }
            service.spreadsheets().values().update(
                spreadsheetId=MY_SPREADSHEET_ID, 
                valueInputOption='USER_ENTERED',
                range=final_range,
                body=body
            ).execute()

            # remove vehicle from future list if it exists
            if(is_car_in_future):
                batch_body = {
                    "requests": [
                        {
                            "deleteDimension": {
                                "range": {
                                    "sheetId": SHEETID,
                                    "dimension": "ROWS",
                                    "startIndex": del_future_range-1,
                                    "endIndex": del_future_range
                                }
                            }
                        }
                    ]
                }
                service.spreadsheets().batchUpdate(spreadsheetId=MY_SPREADSHEET_ID, body=batch_body).execute()




#############################################################################################################################################################

        elif current_or_future == "Add Future":
            for i in range(0, len(prizeride_data) - 1):
                if prizeride_data[i][2] == 'Future':
                    if str(prizeride_data[i][0]).lower() == str(vehicle_name).lower():
                        return "VEHICLE ALREADY ADDED!"

            # add row
            batch_body = {
                    "requests": [
                        {
                            "insertDimension": {
                                "range": {
                                    "sheetId": SHEETID,
                                    "dimension": "ROWS",
                                    "startIndex": len(prizeride_data),
                                    "endIndex": len(prizeride_data)+1
                                }
                            }
                        }
                    ]
                }
            service.spreadsheets().batchUpdate(spreadsheetId=MY_SPREADSHEET_ID, body=batch_body).execute()

            # insert new car
            values = [
                [vehicle_name, "", "Future"]
            ]
            body = {
                'majorDimension': 'ROWS',
                'values' : values
            }
            service.spreadsheets().values().update(
                spreadsheetId=MY_SPREADSHEET_ID, 
                valueInputOption='USER_ENTERED',
                range='Prize Ride!A' + str(len(prizeride_data)+1) + ':C' + str(len(prizeride_data)+1),
                body=body
            ).execute()



#############################################################################################################################################################
        elif current_or_future == "Remove Future":
            was_found = False
            for i in range(0, len(prizeride_data) - 1):
                if prizeride_data[i][2] == 'Future':
                    if str(prizeride_data[i][0]).lower() == str(vehicle_name).lower():
                        was_found = True
                        del_range = i + range_adj
                        batch_body = {
                            "requests": [
                                {
                                    "deleteDimension": {
                                        "range": {
                                            "sheetId": SHEETID,
                                            "dimension": "ROWS",
                                            "startIndex": del_range-1,
                                            "endIndex": del_range
                                        }
                                    }
                                }
                            ]
                        }
                        service.spreadsheets().batchUpdate(spreadsheetId=MY_SPREADSHEET_ID, body=batch_body).execute()
            if not was_found:
                return "VEHICLE NOT FOUND FOR REMOVAL!"


    return prizeride_data


if __name__ == '__main__':
    main()