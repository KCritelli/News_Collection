import warnings
warnings.filterwarnings("ignore")
import unidecode
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import re
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
from lxml import etree
from textblob import TextBlob
#import ahocorasick
import os
import pandas as pd
import numpy as np
import fnmatch
from selenium.webdriver.chrome.options import Options
from gensim.summarization import summarize
from datetime import datetime

 

def run_all(entity_name, additional_terms = ''):
### Settings ###
    #Set path and make new directory
    #path_name = name.replace(' ','_')
    #path = './Documents'
    #os.mkdir(path_name)
    #os.chdir(path + path_name)
    #Adjust default settings
    #chrome_options = Options()
 
    chrome_options = webdriver.ChromeOptions()
    #capabilities = {'chromeOptions':{'useAutomationExtension':True}}
    chrome_options.add_argument("no-sandbox")
    #chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = os.path.join("C:/Users/critkat/","chromedriver")
    capabilities = {'browserName': 'chrome','chromeOptions':  {'useAutomationExtension': True,'forceDevToolsScreenshot': True,'args': ['--start-maximized', '--disable-infobars']}}   
 
    #,desired_capabilities = capabilities
    browser = webdriver.Chrome(executable_path=driver,chrome_options=chrome_options,desired_capabilities=capabilities)

    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36' # This is another valid field
    }

    name = entity_name
    def key_words(entity_name,additional_terms = ''):
        entity_name = entity_name.replace(',','%20')
        entity_name = entity_name.replace(' ','%20')
        additional_terms = additional_terms.replace(',','%20')
        additional_terms = additional_terms.replace(' ','%20')
        if additional_terms != '':
            term_list = entity_name + '%20' + additional_terms
        else:
            term_list = entity_name
        full_url = ('https://news.google.com/search?q=' + term_list +
                '&hl=en-US&gl=US&ceid=US%3Aen')
        return full_url


    def link_cleaning(orig_link):
        temp_link = orig_link['href']
        full_link = temp_link.replace('./articles','https://news.google.com/articles')
        return full_link
 
    #Take the news links and dates from the original search page
    full_link = key_words(entity_name, additional_terms)
    browser.get(full_link)
    page = browser.page_source
    soup = BeautifulSoup(page,'lxml')
 
    def scrape_articles():
        list_links = []
        list_dates = []
        boxes = soup.find_all('div',{'class':'xrnccd'})
        for box in boxes:
            try:
                link = box.find('a',{'class':'VDXfz'})
                try:
                    date = box.find('time',{'class':'WW6dff'})
                    date = date.text
                except:
                    date = ''
                list_links.append(link_cleaning(link))
                list_dates.append(date)
            except:
                link = ''
                date = ''     
        columns = ['Article_link','Date']
        #Define dataframe to store results
        article_results = pd.DataFrame(columns=columns)
        for j in range(0,len(list_links)):
            article_results = (article_results.append(pd.Series([list_links[j],list_dates[j]],index=['Article_link','Date']), ignore_index=True))
        article_results = article_results.drop_duplicates()
        article_results = article_results.ix[article_results['Article_link']!='']
        return article_results
    article_results = scrape_articles()
    browser.close()
    browser.quit()
 
    ######################################## PART 2 ##############################################################
    list_text = []
    list_matches = []
    list_summary = []
    list_flag = []
    result = []
    list_links2 = []
 
    #search_terms = ('SCANDAL|AML|CRIME|FRAUD|MONEY-LAUNDERING|MONEY LAUNDERING|TERRORIST FINANCING|THEFT|SANCTIONS|TERRORISM|CORRUPTION')
 
    for article in article_results['Article_link']:
        ##################################
        s = requests.Session()
 

        r = s.get(article, headers = headers)
        article_inside = BeautifulSoup(r.text,"lxml")
        #print(article_inside)
        connecting_link = article_inside.find('a',{'jsname':'tljFtd'})
        article2 = connecting_link['href']
        list_links2.append(article2)
        try:
            result2 = s.get(article2, headers = headers)
            article_inside2 = BeautifulSoup(result2.text,"lxml")
            try:
                result_div = article_inside2.find_all('p')       
                result = [x for x in result_div if x]
            except:
                result = ''
                pass
            text_block = []
            summary_start = []
            summary_end = []
            match_block = []
            name_flag = 0
            search_term_list = ['SCANDAL','AML','CRIMIN*','CRIME','FRAUD','MONEY-LAUNDERING',
                        'MONEY LAUNDERING','LAUNDERING MONEY','TERRORIS*','THEFT','SANCTIONS',
                        'BLACK-MARKET','CRYPTOCURRENCY','EMBEZZL','DRUG TRAFFICKING','EXTORTION','BRIBERY']
            ### Search method inefficient
            # pyahocorasick package not available on work system
            # Find new method to search all terms more efficiently

            for j in range(1,len(result)):
                summary_start.append(result[j].text)
                name_split = name.split(' ')
                for term in search_term_list:   
                    match = fnmatch.filter(result[j].text.upper().split(),term)
                    if (match != []):
                        text_match = result[j].text
                        for n in name_split:
                            if n.upper() in text_match.upper():
                                text_match = text_match.replace(n,n.upper())
                        for word in search_term_list:
                            if word in text_match.upper():
                                text_match = text_match.replace(word.lower(),word)
                        text_block.append(text_match.replace("\n",""))
                        match_block.append(match)
                    else:
                        pass
            summary = ''.join(summary_start)
            summary = unidecode.unidecode(summary)
            if summary.upper().find(name.upper())!= -1:
                name_flag = 1
            try:
                summary_end.append(summarize(summary, word_count = 100))
            except:
                pass
            list_text.append(text_block)
            list_matches.append(match_block)
            list_summary.append(summary_end)
            list_flag.append(name_flag)
        except:
            text_block = ''
            summary_start = ''
            summary_end = ''
            match_block = ''
        	name_flag = 0
            list_text.append(text_block)
            list_matches.append(match_block)
            list_summary.append(summary_end)
            list_flag.append(name_flag)
    list_links2 = pd.Series(list_links2)
    list_text = pd.Series(list_text)
    list_matches = pd.Series(list_matches)
    list_summary = pd.Series(list_summary) #
    list_flag = pd.Series(list_flag)
    article_results['Article_Link'] = list_links2.values
    article_results['Text'] = list_text.values
    article_results['Matches'] = list_matches.values
    article_results['Summary'] = list_summary.values #
    article_results['Flag'] = list_flag.values
    article_results = article_results.sort_values(['Date'], ascending=[True])
    article_results = article_results.ix[article_results['Flag'] == 1]
    article_results = article_results.ix[article_results['Matches'].apply(lambda x: len(x))!= 0]
    article_results = article_results.drop('Flag', axis=1)
    article_results = article_results.drop('Article_link', axis = 1)
    #num_results = int(article_results.shape[0])

    ###########################################################

    #writer = pd.ExcelWriter(path, engine='xlsxwriter')
    #article_results.to_excel(writer, sheet_name='Sheet1')
    #writer.close()
    return article_results