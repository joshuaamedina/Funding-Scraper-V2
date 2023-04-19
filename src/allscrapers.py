import argparse
import nih, cprit, scraper

def main():

    parser = argparse.ArgumentParser(description='Scrape NSF funded awards')
    parser.add_argument('-s', '--start', dest='start_date', help='range start date, format = YYYYMMDD', required=True)
    parser.add_argument('-e', '--end', dest='end_date', help='range start date, format = YYYYMMDD', required=True)
    parser.add_argument('-i', '--institution', dest='inst', help='institution search term, format = University+of+Texas', required=True)
    parser.add_argument('-u', '--userlist', dest='userlist', help='input file with list of names and affiliations', required=True)
    parser.add_argument('-o', '--output', dest='output', help='output file', required=True)
    args = parser.parse_args()


    #Cprit = cprit.Cprit(args.start_date,args.end_date)
    #Cprit.downloadData()
   # data = Cprit.selectData()
    #Cprit.deleteData()
    
    Nih = nih.Nih(args.start_date,args.end_date)
    #Nih.initializeDate()
    Nih.splitDateRange()
    Nih.findAllProjects()

    Nih.writeUsers('./data/' + args.userlist, './data/' + args.output, Nih.data)

    #print(data)

if __name__ == '__main__':
    main()