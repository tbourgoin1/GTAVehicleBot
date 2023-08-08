import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
import os

DB_URL = 'REPLACE'
dbc = urlparse(DB_URL)
HOST_NAME = 'localhost' # change between localhost and dbc.hostname depending on if dev or prod, respectively
con = psycopg2.connect(
    dbname=dbc.path.lstrip('/'), user=dbc.username, password=dbc.password, host=HOST_NAME, port=dbc.port, sslmode='disable', cursor_factory=RealDictCursor
)
cursor = con.cursor()
con.autocommit = True

cursor = con.cursor()
cursor.execute("SELECT modelid, name FROM vehicleinfo limit 1")
vehicles_db_list = cursor.fetchall()
vehicles_list = {}

for veh in vehicles_db_list:
    #vehicles_list[veh['modelid']] = vehicles_list[veh['name']]
    vehicles_list[veh['modelid']] = veh['name']

print(vehicles_list)