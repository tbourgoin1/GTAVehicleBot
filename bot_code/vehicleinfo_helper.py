import re
import enchant

def find_vehicle(input):
    result = input
    # eliminate manufacturer from input if it exists
    formatted_input = input.lower().strip()
    manufacturers = open("txt_files/car_makes.txt", "r")
    for mfr in manufacturers:
        mfr = mfr.lower().strip()
        if mfr in formatted_input:
            # special cases for bf/emperor manufacturers, these are the only three cases
            if formatted_input != 'emperor' and formatted_input != 'bf400' and formatted_input != 'emperorsnow': 
                formatted_input = formatted_input.replace(mfr, "").strip()

    # spellcheck algos - we have lowercase input minus leading/trailing whitespace and \n
    # detect exact and exact partial matches

    dict_lines = open('txt_files/enchant_carname_dictionary.txt', 'r').readlines()
    #dict_lines = open('txt_files/temp.txt', 'r').readlines()
    input_words = formatted_input.split() # splits the original input word spacewise
    exact_match = False
    misspell_suggestions = []
    for word in input_words:
        for line in dict_lines:
            formatted_line = line.lower().strip()
            if formatted_input == formatted_line:
                exact_match = True
                result = formatted_input
                break
            else:
                formatted_line = formatted_line.split() # array of words
                for dict_word in formatted_line:
                    if word == dict_word:
                        misspell_suggestions.append(line.strip())
                        break
        if exact_match:
            break

    # run enchant misspell algo for more complex spelling errors
    if not exact_match:
        # instantiating the enchant dictionary with request_pwl_dict()
        d = enchant.request_pwl_dict('txt_files/enchant_carname_dictionary.txt')

        # checking whether the words are in the new dictionary and adding
        for sugg in d.suggest(formatted_input):
            if sugg not in misspell_suggestions:
                misspell_suggestions.append(sugg)

        # decide based on spellcheck output what to do
        if len(misspell_suggestions) == 0: # car not found, no suggestions
            return ['not found', False, False]
        elif len(misspell_suggestions) == 1: # exactly one car suggestion found, return as guess
            result = misspell_suggestions[0]
            return [result, False, True]
        else: # multiple members of array, multiple suggestions
            # reformat the suggestions array to be 'correct looking' for the suggestions embed the user will see
            formatted_carname_lines = open('txt_files/formatted_enchant_carname_dictionary.txt', 'r').readlines()
            final_misspell_suggestions = []
            for sugg in misspell_suggestions:
                print(sugg)
                for line in formatted_carname_lines:
                    formatted_line = line.replace('(', '').replace(')', '').lower().strip()
                    if sugg == formatted_line:
                        final_misspell_suggestions.append(line.strip())
            print('misspell suggs: ', final_misspell_suggestions)
            return [final_misspell_suggestions, False, False]
    else: # exact match
        return [result, True, False] # car name/status, was exact match, was guess
   