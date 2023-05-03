from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
import time
import os
import pandas
import scraper
import datetime as dt

class Dod(scraper.Scraper):

    def __init__(self,start, end):
        super().__init__(start,end)
        self.start = str(self.start)[4:6] + '/' + str(self.start)[6:] + "/" + str(self.start)[0:4]
        self.end = str(self.end)[4:6] + '/' + str(self.end)[6:] + "/" + str(self.end)[0:4]
        self.data = []
        print(self.start)
        print(self.end)

    def downloadData(self):
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument("window-size=1920,1080")
        prefs = {"download.default_directory" : "/Users/staff/funding-scraper-v2/data"}
        options.add_experimental_option("prefs",prefs)

        driver = webdriver.Chrome(executable_path = r"./driver/chromedriver",chrome_options=options)

        # get https://www.geeksforgeeks.org/
        driver.get("https://publicaccess.dtic.mil/search/#/grants/advancedSearch")

        # Maximize the window and let code stall 
        # for 10s to properly maximise the window.
        driver.maximize_window()
        time.sleep(5)

        inp = driver.find_element(By.ID, 'mat-input-5')
        inp.send_keys(self.start)

        time.sleep(5)

        inp = driver.find_element(By.ID, 'mat-input-6')
        inp.send_keys(self.end)

        time.sleep(5)

        # Obtain button by link text and click.
        button = driver.find_element(By.CLASS_NAME, 'btn-primary')
        button.click()
        time.sleep(5)

        driver.execute_script("window.scrollTo(0,300)") 

        time.sleep(5)
        button2 = driver.find_element(By.XPATH,'//button[@class="mat-focus-indicator btn-primary mat-raised-button mat-button-base"]')
        button2.click()

        time.sleep(15)

    def selectData(self):

        all_objects = []
        filepath = super().findData()

        df = pandas.read_csv(filepath)

        df['Recipient Organization'] = df['Recipient Organization'].str.lower()

        df_filtered = df[df['Recipient Organization'].str.contains("university of texas")]

        #print(df_filtered['Recipient Organization'])

        #print(df.columns)

        for ind in df_filtered.index:


            myObj = {
                "id" : df_filtered['Award Number'][ind],
                "agency": 'DOD: ' + df_filtered['Funding Agency Name'][ind],
                "awardeeName": df_filtered['Recipient Organization'][ind].upper(),
                "piFirstName": df_filtered['PI First Name'][ind],
                "piLastName": df_filtered['PI Last Name'][ind],
                "coPDPI": "NO DATA AVAILABLE",
                "pdPIName": df_filtered['PI Last Name'][ind] + ',' + df_filtered['PI First Name'][ind],
                "startDate": df_filtered['Potential Period of Performance Start'][ind],
                "expDate": df_filtered['Potential Period of Performance End'][ind],
                "estimatedTotalAmt": df_filtered['Anticipated Award Amount'][ind],
                "title": df_filtered['Project Title'][ind],
                "city" : 'N/A'
            }
            all_objects.append(myObj)

        self.data = all_objects

        super().deleteData()
    