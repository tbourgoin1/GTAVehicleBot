from urllib.parse import urlparse
import psycopg2 # db connection
from psycopg2.extras import RealDictCursor, execute_values
import os
import os.path
# requires indicated txt file to have list of vehicle names
# expected format is copied from patch notes - vehicle manufacturer + name, skipped lines

# format car names from site and put into an array
car_name_arr = []
car_names = open("txt_files/new_lockon_jammer_vehicles.txt", "r")
for line in car_names:
    if line != '' and line != '\n':
        line_arr = line.strip().split(" ")
        final_line = ""
        for i in range (0, len(line_arr)):
            if i != 0:
                final_line += line_arr[i] + " "
        car_name_arr.append(final_line.strip())

# connect to postgres DB
dbc = urlparse("DB_URL_HERE")
HOST_NAME = 'localhost' # change between 'localhost' and dbc.hostname depending on if dev or prod, respectively
conn = psycopg2.connect(
    dbname=dbc.path.lstrip('/'),
    user=dbc.username,
    password=dbc.password,
    host=HOST_NAME,
    port=dbc.port,
    sslmode='disable',
    cursor_factory=RealDictCursor
)
conn.autocommit = True
global cursor 
cursor = conn.cursor()

# query DB and update all vehicles' other notes
sql = "SELECT modelid, name, othernotes FROM vehicleinfo WHERE name = ANY(%s)"
cursor.execute(sql, (car_name_arr,))
db_cars = cursor.fetchall()

for car in db_cars:
    if car['othernotes']:
        if car['othernotes'].strip().lower() != 'none': # Append string to the cars that have othernotes
            car['othernotes'] = car["othernotes"] + '. Has missile lock on jammer.'
        else: # 'None' string othernotes
            car['othernotes'] = 'Has missile lock on jammer.'
    else: # actual blank othernotes
            car['othernotes'] = 'Has missile lock on jammer.'
    car['othernotes'] = car['othernotes'].replace('..', '.') # fix double peroids from above

    # update othernotes - multiple queries, simpler to write
    query = "UPDATE vehicleinfo SET othernotes = %s WHERE modelid = %s"
    cursor.execute(query, (car['othernotes'], car['modelid']))




