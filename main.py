import json
import pandas as pd
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from itertools import product as list_changer

url = "https://to......rn..........ir"  #we don't want to make the real url clear


def run_browser(headless=True):
    chrome_options = webdriver.ChromeOptions()
    if headless == True:
        chrome_options.add_argument('--headless')
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def get_all_products_url(driver):
    products_url = set()
    for i in range(1, 16):
        driver.get(f"{url}/product?page={str(i)}")
        products = driver.find_element(By.CSS_SELECTOR,
                                       "body > main > div > div > div.ng-scope > div.store-products.store-compact-products > div")
        products_a = products.find_elements(By.CSS_SELECTOR, "a")
        for a in products_a:
            link = a.get_attribute("href")
            products_url.add(link)
    products_url = list(products_url)
    return products_url


def login(driver):
    driver.get(f"{url}/site/signin")
    driver.find_element(By.CSS_SELECTOR, "#signin-username").send_keys("username123")
    driver.find_element(By.CSS_SELECTOR, "#signin-password").send_keys("password123")

    driver.find_element(By.CSS_SELECTOR,
                        "body > main > div > div > form > div:nth-child(6) > div.col-md-9.col-lg-6 > button").click()
    sleep(5)


def each_product(driver):
    attr_dic = dict()

    attributes_groups = driver.find_elements(By.CSS_SELECTOR,
                                             "body > main > div > div > div.product-header > div > div.col-12.col-lg-7.pr-lg-0 > form > div.flex-grow-1.align-items-center.d-flex > div > div.product-attributes > div")

    for at_g in attributes_groups:
        if at_g.text != "":
            atr_list = at_g.find_elements(By.CLASS_NAME, "product-attribute-label")
            at_g_name = at_g.find_element(By.CLASS_NAME, "input-group-prepend").text
            attr_dic[at_g_name] = atr_list

    values_list = list(attr_dic.values())
    reorg_values = list(list_changer(*values_list))

    product = list()

    product_name = driver.find_element(By.CSS_SELECTOR,
                                       "body > main > div > div > div.product-header > div > div.col-12.col-lg-7.pr-lg-0 > form > div.flex-grow-1.align-items-center.d-flex > div > div.d-flex.align-items-center.flex-column.flex-sm-row.justify-content-between.w-100 > h1").text

    product.append({"name": product_name})

    image_url = driver.find_element(By.CSS_SELECTOR,
                                    "body > main > div > div > div.product-header > div > div.col-12.col-lg-5.pl-lg-50 > div.product-image.d-inline > a > img").get_attribute(
        "src")
    product.append({"image_url": image_url})
    for l in reorg_values:
        values = []
        for v in l:
            values.append(v)
            v.click()
        else:
            detailed_product = list()
            # check price
            real_price = driver.find_elements(By.CSS_SELECTOR, "h5")[0].text.replace(" تومان", "").replace(",", "")
            if real_price != "" and real_price.isdigit():
                detailed_product.append({"real_price": int(real_price)})
            else:
                detailed_product.append({"real_price": None})

            try:
                discount_per = driver.find_element(By.CSS_SELECTOR,
                                                   "body > main > div > div > div.product-header > div > div.col-12.col-lg-7.pr-lg-0 > form > div.flex-grow-1.align-items-center.d-flex > div > div.product-price-container.pt-20.pt-sm-25.pt-md-30 > span").text.replace(
                    " تخفیف", "").replace("٪", "").replace(",", "")
            except:
                discount_per = 0
            detailed_product.append({"discount_per": int(discount_per)})

            try:
                off_price = driver.find_elements(By.CSS_SELECTOR, "h5")[1].text.replace(" تومان", "").replace(",", "")
            except:
                off_price = None
            if discount_per == 0 or not off_price.isdigit():
                detailed_product.append({"off_price": None})
            else:
                detailed_product.append({"off_price": int(off_price)})

            exist = driver.find_element(By.XPATH, "html").text.find("محصول مورد نظر موجود نمی‌باشد.")
            if exist == -1:
                detailed_product.append({"status": True})
            else:
                detailed_product.append({"status": False})
            temp_v = list()
            for v in values:
                for k in attr_dic.keys():
                    if v in attr_dic[k]:
                        if k == "انتخاب طرح:":
                            k = "design"
                        elif k == "انتخاب مناسب برای:":
                            k = "suitable_for"
                        elif k == "انتخاب مدل گوشی:":
                            k = "device_model"
                        elif k == "انتخاب رنگ:":
                            k = "color"
                        elif k == "انتخاب رنگ فریم:":
                            k = "frame_color"
                        else:
                            k = k.replace(":", "").replace("انتخاب ", "")
                        temp_v.append({k: v.text})
            else:
                detailed_product.append({"attribiuts": temp_v})

        product.append(detailed_product)
    return product


def main(headless=True, wait=int(300)):
    driver = run_browser(headless=headless)
    products_url = get_all_products_url(driver)
    login(driver)

    while True:
        # get detail of each product and combine to products dict
        products = dict()
        for i in range(len(products_url)):
            url = products_url[i]
            driver.get(url)
            try:
                product = each_product(driver)
            except:
                print("error in this url: ", products[i])
                quit()
            else:
                product_id = url.replace(f"{url}/", "")
                products[product_id] = product
        else:
            # export as json file
            with open('tornado_products.json', 'w') as f:
                json.dump(products, f)

            # export as Excel
            pd.DataFrame(products).to_excel("tornado_products.xlsx")
        sleep(wait)
        products_url = get_all_products_url(driver)


if __name__ == "__main__":
    gui_br = input("Do you need GUI browser? [y/n]: ")
    if gui_br == 'y':
        headless = False
    elif gui_br == 'n':
        headless = True
    else:
        print("not acceptable response")
        quit()

    waiting_time = int(input("How many seconds the program should wait between two tries? [ex. 300]: "))

    main(headless=headless, wait=waiting_time)
