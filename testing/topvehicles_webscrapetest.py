from bs4 import BeautifulSoup # beautiful soup 4
from urllib.request import urlopen
import re

# GETTING TOPVEHICLES SPORTS
url = "https://gtacars.net/?filter_race_class=spo&sort=lap_time"
page = urlopen(url)
html = page.read().decode("utf-8")
soup = BeautifulSoup(html, "html.parser")
times = soup.findAll('span')
for time in times:
    print(time.text)