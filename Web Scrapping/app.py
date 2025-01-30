from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from chromedriver_py import binary_path
from datetime import datetime as dt
from sqlalchemy import create_engine
from selenium import webdriver
from bs4 import BeautifulSoup
from pangres import upsert
import pandas as pd

conn = create_engine("mysql+pymysql://{user}:{password}@{hostname}/{database}")
year_now = dt.today().strftime('%Y')

thaimonth_dict = {
    'ม.ค.':'1', 
    'ก.พ.':'2', 
    'มี.ค.':'3', 
    'เม.ย.':'4', 
    'พ.ค.':'5', 
    'มิ.ย.':'6', 
    'ก.ค.':'7', 
    'ส.ค.':'8', 
    'ก.ย.':'9', 
    'ต.ค.':'10', 
    'พ.ย.':'11', 
    'ธ.ค.':'12'
}

web_name = "https://tmd.go.th/"
options = Options()
service_object = Service(binary_path)
driver = webdriver.Chrome(service=service_object,options=options)
driver.maximize_window()
driver.get(web_name)

supportData = driver.find_element(By.XPATH, '/html/body/div[1]/nav/div/div/ul/li[3]/a')
supportData.click()

sumTime = driver.find_element(By.XPATH, '/html/body/div[1]/nav/div/div/ul/li[3]/div/div/div/div/div[4]/ul/li')
sumTime.click()

html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')
driver.quit()

columnsSoupList = soup.find_all('tr', {'class': 'table-header text-center align-middle'})
columnsList = [column.get_text(strip=True) for column in columnsSoupList[0].find_all('td')]

dataSoupList = soup.find_all('tbody', {'class': 'text-center align-middle'})

sunrise_df = pd.DataFrame()
sunset_df = pd.DataFrame()

day_i = "1" 
supData = dataSoupList[0].find_all('tr')
for supData_i in supData:
    supClass = supData_i.find(class_=True).get("class")[0]
    if supClass == 'sunrise':
        day_i = supData_i.find_all('td',{'rowspan':'2'})[0].get_text()

    find_data = supData_i.find_all('td')
    timeList = [text.get_text() for text in find_data]
    data_dict_i = {
        'month_th':columnsList[1:],
        'time':timeList
    }
    data_i = pd.DataFrame(data_dict_i)
    data_i['day'] = day_i
    data_i['month'] = data_i['month_th'].map(thaimonth_dict)
    data_i['date']=year_now+'-'+data_i['month'].apply(lambda t: '0'+str(int(t)) if int(t)<10 else str(int(t)))+'-'+data_i['day'].apply(lambda t: '0'+str(int(t)) if int(t)<10 else str(int(t)))
    data_i = data_i[['date','time']]
    if supClass == 'sunrise':
        sunrise_df = pd.concat([sunrise_df,data_i],ignore_index=True)
    else:
        sunset_df = pd.concat([sunset_df,data_i],ignore_index=True)

sunrise_df.rename(columns={'time': 'sunrise time'},inplace=True)
sunset_df.rename(columns={'time': 'sunset time'},inplace=True)

data = sunrise_df.merge(sunset_df,how='left',on='date')
data = data[~ ((data['sunrise time']=='') | (data['sunset time'] == ''))]

data.set_index(['date'],inplace=True)
upsert(
    con=conn,
    df=data,
    table_name='Table Name',
    if_row_exists='update',
    create_schema=False,
    create_table=False
)