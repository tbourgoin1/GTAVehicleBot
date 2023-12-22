# needed for broughy updated testing videos - likely will not be able to pull from gtacars.net right away

import psycopg2 # db connection
from psycopg2.extras import RealDictCursor, execute_values
from urllib.parse import urlparse
import re

DB_URL = "postgres://gtabot:XuLAyg71nAMVHSF@gtabot-db.flycast:5432/gtabot?sslmode=disable"

PROCESS_UPDATES = True # UPDATE TO TRUE WHEN YOU WANT TO UPDATE VEHICLEINFO

dbc = urlparse(DB_URL)
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

# use the above printed 2darray to update the data manually, then put it in broughy_updated_car_classes.txt for it to then process here
if not PROCESS_UPDATES:
    # change class to the one Broughy made a video on
    cursor.execute("SELECT modelid, laptime, topspeed, laptime_byclass, topspeed_byclass from vehicleinfo where class = 'Supers' ORDER BY laptime")
    vehicleinfo = cursor.fetchall()

    for v in vehicleinfo:
        print([v['modelid'], v['laptime'], v['topspeed'], v['laptime_byclass'], v['topspeed_byclass']])
    print("PROCESS_UPDATES is false, not updating vehicleinfo!")
else:
    update_arr = []
    updated_cars = open("txt_files/broughy_updated_car_classes.txt", "r")
    for car in updated_cars:
        car = re.sub(r"[^A-Za-z0-9 .:,_]","", car.strip())
        car_arr = car.split(",")
        for i in range(0, len(car_arr)):
            car_arr[i] = car_arr[i].lstrip()
        update_arr.append(car_arr)
        print(car_arr)
    query_str = """UPDATE vehicleinfo AS v
                                    SET laptime = r.laptime,
                                        topspeed = r.topspeed,
                                        laptime_byclass = r.laptime_byclass,
                                        topspeed_byclass = r.topspeed_byclass
                                    FROM (VALUES %s) AS r(modelid, laptime, topspeed, laptime_byclass, topspeed_byclass)
                                    WHERE v.modelid = r.modelid;"""
    execute_values(cursor, query_str, update_arr)
    print('vehicleinfo updated!')