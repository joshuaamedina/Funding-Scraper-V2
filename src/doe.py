import requests
from bs4 import BeautifulSoup
import argparse
import datetime
import re
import logging
from openpyxl import load_workbook
import xlsxwriter
from fuzzywuzzy import fuzz
import sys
import scraper
logging.basicConfig(level=logging.DEBUG)

AWARD_INFO = ['Award Number',
              'Title',
              'Institution',
              'PI First Name',
              'PI Last Name',
              'Org Code',
              'Program Office',
              'PM',
              'Start Date',
              'End Date',
              'Most Recent Award Date',
              'Award Type',
              'Amount Awarded to Date',
              'Amount Awarded this FY',
              'Institution Type',
              'UEI',
              'Program Area',
              'Register Number',
              'DUNS'
              ]

class Doe(scraper.Scraper):

    def __init__(self, start, end):
        super().__init__(start,end)
        self.start1 = datetime.datetime.strptime(self.start, '%Y%m%d').strftime('%-m/%-d/%Y')
        self.start_validation = datetime.datetime.strptime(self.start, '%Y%m%d').strftime('%Y-%m-%d-00-00-00')
        self.end1 = datetime.datetime.strptime(self.end, '%Y%m%d').strftime('%-m/%-d/%Y')
        self.end_validation = datetime.datetime.strptime(self.end, '%Y%m%d').strftime('%Y-%m-%d-23-59-59')
        self.url = 'https://pamspublic.science.energy.gov/WebPAMSExternal/Interface/Awards/AwardSearchExternal.aspx'
        self.data = []

    def make_requests(self):
        """
        Retrieve specific award information by making several POST requests. The information returned
        is in the FINAL_RESULTS list.
        """
        with requests.Session() as session:
            # Start a session with a post request to the url
            try:
                res = session.post(self.url, timeout=20)
            except requests.exceptions.ReadTimeout:
                logging.error('timeout during search...try again later')
                sys.exit()
            except Exception as x:
                logging.error(f'request failed because {x}')
                sys.exit()

            # Use response to grab fields necessary for a valid search to go through
            soup = BeautifulSoup(res.content, 'html.parser')

            # Update payload with fields, incl. search params
            payload = {
                "ctl00_REIRadScriptManager1_TSM": soup.find(attrs={"name": "ctl00_REIRadScriptManager1_TSM"})['value'],
                "__EVENTTARGET": "ctl00$MainContent$grdAwardsList",
                "__EVENTARGUMENT": "FireCommand:ctl00$MainContent$grdAwardsList$ctl36;PageSize;100",
                "__VIEWSTATE": soup.find(attrs={"name": "__VIEWSTATE"})['value'],
                "__VIEWSTATEGENERATOR": soup.find(attrs={"name": "__VIEWSTATEGENERATOR"})['value'],
                # Institution name like:
                "ctl00$MainContent$pnlSearch$txtInstitutionName": "University of Texas",
                # Award start date:
                "ctl00$MainContent$pnlSearch$dpPPSDFrom$dateInput": f"{self.start1}",
                "ctl00_MainContent_pnlSearch_dpPPSDFrom_dateInput_ClientState":
                    f"{{'enabled':true,'emptyMessage':'','validationText':'{self.start_validation}', \
                        'valueAsString':'{self.start_validation}','minDateStr':'1980-00-01-00-01-00', \
                        'maxDateStr':'2099-00-31-00-12-00','lastSetTextBoxValue':'{self.start1}'}}",
                "ctl00$MainContent$pnlSearch$dpPPSDTo$dateInput": f"{self.end1}",
                "ctl00_MainContent_pnlSearch_dpPPSDTo_dateInput_ClientState":
                    f"{{'enabled':true,'emptyMessage':'','validationText':'{self.end_validation}', \
                        'valueAsString':'{self.end_validation}','minDateStr':'1980-00-01-00-01-00', \
                        'maxDateStr':'2099-00-31-00-12-00','lastSetTextBoxValue':'{self.end1}'}}",
            }

            # Make another request to update results per page with __EVENTARGUMENT param
            try:
                res = session.post(self.url, data=payload)
            except Exception as x:
                logging.error(f'request failed because {x}')
                sys.exit()

            # Grab updated viewstate that includes larger results per page included
            # Update payload
            soup = BeautifulSoup(res.content, 'html.parser')
            payload['__VIEWSTATE'] = soup.find(attrs={"name": "__VIEWSTATE"})['value']

            # Finally, make first search
            try:
                res = session.post(self.url, data=payload)
            except Exception as x:
                logging.error(f'request failed because {x}')
                sys.exit()
            self.parse_html(res.content)

            # get all event target values
            event_target = soup.find_all("div", {"class": "rgNumPart"})[0]
            event_target_list = [
                re.search('__doPostBack\(\'(.*)\',', t["href"]).group(1)
                for t in event_target.find_all('a')
            ]

            # Make updated post request to perform actual search
            for link in event_target_list[1:]:
                payload['__EVENTTARGET'] = link
                payload['__VIEWSTATE'] = soup.find(attrs={"name": "__VIEWSTATE"})['value']
                try:
                    res = session.post(self.url, data=payload)
                except Exception as x:
                    logging.error(f'request failed because {x}')
                    sys.exit()
                soup = BeautifulSoup(res.content, "html.parser")
                self.parse_html(res.content)


    def parse_html(self,response_content):
        """
        Given a POST response HTML page, grab all search results (award listings)
        on the page and append their results to the final_results list.
        """
        # Grab fields that contain the data
        soup = BeautifulSoup(response_content, 'html.parser')
        table = soup.find(class_="rgMasterTable")
        tbody = table.contents[5]
        trs = tbody.find_all("tr")
        tr_heads, tr_bodies = [], []
        while trs:
            tr_heads.append(trs.pop(0))
            tr_bodies.append(trs.pop(0))
        logging.info(f"{len(tr_heads)} award entries found on this page")
        results_list = []

        # Grab data from fields
        for head in tr_heads:
            tds = head.find_all("td")
            results_list.append({
                'id': tds[1].text.strip(),
                'title': tds[2].text.strip(),
                'awardeeName': tds[3].text.strip(),
                'piFirstName': tds[4].text.strip().split(', ')[1],
                'piLastName': tds[4].text.strip().split(', ')[0],
                'coPDPI': "NO DATA AVAILABLE",
                'agency': 'DOE',
                'pdPIName': tds[4].text.strip().split(', ')[0] + ', ' + tds[4].text.strip().split(', ')[1]
            })
        for index, body in enumerate(tr_bodies):
            lis = body.find_all("li")
            listing = results_list[index]
            listing['Org Code'] = lis[0].text.strip().split(':')[1]
            listing['Program Office'] = lis[1].text.strip().split(':')[1]
            listing['PM'] = lis[2].text.strip().split(':')[1]
            listing['startDate'] = lis[6].text.strip().split(':')[1]
            listing['expDate'] = lis[7].text.strip().split(':')[1]
            listing['Most Recent Award Date'] = lis[8].text.strip().split(':')[1]
            listing['Award Type'] = lis[9].text.strip().split(':')[1]
            listing['estimatedTotalAmt'] = lis[10].text.strip().split(':')[1]
            listing['Amount Awarded this FY'] = lis[11].text.strip().split(':')[1]
            listing['Institution Type'] = lis[12].text.strip().split(':')[1]
            listing['UEI'] = lis[13].text.strip().split(':')[1]
            listing['Program Area'] = lis[14].text.strip().split(':')[1]
            listing['Register Number'] = lis[15].text.strip().split(':')[1]
            listing['DUNS'] = lis[16].text.strip().split(':')[1]

        # Append to final_results list
        self.data += results_list