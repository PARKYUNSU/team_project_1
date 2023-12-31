from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time
import pandas as pd
from datetime import datetime, timedelta
from selenium.common.exceptions import NoSuchElementException


def scrape_rent_data(driver, date):
    rent_data = []
    # 인수일
    start_date = date.strftime("%Y-%m-%d")
    # 반납일
    end_date = (date + timedelta(days=1)).strftime("%Y-%m-%d")
    print(start_date, end_date)

    # 인수일 수정 js code
    edit_start_date_js = 'document.querySelector("#r_date").value = "{}";'.format(
        start_date
    )
    driver.execute_script(edit_start_date_js)

    # 반납일 수정 js code
    edit_end_date_js = 'document.querySelector("#r_date_e").value = "{}";'.format(
        end_date
    )
    driver.execute_script(edit_end_date_js)

    search_xpath = '//*[@id="res_search2"]/div[3]/a/div'

    search = driver.find_element(by=By.CLASS_NAME, value="sc_btn")
    search.click()

    time.sleep(7)

    result_element = []
    index = 2

    # while True:
    #     xpath_1 = '//*[@id="best_pro_list"]/li[{}]/a/div/div[3]/p[1]'.format(index)
    #     xpath_2 = '//*[@id="best_pro_list"]/li[{}]/a/div/div[3]/p[2]'.format(index)
    #     xpath_3 = '//*[@id="best_pro_list"]/li[{}]/a/div/div[4]/div[2]'.format(index)

    #     try:
    #         element_1 = driver.find_element(by=By.XPATH, value=xpath_1).text
    #         element_2 = driver.find_element(by=By.XPATH, value=xpath_2).text.split("|") # "|" 기준으로 슬라이싱
    #         element_3 = driver.find_element(by=By.XPATH, value=xpath_3).text

    #         rent_data.append({
    #             "date": date.strftime("%Y-%m-%d"),
    #             "name": element_1,
    #             "type": element_2[0].strip(),
    #             "seater": element_2[1].strip(),
    #             "m_year": element_2[2].strip(),
    #             "price": element_3
    #         })

    #         index += 1
    #     except NoSuchElementException:
    #         break

    # 수정 코드
    results = driver.find_elements(by=By.CLASS_NAME, value="pro_box")
    for result in results:
        name_text = result.find_element(by=By.CLASS_NAME, value="name").text
        info_text = result.find_element(by=By.CLASS_NAME, value="info").text.split("|")
        price_text = result.find_element(by=By.CLASS_NAME, value="pro_price").text
        price = (
            int(
                result.find_element(by=By.CLASS_NAME, value="price")
                .text[:-1]
                .replace(",", "")
            )
            if len(price_text) > 0
            else 0
        )

        rent_dict = {
            "date": date.strftime("%Y-%m-%d"),
            "name": name_text.replace("[이벤트]", "").strip(),
            "type": info_text[0].strip(),
            "seater": info_text[1].strip(),
            "m_year": info_text[2].strip(),
            "price": price,
            "label": "마감"
            if price == 0
            else "완전자차포함"
            if "이벤트" in name_text
            else "자차미포함",
        }
        rent_data.append(rent_dict)

    return rent_data


url = "https://jejussok.com/rent/rent.php?co=rent"
driver = webdriver.Chrome()
driver.get(url)

date_list = pd.date_range(start="2023-08-01", end="2023-08-01")
rent_data = []

for date in date_list:
    rent_data.extend(scrape_rent_data(driver, date))


df = pd.DataFrame(rent_data)

df.to_csv("rent_data.csv", index=False, encoding="utf-8-sig")

driver.close()
