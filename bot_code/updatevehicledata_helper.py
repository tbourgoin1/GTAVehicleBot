from bs4 import BeautifulSoup # beautiful soup 4
import urllib
from urllib.request import urlopen, Request
import re


# CAUTION - HAVENT TESTED THIS YET ALL THE WAY THRROUGH. USED THE CHECK SCRAPE SCRIPT AND FIXED IT, LOOKS GOOD, BUT HAVENT USED WITH BOT
# CAN'T RUN THIS UNTIL GTACARS.NET HAS ALL UPDATED LAP TIME AND TOP SPEED INFO
# NOTE IMAGES NO LONGER SHOULD COME FROM GTACARS.NET - USE GTAWIKI. ADAPT move_images_to_gtawiki.py INTO HERE
# BUGGED FOR flags and price - sometimes price is 0 sometimes it's the trade price if it has one

def get_new_vehicle_data(url, modelid):
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        page = urlopen(req)
    except urllib.error.HTTPError as e: # 404, in case there's a vehicle we've inserted into the DB that the site doesn't have yet
        print(e)
        return

    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
     #print(soup.get_text()) # gets all webpage text, no HTML. 
    # Can parse from here or get HTML tags like below

    # dict of all DB info fields from broughy's site
    vehicle_info = {
        "modelid" : modelid,
        "manufacturer" : "",
        "name" : "",
        "class" : "",
        "laptime" : "",
        "topspeed" : "",
        "image" : "",
        "flags" : "",
        "laptime_byclass" : "",
        "topspeed_byclass" : "",
        "drivetrain" : "",
        "numseats" : "",
        "price" : ""
    }

    # GETTING MANUFACTURER - # gets the table item for manufacturer and its text value for use
    manufacturer = soup.find('a', href=re.compile(r'manufacturer='))
    if manufacturer: # Unknown may as well be treated as blank
        if manufacturer.text != 'Unknown':
            vehicle_info['manufacturer'] = manufacturer.text

    # GETTING NAME -  # get title tag's text, take the text before the first '—'. That's the name + special like HSW
    name = soup.find('title')
    if name:
       vehicle_info["name"] = name.text.split('—')[0].strip()
    print(vehicle_info["name"])
    

    # GETTING CLASS
    classes = soup.findAll('a', href=re.compile(r'filter_race_class='))
    print(classes)
    if classes:
        classes_string = ""
        for c in classes:
            c = c.text
            if "Tier" not in c and "out of" not in c:
                if not classes_string:
                    classes_string += c
                else:
                    classes_string += (", " + c)
        vehicle_info["class"] = classes_string
    else:
        no_race_class = soup.find('a', href=re.compile(r'filter_class='))
        if no_race_class:
            vehicle_info["class"] = no_race_class.text + " (Not Raceable)"
    
    # GETTING LAP TIME AND TOP SPEED - handle where it does and doesn't have this info
    lt_ts_arr = soup.findAll('p')
    lap_time = ""
    top_speed = ""
    for i in range(0, len(lt_ts_arr)):
        if lt_ts_arr[i].text == 'Lap Time':
            if lt_ts_arr[i+1].text == 'Mid DF': # the <p> after when it says lap time/top speed is the value unless F1
                lap_time = lt_ts_arr[i+2].text
            else:
                lap_time = lt_ts_arr[i+1].text
        if lt_ts_arr[i].text == 'Top Speed':
            if lt_ts_arr[i+1].text == 'Mid DF': # the <p> after when it says lap time/top speed is the value unless F1
                top_speed = lt_ts_arr[i+2].text
            else:
                top_speed = lt_ts_arr[i+1].text
            
            top_speed = (float(top_speed.replace('km/h', '').replace("*","").strip()) / 1.609) * 4 # convert to mph + round to nearest .25
            top_speed = str(int((top_speed / 4)))
            break
    
    # None or set by site, accomodate
    if lap_time:
        vehicle_info["laptime"] = lap_time.replace("*", "")
    else:
        vehicle_info["laptime"] = lap_time
    vehicle_info["topspeed"] = top_speed
    
    # GETTING IMAGE
    # will always be the 1st image that appears when you open the car page
    # ...which is the best image and the one we want to use
    image = soup.find('meta', {"property":"og:image"})
    if image["content"]:
        vehicle_info["image"] = "https://gtacars.net" + image["content"] # this format will display in the bot correctly

    # GETTING HANDLING FLAGS
    flags = soup.findAll('a', href=re.compile(r'&filter_tag_a=')) # tag 'a' only gets the advanced flags
    flags_arr = []
    flags_str = ""
    for flag in flags:
        if flag.text == 'hard_rev_limit':
            flags_arr.append('Engine')
        elif flag.text == 'increase_suspension_force_with_speed':
            flags_arr.append('Bouncy')
        elif flag.text == 'reduce_body_roll_with_suspension_mods':
            flags_arr.append('Suspension')

    if len(flags_arr) > 0:
        flags_str = ":warning: "
        for i in range(0, len(flags_arr)):
            if i < (len(flags_arr)- 1):
                flags_str += flags_arr[i] + ", "
            else:
                flags_str += flags_arr[i]
    else:
        flags_str = ":white_check_mark: None"
    vehicle_info["flags"] = flags_str
    
    # GETTING LAP TIME BY CLASS
    ltbc = soup.findAll('a', href=re.compile(r'sort=lap_time&filter_race_class='))
    ltbc_str = ""
    if ltbc:
        for i in range(0, len(ltbc)):
            if i < (len(ltbc) - 1):
                ltbc_str += ltbc[i].text + ", "
            else:
                ltbc_str += ltbc[i].text
        vehicle_info["laptime_byclass"] = ltbc_str # if not present, it'll stay an empty string

    # GETTING TOP SPEED BY CLASS
    tsbc = soup.findAll('a', href=re.compile(r'sort=top_speed&filter_race_class='))
    tsbc_str = ""
    if tsbc:
        for i in range(0, len(tsbc)):
            if i < (len(tsbc) - 1):
                tsbc_str += tsbc[i].text + ", "
            else:
                tsbc_str += tsbc[i].text
        vehicle_info["topspeed_byclass"] = tsbc_str # if not present, it'll stay an empty string
    
    # GETTING DRIVETRAIN - stuff like helis don't have this, so need to accomodate that
    drivetrain = soup.find('a', href=re.compile(r'drivetrain='))
    dt_str = ""
    if drivetrain:
        dt_array = drivetrain.text.split(" ")
        if dt_array[0] == "Rear":
            dt_str = "RWD"
        elif dt_array[0] == "Front":
            dt_str = "FWD"
        else:
            dt_str = "AWD"
    else:
        dt_str = "N/A"
    vehicle_info["drivetrain"] = dt_str
    
    # GETTING SEATS
    seats = soup.find('a', href=re.compile(r'seats='))
    if seats:
        vehicle_info["numseats"] = re.sub("[^0-9]", "", seats.text)

    # GETTING PRICE
    price_arr = soup.findAll('span')
    price = ""
    found_price = False
    for span in price_arr:
        if "$" in span.text:
            price = re.sub("[^0-9]","", span.text)
            found_price = True
            break
    if not found_price:
        price = '0'
    vehicle_info["price"] = price

    return vehicle_info