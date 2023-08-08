import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
import os

DB_URL = os.getenv("DATABASE_URL")
dbc = urlparse(DB_URL)
host_name = 'localhost' # change between localhost and dbc.hostname depending on if dev or prod, respectively
con = psycopg2.connect(
    dbname=dbc.path.lstrip('/'), user=dbc.username, password=dbc.password, host=host_name, port=dbc.port, sslmode='disable', cursor_factory=RealDictCursor
)

cursor = con.cursor()
sql = "SELECT * FROM vehicleinfo WHERE modelid = %s LIMIT 1"
vehicle = 'ninef'
cursor.execute(sql, [vehicle])
#cursor.execute("SELECT modelid, name, manufacturer, laptime, topspeed FROM vehicleinfo")
# fetch commands will actually remove the tuples from cursor, so you need to assign it to something and then do something with it
# RealDictCursor allows you to use the column name as the reference to the field. without it, it's integer indexes only
print(cursor.fetchone()['modelid'])
#record = cursor.fetchone()
#print(record['laptime'])

# con.commit() # commits changes to db
con.close()