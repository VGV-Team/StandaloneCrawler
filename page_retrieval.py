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

    return driver.page_source, driver.current_url


def extract_links(website):
    html = BeautifulSoup(website, "html.parser")
    a = html.find_all("a", href=True)
    links = []
    for link in a:
        href = link["href"]
        # filter empty links, anchor links and root links
        if len(href) > 0 and href[0] != "#" and href != "/":
            links.append(change_link_to_absolute(href))
    return links


def extract_images(website):
    html = BeautifulSoup(website, "html.parser")
    a = html.find_all("img", src=True)
    images = []
    for image in a:
        src = image["src"]
        # filter empty links, anchor links and root links
        if len(src) > 0 and src[0] != "#" and src != "/":
            images.append(change_link_to_absolute(src))
    return images


def extract_documents(website):
    html = BeautifulSoup(website, "html.parser")
    a = html.find_all("a", href=True)
    documents = []
    for link in a:
        href = link["href"]
        # filter empty links, anchor links and root links
        if len(href) > 0 and href[0] != "#" and href != "/" and \
                href.upper().endswith((constants.DATA_TYPE_CODE_PDF, constants.DATA_TYPE_CODE_DOC,
                               constants.DATA_TYPE_CODE_DOCX, constants.DATA_TYPE_CODE_PPT,
                               constants.DATA_TYPE_CODE_PPTX)):
            documents.append(change_link_to_absolute(href))
    return documents


def change_link_to_absolute(link):
    if not link.startswith("http://") and not link.startswith("https://"):
        # link is relative link
        return current_url + "/" + link
    else:
        # TODO: This
        # link is absolute link
        return link


# we need url to resolve relative links
def add_to_frontier(links, url, current_url):
    for link in links:
        # TODO: check for duplicate links

        site_data = db.find_site(get_site(link))
        if len(site_data) == 0:
            # new site/domain; add site to db and page to frontier
            new_site(link)
        else:
            # site exists in db, add page to frontier
            site_id = site_data[0][0]
            db.add_page(site_id=site_id, url=link, accessed_time=time.time())


def find_website_duplicate(url, website):
    # check if URL is already in a frontier
    return "duplicate url or None"


# creates new site(domain) and adds the page to frontier
def new_site(url):
    site = get_site(url)
    # TODO: parse robots.txt and sitemap
    site_id = db.add_site(site, constants.DATABASE_NULL, constants.DATABASE_NULL)
    db.add_page(site_id, url, time.time())


# temporary, for testing purposes
def initialize_database(db):
    db.delete_all_data()
    global FRONTIER
    for url in FRONTIER:
        new_site(url)
    FRONTIER = []


db = DatabaseInterface()

if __name__ == "__main__":

    initialize_database(db)

    try:
        for i in range(100):
            print("Step", i)
            page_id, site_id, url = get_next_url()
            if page_id is None:
                break
            print("URL:", url)
            website, current_url = download_website(url)
            links = extract_links(website)
            print(links)
            add_to_frontier(links, url, current_url)
            # TODO: change this to get status code from request and HTML from content
            db.update_page_to_html(id=page_id, html_content="<html>placeholder</html>", http_status_code="400")

            images = extract_images(website)
            for image in images:
                print(image)
                image_data, image_url = download_website(image)
                # TODO: image type detection
                db.add_image(page_id, image, "PNG", image_data, time.time())

            documents = extract_documents(website)
            for document in documents:
                print(document)
                document_data, document_url = download_website(document)
                # TODO: document type detection
                db.add_page_data(page_id, constants.DATA_TYPE_CODE_DOC, document_data)



    except:
        print("ERROR")
        traceback.print_exc()
        if driver is not None:
            driver.close()
