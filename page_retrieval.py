from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from database_interface import DatabaseInterface
import constants
import time
import traceback

FRONTIER = ["http://evem.gov.si",
            "http://e-uprava.gov.si",
            "http://podatki.gov.si",
            "http://e-prostor.gov.si"]

driver = None


def init_selenium():
    options = Options()
    options.add_argument("--headless")
    global driver
    driver = webdriver.Chrome(executable_path="webdriver/chromedriver.exe", options=options)


def get_site(url):
    parse = urlparse(url)
    return parse.hostname


def get_next_url():
    # take next page from pages table marked with frontier code order by accessed_time
    data = db.get_next_N_frontier(N=1)
    # 0: id (page_id), 1: site_id (FK), 2: url
    if len(data) > 0:
        data = data[0]
        return data[0], data[1], data[2]
    else:
        return None, None, None


def download_website(url):
    # retrieve and render website content
    # consider failed websites
    # return "this is my website"
    if driver is None:
        init_selenium()
    driver.get(url)
    # print(driver.page_source)

    # we might need this - it executes every script on the page (or a specific one should we select it)
    # html = driver.execute_script("return document.getElementsByTagName('html')[0].innerHTML")

    # maybe useful...
    # aTags = driver.find_elements_by_css_selector("li a")
    # for a in aTags:
    #    print(a.get_attribute("href"))

    return driver.page_source


def extract_links(website):
    html = BeautifulSoup(website, "html.parser")
    a = html.find_all("a", href=True)
    links = []
    for link in a:
        #print(link)
        links.append(link["href"])
    return links


# we need url to resolve relative links
def add_to_frontier(links, url):
    for link in links:
        if link.startswith("http://") or link.startswith("https://"):
            FRONTIER.append(link)
        else:
            pass
            # TODO: kinda tricky... need to think about how to approach this - too many javascript redirects
            # print(url + "/" + link)


def find_website_duplicate(url, website):
    # check if URL is already in a frontier
    return "duplicate url or None"

# temporary, for testing purposes
def initialize_database(db):
    db.delete_all_data()
    global FRONTIER
    for url in FRONTIER:
        site = get_site(url)
        # TODO: parse robots.txt and sitemap
        site_id = db.add_site(site, constants.DATABASE_NULL, constants.DATABASE_NULL)
        db.add_page(site_id, url, time.time())
    FRONTIER = []

db = DatabaseInterface()

if __name__ == "__main__":

    initialize_database(db)

    try:
        for i in range(100):
            print("Step", i, "; FRONTIER size:", len(FRONTIER))
            page_id, site_id, url = get_next_url()
            if page_id is None:
                break
            print("URL:", url)
            website = download_website(url)
            # TODO: handle duplicate link
            #duplicate_link = find_website_duplicate(url, website)
            links = extract_links(website)
            print(links)
            # TODO: parse links and add to database(sites, pages)/frontier
            #add_to_frontier(links, url)
            db.update_page_to_html(id=page_id, html_content="<html>placeholder</html>",http_status_code="400")
    except:
        print("ERROR")
        traceback.print_exc()
        if driver is not None:
            driver.close()
