import os
import re
import time
import argparse

import selenium.common.exceptions
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


def validate_url(url: str) -> str:
    url_regex = r'^https?://.*auto\.ru.*$'
    if not re.match(url_regex, url):
        raise argparse.ArgumentTypeError(
            "Invalid URL format. Please provide a valid URL containing 'auto.ru'.")
    return url


def create_parser() -> argparse.ArgumentParser:
    parser_in = argparse.ArgumentParser()

    parser_in.add_argument(
        "url",
        help="Enter the URL of the ad you want to get data from (the parser works with the site 'auto.ru')",
        type=validate_url
    )

    return parser_in


def create_driver() -> webdriver:
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument('log-level=3')
    options.add_argument("no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-notifications")
    # options.add_argument("--headless")
    s = Service(executable_path=os.environ.get('PATH_TO_CHROMEDRIVER'))
    driver = webdriver.Chrome(service=s, options=options)
    driver.maximize_window()

    return driver


def pass_protection(driver: webdriver):
    captcha_detected = True
    other_detected = True

    while captcha_detected or other_detected:
        try:
            driver.find_element(By.XPATH, '//*[@id="confirm-button"]').click()
            time.sleep(3)
        except selenium.common.exceptions.NoSuchElementException:
            other_detected = False
        try:
            driver.find_element(By.XPATH, '//*[@id="js-button"]').click()
            time.sleep(3)
        except selenium.common.exceptions.NoSuchElementException:
            captcha_detected = False


def get_ad_details(url: str) -> dict:
    driver = create_driver()
    driver.get(url)

    pass_protection(driver)

    paths = {
        "mark": {
            "cars": '//*[@id="app"]/div/div[2]/div[3]/div/div[2]/div/div[2]/div/div[1]/div[1]/div/div[3]/div/a',
            "lcv": '//*[@id="app"]/div/div[2]/div[3]/div/div[2]/div/div[2]/div/div[1]/div[1]/div/div[4]/div/a',
            "motorcycle": '//*[@id="app"]/div/div[2]/div[3]/div/div[2]/div/div[2]/div/div[1]/div[1]/div/div[4]/div/a'
        },
        "model": {
            "cars": '//*[@id="app"]/div/div[2]/div[3]/div/div[2]/div/div[2]/div/div[1]/div[1]/div/div[4]/div/a',
            "lcv": '//*[@id="app"]/div/div[2]/div[3]/div/div[2]/div/div[2]/div/div[1]/div[1]/div/div[5]/div/a',
            "motorcycle": '//*[@id="app"]/div/div[2]/div[3]/div/div[2]/div/div[2]/div/div[1]/div[1]/div/div[5]/div/a'
        }
    }

    is_new = url.split('/')[4] == 'new'
    transport_type = url.split('/')[3]

    mark = driver.find_element(
        By.XPATH,
        paths['mark'][transport_type]
    ).text
    model = driver.find_element(
        By.XPATH,
        paths['model'][transport_type]
    ).text
    if is_new:
        mileage = '0 км'
    else:
        mileage = driver.find_element(
            By.CLASS_NAME,
            'CardInfoRow_kmAge'
        ).text.lstrip('Пробег\n')
    price = driver.find_element(
        By.CLASS_NAME,
        'OfferPriceCaption__price'
    ).text

    driver.quit()

    ad_details = {
        'mark': mark,
        'model': model,
        'mileage': mileage,
        'price': price,
    }

    return ad_details


if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()

    if not args.url:
        parser.error("URL are required.")

    ad_details = get_ad_details(args.url)

    print("Детали объявления:")
    print(f"Марка: {ad_details['mark']}")
    print(f"Модель: {ad_details['model']}")
    print(f"Пробег: {ad_details['mileage']}")
    print(f"Цена: {ad_details['price']}")
