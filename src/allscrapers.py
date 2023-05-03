import argparse
import nih, cprit, doe, nsf, dod, scraper
import json

def main():

    parser = argparse.ArgumentParser(description='Scrape NSF funded awards')
    parser.add_argument('-s', '--start', dest='start_date', help='range start date, format = YYYYMMDD', required=True)
    parser.add_argument('-e', '--end', dest='end_date', help='range start date, format = YYYYMMDD', required=True)
    parser.add_argument('-i', '--institution', dest='inst', help='institution search term, format = University+of+Texas', required=True)
    parser.add_argument('-u', '--userlist', dest='userlist', help='input file with list of names and affiliations', required=True)
    parser.add_argument('-o', '--output', dest='output', help='output file', required=True)
    args = parser.parse_args()

    allData = []

    Dod = dod.Dod(args.start_date,args.end_date)
    Dod.downloadData()
    Dod.selectData()
    allData += Dod.data


'''
    Nsf = nsf.Nsf(args.start_date, args.end_date, args.inst)
    Nsf.search_by_date_range()
    Nsf.retrieve_award_info()
    allData += Nsf.data

    Doe = doe.Doe(args.start_date, args.end_date)
    Doe.make_requests()
    #print(len(Doe.data))
    allData += Doe.data


    Cprit = cprit.Cprit(args.start_date,args.end_date)
    Cprit.downloadData()
    Cprit.selectData()
    allData += Cprit.data
    #Cprit.writeUsers('./data/' + args.userlist, './data/' + args.output, Cprit.data)
    
    Nih = nih.Nih(args.start_date,args.end_date)
    #Nih.initializeDate()
    Nih.splitDateRange()
    Nih.findAllProjects()
    allData += Nih.data


    Nih.writeUsers('./data/' + args.userlist, './data/' + args.output, allData)

    #print(data)
'''    
if __name__ == '__main__':
    main()