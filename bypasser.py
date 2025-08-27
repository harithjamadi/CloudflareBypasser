# -*- coding: utf-8 -*-
import time
import json
import os
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# -----------------------------------------------------------------------------
# Launch Chrome driver
# -----------------------------------------------------------------------------
def launch_driver(download_folder=""):
    options = Options()
    options.set_capability("pageLoadStrategy", "normal")
    options.set_capability("unhandledPromptBehavior", "accept")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    if download_folder:
        prefs = {
            'download.default_directory': download_folder,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        }
        options.add_experimental_option('prefs', prefs)

    return webdriver.Chrome(options=options)


# -----------------------------------------------------------------------------
# Function to solve Cloudflare challenge manually and capture cf_clearance
# -----------------------------------------------------------------------------
def bypasser(url, retries=30, delay=2, cookie_file="cf_cookie.json"):
    driver = launch_driver()
    driver.get(url)

    cf_cookie = None
    for attempt in range(retries):
        cookies = driver.get_cookies()
        for c in cookies:
            if c['name'] == 'cf_clearance':
                cf_cookie = c
                print(f"✅ Got cf_clearance on attempt {attempt+1}")
                break
        if cf_cookie:
            break
        print(f"⏳ Waiting for cf_clearance... attempt {attempt+1}/{retries}")
        time.sleep(delay)

    if cf_cookie:
        parsed = urlparse(url)
        domain = parsed.netloc

        if os.path.exists(cookie_file):
            with open(cookie_file, "r", encoding="utf-8") as f:
                cookies_dict = json.load(f)
        else:
            cookies_dict = {}

        cookies_dict[domain] = cf_cookie

        with open(cookie_file, "w", encoding="utf-8") as f:
            json.dump(cookies_dict, f, ensure_ascii=False, indent=2)

        print(f"✅ cf_clearance for {domain} saved to {cookie_file}")

    driver.quit()
    return cf_cookie


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("⚠️ Usage: python bypasser.py <URL>")
    else:
        bypasser(sys.argv[1])
