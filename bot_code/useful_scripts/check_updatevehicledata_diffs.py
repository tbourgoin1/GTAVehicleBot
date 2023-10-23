import psycopg2 # db connection
from psycopg2.extras import RealDictCursor, execute_values
from urllib.parse import urlparse
import os

DB_URL = "fill in"

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

cursor.execute("SELECT * FROM vehicleinfo")
vehicleinfo = cursor.fetchall()
cursor.execute("SELECT * FROM vehicleinfo_bak")
vehicleinfo_bak = cursor.fetchall()

path = "txt_files/updatevehicledata_diffs.txt"
file = open(path, 'w')
write_str = ""
diff_count = 0


for v in vehicleinfo:
    id = v['modelid']
    v_str = id
    v_bak_str = id
    keep = False
    for v_bak in vehicleinfo_bak:
        if id == v_bak['modelid']:
            for field in v_bak:
                if v[field] != v_bak[field]:
                    v_str += ", " + v[field]
                    v_bak_str += ", " + v_bak[field]
                    keep = True
            break
    if keep:
        write_str += v_str + "\n" + v_bak_str + "\n\n"
        diff_count += 1

if write_str:
    write_str = "DIFF COUNT: " + str(diff_count) + "\n\n" + write_str
    file.write(write_str)
else:
    file.write("no diffs!")

print('Success, result can be found in txt file')