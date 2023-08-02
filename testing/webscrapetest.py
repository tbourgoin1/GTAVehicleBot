from bs4 import BeautifulSoup # beautiful soup 4
from urllib.request import urlopen
import re

#url = "https://gtacars.net/gta5/tenf"
#url = "https://gtacars.net/gta5/seasparrow2"
url = "https://gtacars.net/gta5/bf400"
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
classes_string = classes[0].text
classes.remove(classes[0])
for clas in classes:
    classes_string += ", " + clas.text
print(classes_string)

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
    print("This vehicle doesn't have a drivetrain listed, use N/A")

# GETTING ...

