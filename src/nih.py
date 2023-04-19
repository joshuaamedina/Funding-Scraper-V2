import argparse
from datetime import datetime, timedelta
import logging
import json
import requests
from openpyxl import load_workbook
import xlsxwriter
from fuzzywuzzy import fuzz
import math
import scraper

class Nih(scraper.Scraper):
        
    def __init__(self, start, end):
        super().__init__(start,end)
        self.start = str(self.start)[0:4] + "-" + str(self.start)[4:6] + "-" + str(self.start)[6:]
        self.end = str(self.end)[0:4] + "-" + str(self.end)[4:6] + "-" + str(self.end)[6:]
        self.url = 'https://api.reporter.nih.gov/v2/projects/search'
        self.data = []
        self.initializeDate()

    def initializeDate(self):
        self.origin = datetime.strptime(self.start,"%Y-%m-%d")
        finish = datetime.strptime(self.end,"%Y-%m-%d")
        days = (finish - self.origin).days
        self.groups = math.ceil(days/75)
        l = list(range(0,days))
        n = math.ceil(days/self.groups)
        self.chunks = list(super().partition(l,n))

    def partition(l, n):
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def splitDateRange(self):
        api_calls = []
        timeDict ={}
        timeList= []
        timeList.append(self.origin)
        for x in range(1,self.groups):
            timeList.append(timeList[x-1] + timedelta(days=len(self.chunks[x-1])))

        timeDict[0] = [timeList[0], timeList[0]+ timedelta(days=len(self.chunks[0])-1)]
        for x in range(1,self.groups):
            timeDict[x] = [timeList[x] -timedelta(days=1), (timeList[x]) + timedelta(days=len(self.chunks[x])-1)]

        timeDict[len(timeDict)-1] = [timeDict[len(timeDict)-1][0], (timeDict[len(timeDict)-1][1]+timedelta(days=1))]

        for x in timeDict:
            texas = {
            "criteria":
            {
                "project_start_date": { "from_date": str(timeDict[x][0].date()), "to_date": str(timeDict[x][1].date()) },
                "org_names": ["UNIVERSITY OF TEXAS","University of TX","UT SOUTHWESTERN MEDICAL CENTER"]
            },
            "limit": 500,
            "offset":0,
            "sort_field":"project_start_date",
            "sort_order":"desc"
            }

            api_calls.append(texas)

        self.api_calls = api_calls

    def findAllProjects(self):

        """
        Given a start date, end date, and a list of json payloads the function makes 
        a POST call to NIH API for each payload. Each payload is given a date range and a 
        list of strings for the query. Data from the response is parsed and appended to our 
        list of formatted objects. North Texas results are removed.
        """

        all_results = []
        results = []

        for x in self.api_calls:
            response = requests.post(self.url, json = x).json()
            temp = response["results"]
            assert(len(temp) < 500), "The date range provided too many results, please provide a block smaller than 75 days."
            results += temp

        for y in results:
            if(results.count(y) > 1):
                assert("Duplicates in the response")
        
        logging.info(f"START: {self.start} END: {self.end}")
        print(f'Before removing North Texas: {len(results)}')

        for x in results:

            # Remove all of North Texas Results

            if ('NORTH' in x['organization']['org_name']):
                logging.info(f"REMOVING: {x['organization']['org_name']}")
                continue

            startDate = x["project_start_date"]
            if(startDate):
                startDate = startDate[5:7] + "/" + startDate[8:10] + "/" + startDate[0:4]
            endDate = x["project_end_date"]
            if(endDate):
                endDate = endDate[5:7] + "/" + endDate[8:10] + "/" + endDate[0:4]
            else:
                endDate = "N/A"

            coPDPI = []
            for y in x["principal_investigators"]:
                if(y["is_contact_pi"] == True):
                    piFirstName = y["first_name"]
                    piLastName = y["last_name"]
                else:
                    coPDPI.append({
                        "first_name": y["first_name"],
                        "middle_name": y["last_name"],
                        "last_name" : y["last_name"]
                    })

            # Create objects with the information we want.

            myObj = {
                "id" : x["appl_id"],
                "agency": x["agency_ic_fundings"][0]["abbreviation"],
                "awardeeName": x["organization"]["org_name"],
                "piFirstName": piFirstName,
                "piLastName": piLastName,
                "coPDPI": coPDPI or "NO DATA AVAILABLE",
                "pdPIName": x["contact_pi_name"],
                "startDate": startDate,
                "expDate": endDate,
                "estimatedTotalAmt": x["award_amount"],
                "title": x["project_title"],
                "city" : x["organization"]["org_city"]
            }

            all_results.append(myObj)

        print(f'After removing North Texas: {len(all_results)}')
        self.data = all_results
        

        

'''
def main():

    parser = argparse.ArgumentParser(description='Scrape NSF funded awards')
    parser.add_argument('-s', '--start', dest='start_date', help='range start date, format = YYYYMMDD', required=True)
    parser.add_argument('-e', '--end', dest='end_date', help='range start date, format = YYYYMMDD', required=True)
    parser.add_argument('-i', '--institution', dest='inst', help='institution search term, format = University+of+Texas', required=True)
    parser.add_argument('-u', '--userlist', dest='userlist', help='input file with list of names and affiliations', required=True)
    parser.add_argument('-o', '--output', dest='output', help='output file', required=True)
    args = parser.parse_args()

    #start = str(args.start_date)[0:4] + "-" + str(args.start_date)[4:6] + "-" + str(args.start_date)[6:]
    #end = str(args.end_date)[0:4] + "-" + str(args.end_date)[4:6] + "-" + str(args.end_date)[6:]


    data = []
    nih = Nih(data,args.start_date,args.end_date)
    Nih.initializeDate(nih)
    Nih.splitDateRange(nih)
    all_awards = Nih.findAllProjects(nih)

    # split user inputted date range, get all NIH awards, match TACC Users

if __name__ == '__main__':
    main()
'''