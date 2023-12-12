import re

# requires indicated txt file to have list of vehicle model ids

car_names = open("txt_files/NEWDLC_modelids.txt", "r")
query_str = "INSERT INTO vehicleinfo (modelid) VALUES "
for line in car_names:
    line = line.strip()
    query_str += "('" + line + "'), "
query_arr = query_str.rsplit(", ", 1)
print(''.join(query_arr) + ";")