from bs4 import BeautifulSoup # beautiful soup 4
from urllib.request import urlopen
import re

url = "https://gtacars.net/gta5/tenf"
#url = "https://gtacars.net/gta5/seasparrow2"
#url = "https://gtacars.net/gta5/bf400"
#url = "https://gtacars.net/gta5/asea2"
#url = "https://gtacars.net/gta5/zr350"
#url = "https://gtacars.net/gta5/sultanrs"
page = urlopen(url)
html = page.read().decode("utf-8")
soup = BeautifulSoup(html, "html.parser")

#print(soup.get_text()) # gets all webpage text, no HTML. 
# Can parse from here or get HTML tags like below

# GETTING IMAGE
# will always be the 1st image that appears when you open the car page
# ...which is the best image and the one we want to use
image = soup.find('meta', {"name":"og:image"})
print("https://www.gtacars.net" + image["content"]) # this format will display in the bot correctly

# GETTING MANUFACTURER - # gets the table item for manufacturer and its text value for use
manufacturer = soup.find('a', href=re.compile(r'manufacturer=')).text
print(manufacturer)

# GETTING CLASS
classes = soup.findAll('a', href=re.compile(r'1&filter_race_class='))
if classes:
    classes_string = classes[0].text
    classes.remove(classes[0])
    if len(classes) > 0:
        classes_string = "Race Classes: " + classes_string
    else:
        classes_string = "Race Class: " + classes_string
    for clas in classes:
        classes_string += ", " + clas.text
    print(classes_string)
else:
    clas = soup.find('a', href=re.compile(r'filter_class=')).text
    print("Class: " + clas + ", Not Raceable")

# GETTING SEATS
seats = soup.find('a', href=re.compile(r'seats=')).text
print(re.sub("[^0-9]", "", seats))

# GETTING DRIVETRAIN - stuff like helis don't have this, so need to accomodate that
drivetrain = soup.find('a', href=re.compile(r'drivetrain='))
if drivetrain:
    dt_array = drivetrain.text.split(" ")
    if dt_array[0] == "Rear":
        print("RWD")
    elif dt_array[0] == "Front":
        print("FWD")
    else:
        print("AWD")
else:
    print("no drivetrain, -> N/A")

# GETTING NAME -  # get title tag's text, take the text before the first '—'. That's the name + special like HSW
name = soup.find('title').text.split('—')[0]
print(name)

# GETTING LAP TIME AND TOP SPEED - handle where it does and doesn't have this info
lt_ts_arr = soup.findAll('p')
lap_time = ""
top_speed = ""
for i in range(0, len(lt_ts_arr)):
    if lt_ts_arr[i].text == 'Lap Time':
        lap_time = lt_ts_arr[i+1].text # the <p> after when it says lap time/top speed is the value
    if lt_ts_arr[i].text == 'Top Speed':
        top_speed = lt_ts_arr[i+1].text
        break
no_lt_ts_str = "No Time Set"
if lap_time == "":
    lap_time = no_lt_ts_str
if top_speed == "":
    top_speed = no_lt_ts_str
print(lap_time)
print(top_speed)

# GETTING LAP TIME BY CLASS
ltbc = soup.findAll('a', href=re.compile(r'sort=lap_time&filter_race_class='))
ltbc_str = "LT by class: "
if ltbc:
    for i in range(0, len(ltbc)):
        if i < (len(ltbc) - 1):
            ltbc_str += ltbc[i].text + ", "
        else:
            ltbc_str += ltbc[i].text
    print(ltbc_str)
else:
    print("No time set, no position in class. make this blank in final ver")

# GETTING TOP SPEED BY CLASS
tsbc = soup.findAll('a', href=re.compile(r'sort=top_speed&filter_race_class='))
tsbc_str = "TS by class: "
if tsbc:
    for i in range(0, len(tsbc)):
        if i < (len(tsbc) - 1):
            tsbc_str += tsbc[i].text + ", "
        else:
            tsbc_str += tsbc[i].text
    print(tsbc_str)
else:
    print("No time set, no position in class. make this blank in final ver")


# GETTING PRICE
price_arr = soup.findAll('span')
price = ""
found_price = False
for span in price_arr:
    if "$" in span.text:
        price = span.text.strip().replace(" ", "")
        found_price = True
        break
if not found_price:
    price = "No Price Set"
print(price)

kaljflsj = '''# GETTING DLC - day 1 dlc cars have another data point 1st that uses DLC, have to find it 
dlc_tags = soup.findAll('a', href=re.compile(r'&filter_dlc='))
dlc = ""
if(dlc_tags[0].text[0].isdigit()):
    dlc = dlc_tags[1].text
else:
    dlc = dlc_tags[0].text
print(dlc)'''

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
print(flags_str)