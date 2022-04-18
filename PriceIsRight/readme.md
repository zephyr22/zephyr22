#### Price is Right
This an example of web scraping.  It scrapes The Price is Right Episode Guide pages found here: https://tpirepguide.com/ and specifically looks only for the Showcase Showdown sections.  For information on the portion of this show see: https://priceisright.fandom.com/wiki/Showcase_Showdown

Files:
- PIR_Main.py: python file that contains the main function that kicks off the scraping.  Option to specify two parameters, a URL and the ID associated with that page that appears in the upper left.  The program will then find the prior day's url on that web page and continuing scraping either till an exception is reached or there are no more urls to scrape.  The program will also pickle the data obtained as it goes in case of a crash or other failure that prevents saving.
- PIR_URLParser.py: python file that contains a scraping class specific to the Price is Right site.  Most of the days seem to follow a set pattern and this was used to identify the Showcase Showdown section.  Days that do not follow the pattern will be skipped over
- Data Folder: Contains csv files from the raw scraping
- PIRLoadPickle.ipynb: jupyter notebook that has examples of loading the saved pickle file to the approapriate csvs in case of script failure
- ScrapeCleaning.ipynb: jupyter notebook that takes the raw scraped data, cleans it, and calculates the events
- FullContent.csv: contains the cleaned data with one row per contestant and rows for showcases that were present but not successfully parsed
- OneRowData.csv: contains the cleaned data with one row for each showcase showdown
- GraphResults.ipynb: graphs that explore the data obtained
