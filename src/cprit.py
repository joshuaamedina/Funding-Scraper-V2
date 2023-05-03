# import module
import os, fnmatch
import pandas
import datetime as dt
from selenium import webdriver
#from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import calendar
import argparse
import scraper

# Create the webdriver object. Here the 
# chromedriver is present in the driver 
# folder of the root directory.
class Cprit(scraper.Scraper):

    def __init__(self,start, end):
        super().__init__(start,end)
        t = dt.datetime(int(str(self.start)[0:4]), int(str(self.start)[4:6]), int(str(self.start)[6:]), 0, 0, 1)
        self.start = (float(calendar.timegm(t.timetuple())) * 1000000000)

        s = dt.datetime(int(str(self.end)[0:4]), int(str(self.end)[4:6]), int(str(self.end)[6:]), 0, 0, 1)
        self.end = (float(calendar.timegm(s.timetuple())) * 1000000000)
        self.data = []


    def downloadData(self):
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        prefs = {"download.default_directory" : "/Users/staff/funding-scraper/data"}
        options.add_experimental_option("prefs",prefs)

        driver = webdriver.Chrome(executable_path = r"./driver/chromedriver",chrome_options=options)
        
        # get https://www.geeksforgeeks.org/
        driver.get("https://www.cprit.state.tx.us/grants-funded")
        
        # Maximize the window and let code stall 
        # for 10s to properly maximise the window.
        driver.maximize_window()
        time.sleep(10)
        
        # Obtain button by link text and click.
        button = driver.find_element(By.CLASS_NAME, 'buttons-csv')
        button.click()
        time.sleep(10)

    def selectData(self):
        all_objects = []
        filepath = super().findData()

        df = pandas.read_csv(filepath)
        df['Grant ID'] = df['Grant ID'].astype(str)
        df["Award Date"] = df['Award Date'].str[0:4] + '-' + df['Award Date'].str[5:7] + '-' + df['Award Date'].str[8:10] + ' 00:00:01'
        df['Timestamp'] = pandas.to_datetime(df['Award Date']).astype(int)
        df['Timestamp'] = df['Timestamp']

        df['Organization'] = df['Organization'].astype(str)
        print(df.columns.values)


        df_filtered = df[df['Organization'].str.contains("University of Texas")]
        df_filtered = df[df['Timestamp'].between(self.start,self.end,inclusive=True)]

        print(df_filtered)

        print(df.dtypes)

        for ind in df_filtered.index:

            name = (df_filtered['Primary Investigator/Program Director'][ind]).split(',')
            if len(name) == 2:
                piFirstName = name[1].strip()
                piLastName = name[0]
            elif len(name) == 1:
                piFirstName = name[0]
                piLastName = name[0]

            myObj = {
                "id" : df_filtered['Grant ID'][ind],
                "agency": 'CPRIT: ' + df_filtered['Program'][ind],
                "awardeeName": df_filtered['Organization'][ind],
                "piFirstName": piFirstName,
                "piLastName": piLastName,
                "coPDPI": "NO DATA AVAILABLE",
                "pdPIName": piLastName + ',' + piFirstName,
                "startDate": df_filtered['Award Date'][ind][0:10],
                "expDate": 'N/A',
                "estimatedTotalAmt": df_filtered['Award Amount1'][ind],
                "title": df_filtered['Title'][ind],
                "city" : 'N/A'
            }
            all_objects.append(myObj)
        self.data = all_objects

        super().deleteData()