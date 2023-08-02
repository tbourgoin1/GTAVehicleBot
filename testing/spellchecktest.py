
# import the enchant module
import enchant
 
# the path of the text file
file_path = "carnames.txt"
 
# instantiating the enchant dictionary
# with request_pwl_dict()
d = enchant.request_pwl_dict(file_path)
 
# checking whether the words are
# in the new dictionary
print(d.check("10F"))

print(d.suggest("rh8"))


