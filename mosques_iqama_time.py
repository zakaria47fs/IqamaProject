import pandas as pd
from tqdm import notebook

from pytz import timezone
import pytz
from datetime import datetime, date
import requests

from time import sleep
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from lxml import html
from bs4 import BeautifulSoup
import os
from os.path import join


df_mosques = pd.read_csv('Mosques data.csv')

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")

chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)


def today_pray_times(latitude,longitude):

    current_month = datetime.today().month
    current_year = datetime.today().year
    current_day = datetime.today().day
    request = requests.get(f'http://api.aladhan.com/v1/calendar?latitude={latitude}&longitude={longitude}&month={current_month}&year={current_year}')
    
    return request.json()['data'][current_day-1]


def website_pray_tables(website):
    
    tables_df = []

    driver = webdriver.Chrome()
    driver.implicitly_wait(30)
    
    i = 0
    
    url = website

    if type(url) == float or url=='Not Found':return []

    driver.get(url)

    #Selenium hands of the source of the specific job page to Beautiful Soup
    soup_level=BeautifulSoup(driver.page_source, 'lxml')

    #Beautiful Soup grabs the HTML table on the page
    tables = soup_level.find_all('table')

    #extracing links from main/master link    
    links = soup_level.find_all("a")
    href_links = []
    for link in links:
        if (link.get("href") is not None) and ("http" in link.get("href")):
            if 'prayer' in link.text.lower() or 'time' in link.text.lower() or 'iqama' in link.text.lower():
                href_links.append(link.get("href"))

    for href in href_links:
        driver.get(href)
        soup_level = BeautifulSoup(driver.page_source, 'lxml')
        tables.extend(soup_level.find_all('table'))
        
    for table in tables:

        #Getting only tables showing Prayers or Iqamah times 
        if not 'fajr' in table.get_text(' ').lower():
            continue
        
        #Giving the HTML table to pandas to put in a dataframe object
        df = pd.read_html(str(table),header=0)
        tables_df.append(df[0])
    
    return tables_df


if __name__ == "__main__":

    driver.implicitly_wait(30)

    i = 0
    for url in notebook.tqdm(df_mosques['Website'].values):
        
        if type(url) == float or url=='Not Found':continue
            
        driver.get(url)

        #Selenium hands of the source of the specific job page to Beautiful Soup
        soup_level=BeautifulSoup(driver.page_source, 'lxml')

        #Beautiful Soup grabs the HTML table on the page
        tables = soup_level.find_all('table')
        
        #extracing links from main/master link    
        links = soup_level.find_all("a")
        href_links = []
        for link in links:
            if (link.get("href") is not None) and ("http" in link.get("href")):
                if 'prayer' in link.text.lower() or 'time' in link.text.lower() or 'iqama' in link.text.lower():
                    href_links.append(link.get("href"))
                
        for href in href_links:
            driver.get(href)
            soup_level = BeautifulSoup(driver.page_source, 'lxml')
            tables.extend(soup_level.find_all('table'))
        
        folder_name = f'ScrapeTables/website{i}'
        import os
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            
        f = open(f"{folder_name}/website.txt", "w")
        f.write(f'The tables on this folder are extracted from : {url}')
        f.close()
        
        j = 0
        for table in tables:

            #Getting only tables showing Prayers or Iqamah times 
            if not 'fajr' in table.get_text(' ').lower():
                continue
            
            #Giving the HTML table to pandas to put in a dataframe object
            df = pd.read_html(str(table),header=0)

            df[0].to_csv (f'{folder_name}/table{i}_{j}.csv', index = False, header=True)

            j += 1
        i += 1
        
    driver.close()