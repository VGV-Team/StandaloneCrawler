from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
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


def get_next_url():
    # take next page from pages table marked with frontier code order by accessed_time
    # return "next url from page table"
    global FRONTIER
    url = FRONTIER[0]
    FRONTIER = FRONTIER[1:]
    return url, 0


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


if __name__ == "__main__":
    try:
        for i in range(100):
            print("Step", i, "; FRONTIER size:", len(FRONTIER))
            url, site_id = get_next_url()
            print("URL:", url)
            website = download_website(url)
            # TODO: handle duplicate link
            duplicate_link = find_website_duplicate(url, website)
            links = extract_links(website)
            add_to_frontier(links, url)
    except:
        print("ERROR")
        traceback.print_exc()
        if driver is not None:
            driver.close()
