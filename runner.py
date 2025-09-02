import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bypasser import useBypasser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# -------------------------------------------------------------------------
# Launch Chrome driver
# -------------------------------------------------------------------------
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
    def __init__(self):
        self.driver = launch_driver()

    def checkupdate(self, url, ind, ref, current_timepoint=None):
        try:
            if ind == 'selenium':
                self.driver.set_page_load_timeout(60)
                useBypasser(url, self.driver)

                e1 = WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, ref))
                )
                return e1.get_attribute('innerHTML')

        except Exception as e:
            logging.error(f"Error occurred during checkupdate: {e}")
        return None

    def end(self):
        self.driver.quit()


# # usage:
# a = Checking_RCT()
# text = a.checkupdate("https://glp.se.gob.ar/biocombustible/reporte_precios.php", "selenium", "(//tr[contains(@class, 'impar')])[1]")
# print(text)
# a.end()


if __name__ == "__main__":
    a = Checking_RCT()
    text = a.checkupdate(
        "https://glp.se.gob.ar/biocombustible/reporte_precios.php",
        "selenium",
        "(//tr[contains(@class, 'impar')])[1]"
    )

    if text:
        print(text)
    a.end()

