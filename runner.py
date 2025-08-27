# -*- coding: utf-8 -*-
import json
import os
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# -----------------------------------------------------------------------------
# Launch Chrome driver
# -----------------------------------------------------------------------------
def launch_driver(download_folder=""):
    options = Options()
    options.set_capability("pageLoadStrategy", "none")
    options.set_capability("unhandledPromptBehavior", "accept")
    options.add_argument("--start-maximized")

    if download_folder:
        prefs = {
            'download.default_directory': download_folder,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        }
        options.add_experimental_option('prefs', prefs)

    driver = webdriver.Chrome(options=options)
    return driver


class Checking_RCT:
    def __init__(self, cookie_file="cf_cookie.json"):
        self.driver = launch_driver()
        self.cookie_file = cookie_file

    def inject_cookie_and_open(self, url):
        parsed = urlparse(url)
        domain = parsed.netloc

        if not os.path.exists(self.cookie_file):
            raise FileNotFoundError(f"❌ Cookie file {self.cookie_file} not found")

        with open(self.cookie_file, "r", encoding="utf-8") as f:
            cookies_dict = json.load(f)

        if domain not in cookies_dict:
            raise KeyError(f"❌ No cookie found for domain {domain}")

        cookie_dict = cookies_dict[domain]

        base_url = f"https://{cookie_dict['domain'].lstrip('.')}"
        self.driver.get(base_url)
        self.driver.add_cookie(cookie_dict)
        self.driver.get(url)

    def checkupdate(self, url, ind, ref, current_timepoint=None):
        if ind == 'selenium':
            self.driver.set_page_load_timeout(60)
            self.inject_cookie_and_open(url)

            e1 = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, ref))
            )
            return e1.get_attribute('innerHTML')

    def end(self):
        self.driver.quit()


if __name__ == "__main__":
    a = Checking_RCT(cookie_file="cf_cookie.json")

    text = a.checkupdate(
        "https://glp.se.gob.ar/biocombustible/reporte_precios.php",
        "selenium",
        "(//tr[contains(@class, 'impar')])[1]"
    )
    print(text)
    a.end()
