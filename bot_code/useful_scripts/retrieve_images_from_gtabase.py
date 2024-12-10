from bs4 import BeautifulSoup # beautiful soup 4
import urllib
from urllib.request import urlopen, Request
import re
from email.mime import image
from logging import error
import os
from time import time
from typing import Iterable
from nextcord import Interaction, SlashOption
import nextcord
from nextcord.ext.commands.core import check
from dotenv import load_dotenv
from nextcord.ext import commands
import re # regex
import logging.handlers
import psycopg2 # db connection
from psycopg2.extras import RealDictCursor, execute_values
from urllib.parse import urlparse

dbc = urlparse('postgres://gtabot:XuLAyg71nAMVHSF@gtabot-db.flycast:5432/gtabot?sslmode=disable')
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


def scrape_site(url): # scrape the website with beautifulsoup
    bad_url = False
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        page = urlopen(req)
        html = page.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
    except urllib.error.HTTPError as e: # 404, in case there's a vehicle we've inserted into the DB that the site doesn't have yet
        bad_url = True
        pass

    if bad_url:
        return 'BAD URL'
    return soup

def find_img_url(veh): # check for 404 error and return the vehicle name if unfindable
    veh_name = veh['name']
    #removable_substrings = ['(HSW)', '(Drift)', '(Old)', '(New)']
    if '(HSW)' in veh_name or '(Drift)' in veh_name: # for vehicles with parenthesis in the name (hsw, drift, etc) use the regular variant's image
        index = veh_name.index(' (')
        veh_name = veh_name[:index].strip()
        #print(veh_name)
    veh_name = re.sub(r"[^a-zA-Z0-9 -]","", veh_name) # alphanumeric, spaces, dashes only
    print(veh_name)
    soup = scrape_site("https://www.gtabase.com/grand-theft-auto-v/vehicles/" + veh_name.strip().lower().replace(" ", "-")) # convert 'Stirling GT' to 'stirling-gt'
    if soup == 'BAD URL':
        soup = scrape_site("https://www.gtabase.com/grand-theft-auto-v/vehicles/" + veh['manufacturer'].strip().lower().replace(" ", "-") + '-' + veh_name.strip().lower().replace(" ", "-"))
        if soup == 'BAD URL':
            return '', True
    figure = soup.find('figure')
    img_url = 'https://www.gtabase.com' + figure.find('img')['src'] # extract image URL from site - there is only one 'figure' tag on the whole page, which contains the img we need 
    return img_url, False


def special_cases(veh):
    if veh['name'] == 'Dominator FX Interceptor':
        return 'https://www.gtabase.com/igallery/gta5-database/dominator-fx-interceptor-2-360.jpg'
    if veh['name'] == 'Sprunk Buffalo':
        return 'https://www.gtabase.com/images/jch-optimize/ng/images_gta-5_vehicles_sports_main_buffalo-sprunk.webp'
    if veh['name'] == 'Baller (New)':
        return 'https://www.gtabase.com/images/jch-optimize/ng/images_gta-5_vehicles_suvs_main_baller-2.webp'
    if veh['name'] == 'Baller (Old)':
            return 'https://www.gtabase.com/images/jch-optimize/ng/images_gta-5_vehicles_suvs_main_baller.webp'
    if veh['name'] == "Duke O'Death":
        return 'https://www.gtabase.com/images/jch-optimize/ng/images_gta-5_vehicles_muscle_main_duke-o-death.webp'

'''if veh['name'] == '':
        return ''
'''

cursor.execute("SELECT modelid, manufacturer, name, image, dlc FROM vehicleinfo")
original_veh_list = cursor.fetchall()

success_file = open("txt_files\gtabase_car_URLs.txt", 'w')
fail_file = open("txt_files\gtabase_failed_URLs.txt", 'w')

final_updated_img_urls = []

for veh in original_veh_list:
    #print(veh['modelid'])
    res = special_cases(veh) # hardcoded weird URL names for specific vehicles
    if(res):
        img_url = res
        #print(img_url)
        success_file.write(veh['modelid'] + ', ' + img_url + '\n')
        final_updated_img_urls.append([veh['modelid'], img_url])
    else:
        img_url, was_404 = find_img_url(veh)
        if(was_404):
            fail_file.write(veh['name'] + '\n')
            print(veh['name'] + " FAIL")
        else:
            #print(img_url)
            success_file.write(veh['modelid'] + ', ' + img_url + '\n')
            final_updated_img_urls.append([veh['modelid'], img_url])
