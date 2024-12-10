# scrapes gtaWIKI for all its car images based on what's present in vehicleinfo
# that doesn't already have a gtawiki image - change query to do those anyway


from bs4 import BeautifulSoup # beautiful soup 4
import urllib
from urllib.request import urlopen, Request
from email.mime import image
from logging import error
import os
from time import time
from nextcord.ext.commands.core import check
from dotenv import load_dotenv
from nextcord.ext import commands
import psycopg2 # db connection
from psycopg2.extras import RealDictCursor, execute_values
from urllib.parse import urlparse


def special_cases(veh_name):
    if veh_name == 'Dukes':
        return 'https://static.wikia.nocookie.net/gtawiki/images/5/53/Dukes-GTAV-front.png/revision/latest?cb=20150530114053'
    elif veh_name == 'Fränken Stange':
        return 'https://static.wikia.nocookie.net/gtawiki/images/6/63/Fr%C3%A4nkenStange-GTAV-front.png/revision/latest/scale-to-width-down/1000?cb=20191111175139'
    elif veh_name == 'Liberator':
        return 'https://static.wikia.nocookie.net/gtawiki/images/e/e0/Liberator-GTAV-front.png/revision/latest/scale-to-width-down/1000?cb=20160929162837'
    elif veh_name == 'FIB (Buffalo)':
        return 'https://static.wikia.nocookie.net/gtawiki/images/8/87/FIB-GTAV-front.png/revision/latest/scale-to-width-down/1000?cb=20151222203022'
    elif veh_name == 'Trailer (Christmas)':
        return 'https://static.wikia.nocookie.net/gtawiki/images/b/bc/TrailerS5-GTAOe-front.png/revision/latest/scale-to-width-down/1000?cb=20231214201124'
    elif veh_name == 'Trailer (Car carrier (Pack Man))':
        return 'https://static.wikia.nocookie.net/gtawiki/images/4/45/Tr2-GTAV-front.png/revision/latest/scale-to-width-down/1000?cb=20170512222606'
    elif veh_name == 'FIB (SUV)':
        return 'https://static.wikia.nocookie.net/gtawiki/images/c/cf/FIB2-GTAV-front.png/revision/latest/scale-to-width-down/1000?cb=20151217204743'
    elif veh_name == 'Trailer':
        return 'https://static.wikia.nocookie.net/gtawiki/images/6/6f/TrailerSContainer-GTAV-front.png/revision/latest/scale-to-width-down/1000?cb=20170513150459'
    elif veh_name == 'Tipper (4 wheels)':
        return 'https://static.wikia.nocookie.net/gtawiki/images/1/11/Tipper-GTAV-front.png/revision/latest/scale-to-width-down/1000?cb=20161018181108'
    elif veh_name == 'Tipper (6 wheels)':
        return 'https://static.wikia.nocookie.net/gtawiki/images/0/07/Tipper2-GTAV-front.png/revision/latest/scale-to-width-down/1000?cb=20161018181106'

def parse_site(url, attempt_type=0): # attempt type is for redos of special case URLs
    
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        figure = soup.find('figure', {'class' : 'pi-item pi-image', 'data-source' : 'front_image'})
        if figure:
            img_url = figure.find('a', href=True)['href']
            print(img_url)
            success_file.write(veh['modelid'] + ", " + img_url + '\n')
        else:
            raise Exception
    except Exception as e:
        if attempt_type == 2: # last attempt type number, no other solutions
            print('UNKNOWN PROBLEM WITH ' + veh['name'] + '\n')
            fail_file.write(veh['name'] + str(e) + '\n')
        elif attempt_type == 0: # try adding HD universe to the end
            return parse_site(url + '_(HD_Universe)', 1)
        elif attempt_type == 1: # try adding the car variant to the end
            return parse_site(url.replace('_(HD_Universe)', '') + '_(car)', 2)

load_dotenv()
dbc = urlparse(os.getenv('DATABASE_URL'))
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

user_input = input("1 = scrape site and put into txt file\n2 = retrieve from txt file and insert to DB\n")
if user_input == '1':

    cursor.execute("SELECT modelid, name, image FROM vehicleinfo WHERE image NOT LIKE 'https://static.wikia.nocookie.net/gtawiki/images%'")
    original_veh_list = cursor.fetchall()

    success_file = open("txt_files\gta_wiki_images_files\good_cars.txt", 'w')
    fail_file = open("txt_files\gta_wiki_images_files\gbad_cars.txt", 'w')

    for veh in original_veh_list:
        veh_name = veh['name']
        special_case_img_url = special_cases(veh_name)
        if special_case_img_url:
            print(special_case_img_url)
            success_file.write(veh['modelid'] + ", " + special_case_img_url + '\n')
        else:
            index = veh_name.find(' (')
            if index != -1:
                veh_name = veh_name[:index].strip()
            url = 'https://gta.fandom.com/wiki/' + veh_name.replace(" ", "_")
            parse_site(url)
elif user_input == '2':
    file = open("txt_files\gta_wiki_images_files\good_cars.txt", 'r')
    for line in file:
        line = line.strip().split(", ")
        cursor.execute("UPDATE vehicleinfo SET image = %s WHERE modelid = %s", (line[1], line[0]))
        print('updated ' + line[0])
        #break

else:
    print('bad INPUT!')