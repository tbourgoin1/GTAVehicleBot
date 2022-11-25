from __future__ import print_function
from distutils import command
import pickle
import os.path
import re
from typing import final
import special_vehicle_name_cases
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from fastDamerauLevenshtein import damerauLevenshtein

# USED FOR VEHICLEINFO

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

MY_SPREADSHEET_ID = '1jjIrthDyrqKeMkXzo2HnYKIzTbmOiSMDCh6n8BkTN54'


def check_for_exact_partial_matches(vehicle_name, vehicle_list_member, formatted_vehicle_list_member):
    # IF INPUT HAS EXACT PART OF WORD IN IT (i.e. input was hunter, find fh-1 hunter. not duster)
    words_of_input_name = vehicle_name.split() # splits the original input word spacewise
    words_of_cur_name = str(vehicle_list_member).split() # splits the current name we're looking at spacewise
    for word in words_of_input_name:
        word = re.sub("\W","", str(word)).lower() # format the word
        for cur_name_word in words_of_cur_name:
            cur_name_word = re.sub("\W","", str(cur_name_word)).lower() # format the current name
            if word == cur_name_word and cur_name_word != "custom":
                return_this = [word, formatted_vehicle_list_member]
                return return_this # return immediately once find a match, decide best case ratio later

def find_sheet_info(vehicle_name, spreadsheet_id, initial_range, range_adjustment, service):
    sheet = service.spreadsheets()
    all_vehicle_names = sheet.values().get(spreadsheetId=str(spreadsheet_id), range=str(initial_range)).execute() # finds all vehicle names in spreadsheet + other info
    vehicle_list = all_vehicle_names.get('values', []) # gets the values, or names of vehicles, from the results

    range_num = 0 # the (row number - row_adjustment) the vehicle will be found on
    formatted_vehicle_name = re.sub("\W","", str(vehicle_name)).lower() # removes all non letters/numbers from the specific vehicle we're looking at from query
    was_exact_match = False # for if the user provided string is < 4 chars. If not exact match, refuse to return. Otherwise, return.
    was_exact_partial_match = False # if the user provided string < 4 chars but it was one of the words of the vehicle. Don't too short them if so.
    was_partial_match = False # for trying to fix misspells. If the input was "beater" or "gasser" or something, don't try to detect misspells
    percentage_letters_matched = 0 # keeps track for partial matches. Chooses the partial match with the largest % of letters matched
    input_had_manufacturer = False # used for displaying too short or not found later

    # NON-EXACT PARTIAL % LETTERS MATCHED AND EXACT PARTIAL % LETTERS MATCHED. Use after this runs fully to compare which to pick at the end based on who's higher
    non_epm_pct = 0 # NON EXACT PARTIAL
    non_epm_chosen_range = 0 # the range we want to use for a non-exact-partial-match
    epm_chosen_range = 0 # the range we want to use for a exact-partial-match

    misspell_pct = 0 # % letters matched for misspellings. only used if no other matches
    misspell_chosen_range = 0
    
    # FOR EXACT PARTIAL MATCHES ONLY - the damerau ratio
    EP_percentage_letters_matched = 0

    # 2D ARRAY FOR VEHICLE NOT FOUND - vehicle_name, ratio
    not_found_suggestions = []

    # SPECIAL VEHICLE NAME CASES - find any special cases and fix the name before searching
    special_array = special_vehicle_name_cases.main(formatted_vehicle_name, 'vehicleinfo')
    formatted_vehicle_name = special_array[0]
    input_had_manufacturer = special_array[1]

    # START SEARCHING FOR VEHICLE
    for i in range(0, len(vehicle_list) - 1):
        vehicle_list_member = re.sub("[^a-zA-Z0-9 -]", "", str(vehicle_list[i])) # for potential use later for not found array
        formatted_vehicle_list_member = re.sub("\W","", str(vehicle_list[i])).lower() # removes all non letters from vehicle we're looking at
        # EXACT MATCH
        if str(formatted_vehicle_name.lower()) == str(formatted_vehicle_list_member).lower(): # if the car we want is found as an EXACT MATCH, set the range num to the row it's in and stop
            range_num = i + range_adjustment # adjusts for title rows of sheet
            print("EXACT MATCH: ", formatted_vehicle_list_member, " to query val: ", formatted_vehicle_name)
            was_exact_match = True
            break
        # IF THERE'S A SUBSET OF THE LETTERS IN A ROW AS IN THE CURRENT WORD, PARTIAL MATCH
        elif formatted_vehicle_name.lower() in str(formatted_vehicle_list_member).lower(): # partial match - part of word like "rhaps" or "verlier". spelled CORRECTLY
            was_partial_match = True
            ratio_matched = len(formatted_vehicle_name) / len(str(formatted_vehicle_list_member))
            if(ratio_matched > percentage_letters_matched): # if we have higher % of letters matched, switch to that i.e. turismo classic found first but loses to turismo r on input of "turismo"
                print("PARTIAL MATCH, PIECE OF WORD IN NAME: ", formatted_vehicle_list_member, " to query val: ", formatted_vehicle_name)
                print("NEW RATIO: ", ratio_matched)
                range_num = i + range_adjustment # adjusts for title rows of sheet
                percentage_letters_matched = ratio_matched
                non_epm_pct = ratio_matched
                non_epm_chosen_range = i + range_adjustment # sets the range to look for more info once we decide. adjusts for title rows of sheet
                is_car_added_to_not_found_list = False
                for not_found_vehicle in not_found_suggestions:
                    if(vehicle_list_member == not_found_vehicle[0]):
                        is_car_added_to_not_found_list = True
                        break
                if(not is_car_added_to_not_found_list):
                    not_found_suggestions.append([vehicle_list_member, ratio_matched, "NON EP"])
        
        # ANY OTHER CASE - MISSPELLINGS ETC. TREATED SEPARATELY ONLY IF NO OTHER OPTION
        else: 
            ratio_matched = damerauLevenshtein(formatted_vehicle_name.lower(), str(formatted_vehicle_list_member).lower()) # ratio of how similar the strings are, decimal 0 < x < 1
            if(ratio_matched > 0.5 and ratio_matched > misspell_pct and not was_partial_match): # record this separately in case we need later
                print("POTENTIAL MISSPELL FOUND: ", formatted_vehicle_list_member, " to query val: ", formatted_vehicle_name)
                print("MISSPELL RATIO: ", ratio_matched)
                range_num = i + range_adjustment # adjusts for title rows of sheet
                misspell_chosen_range = i + range_adjustment # sets the range to look for more info once we decide. adjusts for title rows of sheet
                misspell_pct = ratio_matched
                is_car_added_to_not_found_list = False
                for not_found_vehicle in not_found_suggestions:
                    if(vehicle_list_member == not_found_vehicle[0]):
                        is_car_added_to_not_found_list = True
                        break
                if(not is_car_added_to_not_found_list):
                    not_found_suggestions.append([vehicle_list_member, ratio_matched, "NON EP"])

        # ALWAYS CHECK EXACT PARTIAL MATCH AT THE END
        exact_partial_result = check_for_exact_partial_matches(vehicle_name, vehicle_list[i], formatted_vehicle_list_member) # array of 2 words
        if exact_partial_result is not None: # record and set exact partial match if there is one
            EP_ratio = damerauLevenshtein(str(exact_partial_result[0]).lower(), str(exact_partial_result[1]).lower()) # ratio of how similar the strings are, decimal 0 < x < 1
            if EP_ratio > EP_percentage_letters_matched and EP_ratio != 1.0: # don't take exact matches to other cars.
                print("EXACT PARTIAL RATIO HIGHER, CHANGED: ", exact_partial_result)
                print("NEW RATIO: ", EP_ratio)
                range_num = i + range_adjustment # adjusts for title rows of sheet
                epm_chosen_range = i + range_adjustment
                EP_percentage_letters_matched = EP_ratio
                for i in range(0, len(not_found_suggestions)): # search current not found suggs list to see if the car has been added to it already. If it has, add the EPM version since the ratio is better
                    print("NOT FOUND SUGGS, THEN LIST MEMBER: ", not_found_suggestions[i][0], vehicle_list_member)
                    if(not_found_suggestions[i][0] == vehicle_list_member):
                        not_found_suggestions.pop(i)
                        break
                not_found_suggestions.append([vehicle_list_member, EP_ratio, "EP"])
                
    # prioritize exact partial match and choose it if it's very good
    range_num_is_best_guess = False
    if(not was_exact_match and EP_percentage_letters_matched >= 0.8):
        print("range num set to epm: " + str(epm_chosen_range))
        range_num = epm_chosen_range
        range_num_is_best_guess = True
    # else if it did find a good partial match, always choose it over the exact partial match result
    elif(non_epm_pct > 0.8 and not was_exact_match): 
        print("range num set to non epm: " + str(non_epm_chosen_range))
        range_num = non_epm_chosen_range
        range_num_is_best_guess = True
    # choose a good misspell if last resort from other 2
    elif(misspell_pct > 0.8 and not was_exact_match):
        print("range num set to misspell: " + str(misspell_chosen_range))
        range_num = misspell_chosen_range
        range_num_is_best_guess = True
    
    print("Suggestions: " + str(not_found_suggestions))

    # include was_exact_match because it may try to partial match cars before we get to the exact and add them into not_found_suggestions
    if(range_num_is_best_guess or was_exact_match or len(not_found_suggestions) == 1): # found one definitive vehicle, whether the singular best guess or an exact match. Get this vehicle's info.
        return [str(range_num), was_exact_match]
    elif(len(not_found_suggestions) > 0): # didn't find one singular good exact or best guess vehicle but have at least 1 suggestion
        return ["TRY AGAIN: I have suggestions", not_found_suggestions]
    else: # case of failing to find vehicle name in sheet. No best guess, no suggestions.
        return ["ERROR: Vehicle not found", not_found_suggestions]
        



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

    initial_range = 'Vehicle Data!A2:A1000' # used for the first range depending on the sheet to find the vehicle name in the sheet

    range_adjustment = 2 # must be 2 for my sheet to accomodate for title
    print("INITIAL RANGE: " + initial_range)
    returned_result_info = find_sheet_info(vehicle_name, MY_SPREADSHEET_ID, initial_range, range_adjustment, service) # either set to string error, or an array of some vehicle data
    if("ERROR: Vehicle not found" in returned_result_info[0] or "TRY AGAIN: I have suggestions" in returned_result_info[0]):
        return returned_result_info # returns error msg and/or vehicle suggestions for bot.py
    final_range = 'Vehicle Data!' + 'A' + str(returned_result_info[0]) + ':O' + str(returned_result_info[0]) # construct range for sheet call
    was_exact_match = returned_result_info[1]
    temp_values_size = 14 # num of columns grabbed for vehicleinfo, to check to see if the size of the returned array is correct - if not then vehicle data is incomplete
    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=str(MY_SPREADSHEET_ID), range=str(final_range)).execute()
    temp_values = result.get('values', [])
    values = [] # final result will be put here
    for i in range(0, temp_values_size): # only check first 14 (index 0 - 13) since other notes can be blank
        if(temp_values[0][i] == ""): # if any are blank, return incomplete
            return "VEHICLE DATA INCOMPLETE!"
    for row in temp_values: # gets the vehicle name, class, lap time, top speed, image, handling flags, best match y/n, and customization video
        values.append('%s' % (row[0])) # name
        values.append('%s' % (row[1])) # class
        values.append('%s' % (row[2])) # lap time
        values.append('%s' % (row[3])) # top speed
        values.append('%s' % (row[4])) # img
        values.append('%s' % (row[5])) # handling flags
        if(not was_exact_match): # for telling if this was a best guess or not. true if was a guess
            values.append("Not Exact Match")
        else:
            values.append("Exact Match")
        values.append('%s' % (row[6])) # customization video
        values.append('%s' % ("#" + row[7])) # lap time position in class
        values.append('%s' % ("#" + row[8])) # top speed position in class
        values.append('%s' % (row[9])) # drivetrain
        values.append('%s' % (row[10])) # # seats
        values.append('%s' % (row[11])) # manufacturer
        values.append('%s' % (row[12])) # price
        if(row[13] == "-"):
                row[13] = "Base Game (2013)"
        values.append('%s' % (row[13])) # DLC
        try:
            values.append('%s' % (row[14])) # "Other Notes"
        except IndexError: # if no other notes, the arr will be too short. manually add none
            values.append('%s' % ("None"))
    return values


if __name__ == '__main__':
    main()