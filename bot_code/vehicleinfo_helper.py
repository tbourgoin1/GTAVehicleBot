import re
import enchant
import os

def find_vehicle(input, vehicles_list):
    result = input
    # eliminate manufacturer from input if it exists
    formatted_input = re.sub(r"[^a-z0-9 ]","", input.lower().strip()) # remove everything but spaces and alphanumeric   
    manufacturers = open("txt_files/car_makes.txt", "r")
    for mfr in manufacturers:
        mfr = mfr.lower().strip()
        if mfr in formatted_input:
            # special cases for bf/emperor manufacturers, these are the only three cases
            if formatted_input != 'emperor' and formatted_input != 'bf400' and formatted_input != 'emperor snow': 
                formatted_input = formatted_input.replace(mfr, "").strip()

    # format DB names for use in finding matches
    # vehicles_list is a dict with all vehicles -> modelid : unformatted vehicle name
    # formatted_vehicles is a dict with all vehicles -> modelid : formatted vehicle name
    formatted_vehicles = {}
   # print("vehicles_list: ", vehicles_list)
    for modelid in vehicles_list:
        formatted_vehicles[modelid] = re.sub(r"[^a-z0-9 ]","", vehicles_list[modelid].lower().strip())
    
    # spellcheck algos - detect exact and exact partial matches
    input_words = formatted_input.split() # splits the original input word spacewise
    exact_match = False
    misspell_suggestions = [] # array of arrays of suggestions [modelid, unformatted name]
    for word in input_words:
        for veh_modelid in formatted_vehicles:
            veh_name = formatted_vehicles[veh_modelid]
            if formatted_input == veh_name:
                exact_match = True
                result = [veh_modelid, formatted_input]
                print('result exact match: ', result)
                break
            else:
                dict_words = veh_name.split()
                for dict_word in dict_words:
                    if word == dict_word:
                        misspell_suggestions.append([veh_modelid, vehicles_list[veh_modelid]]) # unformatted name good for use in suggestions embed
                        break
        if exact_match:
            break

    # create dictionary txt file and run enchant misspell algo for more complex spelling errors
    if not exact_match:
        temp_dict_path = "txt_files/temp_dictionary.txt"
        temp_dict = open(temp_dict_path, 'w')
        write_str = ""
        for veh in formatted_vehicles:
            write_str += formatted_vehicles[veh] + "\n"
        temp_dict.write(write_str)
        # instantiating the enchant dictionary with request_pwl_dict(), requires txt file
        d = enchant.request_pwl_dict(temp_dict_path)

        # checking whether the words are in the new dictionary and adding the unformatted version for the embed
        for sugg in d.suggest(formatted_input):
            sugg_modelid = [i for i in formatted_vehicles if formatted_vehicles[i] == sugg][0]
            if sugg not in misspell_suggestions:
                misspell_suggestions.append([sugg_modelid, vehicles_list[sugg_modelid]])

        # decide based on spellcheck output what to do
        if len(misspell_suggestions) == 0: # car not found, no suggestions
            return ['not found', False, False]
        elif len(misspell_suggestions) == 1: # exactly one car suggestion found, return as guess
            result = misspell_suggestions[0] # array, one vehicle [modelid, unformatted name]
            return [result, False, True]
        else: # multiple members of array, multiple suggestions. return 2darray [[modelid, unformatted name], [modelid, unformatted name]...]
            # reformat the suggestions array to be 'correct looking' for the suggestions embed the user will see
            return [misspell_suggestions, False, False]
    else: # exact match
        return [result, True, False] # [modelid, formatted car name], was exact match, was guess
   