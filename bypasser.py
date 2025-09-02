import time
import json
import os
import logging
from urllib.parse import urlparse
from seleniumbase import Driver

cookie_file = "cf_cookie.json"

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

def useBypasser(url, driver, cookie_file="cf_cookies.json"):
    parsed = urlparse(url)
    domain = parsed.netloc

    if not os.path.exists(cookie_file):
        logging.warning(f"⚠️ Cookie file {cookie_file} not found, creating new one")
        with open(cookie_file, "w", encoding="utf-8") as f:
            json.dump({}, f)

    with open(cookie_file, "r", encoding="utf-8") as f:
        cookies_dict = json.load(f)

    if domain not in cookies_dict:
        logging.warning(f"❌ No cookie found for domain {domain}, running bypasser...")
        bypasser(url, cookie_file=cookie_file)
        with open(cookie_file, "r", encoding="utf-8") as f:
            cookies_dict = json.load(f)

    cookie_dict = cookies_dict.get(domain)

    driver.get(f"https://{domain}")
    driver.delete_all_cookies()
    driver.add_cookie(cookie_dict)

    try:
        driver.get(url)
        time.sleep(3)

        # --- Check if Cloudflare challenge is still visible ---
        page_source = driver.page_source.lower()
        if "verify you are human" in page_source or "just a moment" in page_source:
            logging.warning("⚠️ Cloudflare challenge detected even with cookie, retrying bypass...")
            raise Exception("Cloudflare challenge triggered")

        logging.info("✅ Page loaded successfully with cf_clearance")
        return True

    except (Exception) as e:
        logging.warning(f"⚠️ Failed to load page with cookie: {e}")
        logging.info("🔄 Running bypasser again...")

        bypasser(url, cookie_file=cookie_file)

        with open(cookie_file, "r", encoding="utf-8") as f:
            cookies_dict = json.load(f)
        cookie_dict = cookies_dict.get(domain)

        driver.get(f"https://{domain}")
        driver.delete_all_cookies()
        driver.add_cookie(cookie_dict)

        driver.get(url)
        time.sleep(3)
        logging.info("✅ Page loaded after re-bypass")
        return True