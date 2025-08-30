import time
import json
import os
import logging
from urllib.parse import urlparse
from seleniumbase import Driver

# -------------------------------------------------------------------------
# Function to solve Cloudflare challenge and capture cf_clearance
# -------------------------------------------------------------------------
def bypasser(url, retries=30, delay=2, cookie_file="cf_cookie.json"):
    driver = Driver(uc=True)
    driver.uc_open_with_reconnect(url, 10)

    cf_cookie = None
    for attempt in range(retries):
        driver.uc_gui_click_captcha()
        cookies = driver.get_cookies()
        for c in cookies:
            if c['name'] == 'cf_clearance':
                cf_cookie = c
                logging.info(f"✅ Got cf_clearance on attempt {attempt+1}")
                break
        if cf_cookie:
            break
        logging.info(f"⏳ Waiting for cf_clearance... attempt {attempt+1}/{retries}")
        time.sleep(delay)

    if cf_cookie:
        parsed = urlparse(url)
        domain = parsed.netloc

        cookies_dict = {}
        if os.path.exists(cookie_file):
            with open(cookie_file, "r", encoding="utf-8") as f:
                cookies_dict = json.load(f)

        cookies_dict[domain] = cf_cookie

        with open(cookie_file, "w", encoding="utf-8") as f:
            json.dump(cookies_dict, f, ensure_ascii=False, indent=2)

        logging.info(f"✅ cf_clearance for {domain} saved to {cookie_file}")


    driver.quit()
    return cf_cookie
