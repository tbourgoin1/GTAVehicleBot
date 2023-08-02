
# import the enchant module
import enchant
import re
 
# the path of the text file
file_path = "ingame_car_names.txt"
 
# instantiating the enchant dictionary
# with request_pwl_dict()
d = enchant.request_pwl_dict(file_path)

input = 'sultan'
suggestions = []

# IF INPUT HAS EXACT PART OF WORD IN IT (i.e. input was hunter, find fh-1 hunter. not duster)
words_of_input_name = input.split()
f = open('ingame_car_names.txt', 'r')
ingame_car_names = f.readlines()
formatted_input = re.sub("\W","", str(input)).lower() 
print(formatted_input)
for car in ingame_car_names:
    car_words = car.split()
    for word in car_words:
        word = re.sub("\W","", str(word)).lower() # format the word
        if formatted_input == word:
            suggestions.append(car.strip())

# checking whether the words are in the new dictionary and adding
for sugg in d.suggest(input):
    if sugg not in suggestions:
        suggestions.append(sugg)

print(suggestions)