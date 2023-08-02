from selenium import webdriver
from selenium.webdriver.common.by import By
browser = webdriver.Chrome()
url = "https://gtacars.net/gta5/tenf"
browser.get(url)
images = browser.find_element(By.XPATH, '//img').get_attribute('src')
print(images)
#len(images) # = 18 images