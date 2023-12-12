import re

# requires indicated txt file to have list of vehicle names

car_names = open("txt_files/NEWDLC_carnames.txt", "r")
for line in car_names:
    print(re.sub(r"[^a-z0-9]","", line.strip().lower()))