from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from datetime import date, datetime, timedelta
from selenium.webdriver.common.by import By
from chromedriver_py import binary_path
from selenium import webdriver
import time
import os

coin_dict = {'BTCTHB':'Bitcoin',
             'DOGETHB':'Dogecoin',
             'LTCUSDT':'Litecoin',
             'USDTTHB':'Tether',
             'SIXTHB':'SIX'}

current_time = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
start_date = datetime.strptime('2024-10-24','%Y-%m-%d')
end_date = datetime.strptime('2024-10-27','%Y-%m-%d')

while start_date <= end_date:
    this_pah = os.getcwd()
    log = open(os.path.join(this_pah,'log.csv'),'a')

    query_date = start_date
    month = query_date.strftime('%m')
    year = query_date.strftime('%Y')
    day = query_date.strftime('%d')
    query_date = query_date.strftime('%Y-%m-%d')


    for i in range(len(coin_dict.keys())):
        coin_keys = list(coin_dict.keys())[i]
        coin_values = list(coin_dict.values())[i]
    
        file_dir = os.path.join(this_pah,f'Screenshot\\{year}\\{month}\\{day}\\{coin_values}')
        coin_path = os.path.join(file_dir,f'{coin_values}_{query_date}.png')
        
        if os.path.isfile(coin_path):
            log.write(f'{current_time},{coin_values},{query_date},Other Create Photo\n')
            log.close()
            continue

        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        try:
            service_object = Service(binary_path)
            driver = webdriver.Chrome(service=service_object)
            url = f'https://www.tradingview.com/chart/?symbol=BITKUB%3A{coin_keys}'
            driver.get(url)
            driver.maximize_window()

            time.sleep(2)

            # open daterange tab
            select_date = driver.find_element(By.XPATH, "/html/body/div[2]/div[5]/div[2]/div/div[2]/div/button/span")
            select_date.click()

            # find date box and change date value to query_date
            get_query_date = WebDriverWait(driver, 20).until\
                (EC.presence_of_element_located((By.XPATH, '//*[@id="overlap-manager-root"]/div/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div/div/div/span/span[1]/input')))
            get_query_date.click()

            # clear date ,insert query_date date and submit in field box
            get_query_date.send_keys(Keys.CONTROL + "a",Keys.DELETE)
            get_query_date.send_keys(query_date)
            driver.find_element(By.XPATH, '//*[@id="overlap-manager-root"]/div/div/div[1]/div/div[4]/div/span/button').click()

            time.sleep(2)

            # point on center
            action = webdriver.ActionChains(driver)
            hover = action.move_to_element_with_offset(WebDriverWait(driver, 20).until\
                    (EC.presence_of_element_located((By.CLASS_NAME,'chart-gui-wrapper'))), 0, 0)
            hover.perform()

            # save screenshot
            driver.save_screenshot(coin_path)
            time.sleep(5)

            log.write(f'{current_time},{coin_values},{query_date},Program Complete\n')

        except Exception as e:
            log.write(f'{current_time},{coin_values},{query_date},Program Error {e}\n')

        finally:
            driver.quit()
            log.close()
            start_date = start_date + timedelta(days=1)