import psycopg2.pool
from psycopg2.extras import RealDictCursor, execute_values
from urllib.parse import urlparse
import time

dbc = urlparse('replace')
HOST_NAME = 'localhost' # change between localhost and dbc.hostname depending on if dev or prod, respectively
pool = psycopg2.pool.SimpleConnectionPool(
    1, # min num of connections
    3, # max num of connections
    dbname=dbc.path.lstrip('/'),
    user=dbc.username,
    password=dbc.password,
    host=HOST_NAME,
    port=dbc.port,
    sslmode='disable',
    cursor_factory=RealDictCursor
)
c1 = pool.getconn()
c2 = None
cursor = c1.cursor()
c1.autocommit = True

sql = "SELECT modelid FROM vehicleinfo limit 1"
cursor.execute(sql)
print(cursor.fetchall())

print(c1.closed)
print(c1.isolation_level)

def check_db_connection():
    global c1, c2, cursor, pool
    if c1:
        if c1.closed != 0:
            c2 = pool.getconn()
            cursor = c2.cursor()
            c2.autocommit = True
            pool.putconn(c1)
            c1 = None
    else:
        if c2.closed != 0:
            c1 = pool.getconn()
            cursor = c1.cursor()
            c1.autocommit = True
            pool.putconn(c2)
            c2 = None

check_db_connection()
sql = "SELECT modelid FROM vehicleinfo limit 1"
cursor.execute(sql)
print(cursor.fetchall())