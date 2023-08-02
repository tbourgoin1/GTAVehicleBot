from __future__ import print_function
import pickle
import os.path
import re
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

MY_SPREADSHEET_ID = '1jjIrthDyrqKeMkXzo2HnYKIzTbmOiSMDCh6n8BkTN54'

def main(number_of_vehicles, vehicle_class, metric):
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

    # gets all vehicle names, classes, lap times, top speeds, lap times by class, top speeds by class, and manufacturer
    sheet_range = "Vehicle Data!A2:L1000"
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    returned_info = sheet.values().get(spreadsheetId=str(MY_SPREADSHEET_ID), range=str(sheet_range)).execute()
    # vehicle name, class, lap time, top speed, image, handling flags, customization vid, lap time by class, top speed by class, drivetrain, # of seats, manufacturer
    temp_values = returned_info.get('values', [])
    unsorted_final_result = []
    final_result = [] # return this

    # distinguish what to order by
    index_to_use = 0
    if(metric == "Lap Time"):
        index_to_use = 7
    elif(metric == "Top Speed"):
        index_to_use = 8

    for vehicle in temp_values:
        if vehicle[1] == vehicle_class: # if our class matches exactly (they will be formatted the same post slash commands)...
            # see if its in the top "number_of_vehicles" and include it if so
            if(vehicle[index_to_use].isnumeric()): # for non-tuners cars, easily append it if whole field < number_of_vehicles
                if(int(vehicle[index_to_use]) <= number_of_vehicles):
                    unsorted_final_result.append(vehicle)
            elif("in Tuners" in vehicle[index_to_use]): # get the first number characters (position of non-tuners class)
                position_str = ""
                for char in vehicle[index_to_use]:
                    if char.isnumeric():
                        position_str += char
                    else:
                        break
                if int(position_str) <= number_of_vehicles:
                    vehicle[index_to_use] = position_str
                    unsorted_final_result.append(vehicle)
        elif(vehicle_class == "Tuners"): # if user selected tuners class, I need to do this differently
            tuners_position_str = ""
            unformatted_pos_str = vehicle[index_to_use]
            unformatted_pos_str = unformatted_pos_str[5:] # removes first few characters so there's no numbers until the Tuners position
            if(unformatted_pos_str != ""): # meaning we actually have a tuner car we're looking at
                did_we_hit_numbers_yet = False
                for char in unformatted_pos_str:
                    if char.isnumeric():
                        tuners_position_str += char
                        did_we_hit_numbers_yet = True
                    elif did_we_hit_numbers_yet:
                        break
                if int(tuners_position_str) <= number_of_vehicles:
                    vehicle[index_to_use] = tuners_position_str
                    unsorted_final_result.append(vehicle)
        
    # sort final result by lap time pos or top speed pos
    iterator = 0
    while iterator < number_of_vehicles:
        iterator+=1
        pop_me = 0
        for vehicle in unsorted_final_result: # append vehicles in order to final result
            if(int(vehicle[index_to_use]) == iterator):
                final_result.append(vehicle)
                unsorted_final_result.pop(pop_me)
                break
            pop_me += 1

    return final_result



if __name__ == '__main__':
    main()