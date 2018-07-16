
# coding: utf-8


# Libraries Required
from lxml import html 
import re
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup

#------------------------------------------------------------------------------------------------------------------------------------#

# get entire company names and codes in Korean Stock Exchange
company_code = pd.read_html('http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13', header = 0)[0]

# 종목코드 = company code
# 회사명 = company name
company_code.종목코드 = company_code.종목코드.map('{:06d}'.format)
company_code = company_code[['회사명', '종목코드']]
company_code = company_code.rename(columns = {'회사명' : 'name', '종목코드' : 'code'})

#------------------------------------------------------------------------------------------------------------------------------------#

# avoid being blacklisted
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
headers = {'User-Agent': user_agent}

#------------------------------------------------------------------------------------------------------------------------------------#

# scrape financial statements for each company for specific year
def get_fin_stat(name, code, year, fin_type, freq_type):
    url_tmp = 'http://companyinfo.stock.naver.com/v1/company/ajax/cF1001.aspx?cmp_cd=%s&fin_typ=%s&freq_typ=%s'
    url = url_tmp % (code, fin_type, freq_type)
    
    page = requests.get(url, headers = headers, timeout = 15)

    soup = BeautifulSoup(page.content, 'lxml')
    table = soup.find('table')
    
    # Extracting columns and index
    columns, index = [], []
    rows = table.find('tbody').find_all('th')
    cols = table.find('thead').find_all('tr')[1].get_text(strip = True).split('(IFRS연결)')[:-1]

    for row in rows:
        index.append(str(row.text))

    for col in cols:
        columns.append(col.split('/')[0])

    # Extracting data values
    values = []
    data = table.findAll('td')
    for row in data:
        values.append(str(row.text))

    fin_statement = pd.DataFrame(np.array(values).reshape(len(index), len(columns)), index=index, columns=columns)
    
    return pd.DataFrame(fin_statement['{}'.format(year)])

#------------------------------------------------------------------------------------------------------------------------------------#

# extract first and last stock prices in year 2017 
def get_1st_last_price_2017(name, code):
	# Assigned specific page numbers to cut time
	# 2017.01.02 price
    url = 'http://finance.naver.com/item/sise_day.nhn?code={}&page=13'.format(code)

    page = requests.get(url, headers = headers, timeout = 10)
    soup = BeautifulSoup(page.content, 'lxml')
    table = soup.find('table')
    last_price = table.findAll('tr')[12].get_text().split('\n')[2]

    # 2017.12.28 price
    url = 'http://finance.naver.com/item/sise_day.nhn?code={}&page=37'.format(code)
    page = requests.get(url, headers = headers, timeout = 10)
    soup = BeautifulSoup(page.content, 'lxml')
    table = soup.find('table')
    first_price = table.findAll('tr')[14].get_text().split('\n')[2]

    return pd.DataFrame([first_price, last_price], index = ['Start_2017', 'End_2017'])

#------------------------------------------------------------------------------------------------------------------------------------#

# extract first stock prices in year 2016 
def get_1st_price_2016(name, code):
    # Assigned specific page numbers to cut time
    # 2016.01.04 price
    url = 'http://finance.naver.com/item/sise_day.nhn?code={}&page=62'.format(code)
    page = requests.get(url, headers = headers, timeout = 10)
    soup = BeautifulSoup(page.content, 'lxml')
    table = soup.find('table')
    first_price = table.findAll('tr')[14].get_text().split('\n')[2]

    return pd.DataFrame([first_price], index = [name], columns=['Start_2016'])

#------------------------------------------------------------------------------------------------------------------------------------#

# Storing financial statement info (2016) and percent change in price (2017)
stock_data = pd.DataFrame(np.zeros(shape = (2300, 36)))
for row in company_code.iterrows():
	name, code = row[1][0], row[1][1]

	try:
		stock_data.iloc[row[0],0:33] = list(get_fin_stat(name, code, 2015, 0, 'Y').iloc[:,0])
		stock_data.iloc[row[0],33:35] = list(get_1st_last_price_2017(name, code).iloc[:,0])
		stock_data.iloc[row[0],35] = list(get_1st_price_2016(name, code).iloc[:,0])
		
	except:
		# KONEX market 
		stock_data.iloc[row[0],:] = [np.nan]
		print(name, 'Timeout')

#------------------------------------------------------------------------------------------------------------------------------------#

# Concatenate collected data and save as csv file
total_data = pd.concat([company_code, stock_data], axis = 1)
total_data.to_csv('Start_price_2016.csv', index = False)

