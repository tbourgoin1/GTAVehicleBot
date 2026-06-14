import psycopg2 # db connection
from psycopg2.extras import RealDictCursor, execute_values
from urllib.parse import urlparse
import re
import os
from dotenv import load_dotenv

load_dotenv()
dbc = urlparse(os.getenv('DATABASE_URL'))

PROCESS_UPDATES = True # UPDATE TO TRUE WHEN YOU WANT TO UPDATE VEHICLEINFO, FALSE TO JUST PRINT EVERYTHING OUT AS-IS TO UPDATE
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


update_arr = []
updated_cars = open("txt_files\\price_changes.txt", "r")
for car in updated_cars:
    car_arr = car.strip().split(",")
    car_arr[1] = int(car_arr[1])
    update_arr.append(car_arr)

    query_str = """UPDATE vehicleinfo AS v
                                    SET price = r.price
                                    FROM (VALUES %s) AS r(modelid, price)
                                    WHERE v.modelid = r.modelid;"""
    
    execute_values(cursor, query_str, update_arr)
    #print(update_arr)
    print('vehicleinfo updated!')