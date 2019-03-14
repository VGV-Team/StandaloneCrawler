from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from database_interface import DatabaseInterface
import constants
import time
import traceback
import requests
import re


FRONTIER = ["http://evem.gov.si",
            "http://e-uprava.gov.si",
            "http://podatki.gov.si",
            "http://e-prostor.gov.si"]

driver = None

def canonicalize(url):
    # remove default port number
    url = url.replace(":80", "")
    # remove anchors
    url = url.split("#", 1)[0]
    # remove current directory '.'
    url = url.replace("/./", "/")
    # remove parent directory (with parent)
    url_parent = [r.start() for r in re.finditer("/../", url)]
    all_slashes = [r.start() for r in re.finditer("/", url)]
    replaces = []
    for up in url_parent:
        parent_slash = max([slash for slash in all_slashes if slash < up])
        replaces.append(url[parent_slash:up]+"/..")
    for r in replaces:
        url = url.replace(r, "")
    # add trailing slash if root or directory TODO: GET parameters and '.'
    if url[-1] != "/" and (url.count("/") == 2 or url[-5:].count(".") == 0):
        url += "/"
    # remove anchor
    url = url.split("#", 1)[0]
    # remove default filename
    if url.endswith("/index.html") or url.endswith("/index.php") or \
            url.endswith("/index.htm") or url.endswith("/index"):
        url = "/".join(url.split("/")[0:-1]) + "/"
    # domain to lower case
    url_split = url.split("/")
    url = "/".join(url_split[0:2]) + "/" + url_split[2].lower() + "/" + "/".join(url_split[3:])
    #print(url)
    return url


def filter_javascript_link(link):
    if "javascript:" not in link:
        return link
    else:
        return None


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
    try:
        if driver is None:
            init_selenium()
        driver.get(url)

        # for status code
        request = requests.get(url)

        # print(driver.page_source)

        # we might need this - it executes every script on the page (or a specific one should we select it)
        # html = driver.execute_script("return document.getElementsByTagName('html')[0].innerHTML")

        # maybe useful...
        # aTags = driver.find_elements_by_css_selector("li a")
        # for a in aTags:
        #    print(a.get_attribute("href"))

        return driver.page_source, driver.current_url, request.status_code
    except:
        print("[Selenium] ERROR PARSING URL: ", url)
        return None, None, None


def extract_links(website, current_url):
    # TODO: include links from href attributes and onclick Javascript events (e.g. location.href or document.location)
    # uglavnm to z javaskriptom je treba zrihtat
    html = BeautifulSoup(website, "html.parser")
    a = html.find_all("a", href=True)
    links = []
    for link in a:
        href = link["href"]
        # filter empty links, anchor links and root links
        if len(href) > 0 and href[0] != "#" and href != "/" and filter_javascript_link(href) is not None and \
                get_image_type(href) is constants.IMAGE_CONTENT_TYPE_UNKNOWN and get_document_type(url) is None:
            links.append(change_link_to_absolute(href, current_url))
    return links


def extract_images(website, current_url):
    html = BeautifulSoup(website, "html.parser")
    a = html.find_all("img", src=True)
    images = []
    for image in a:
        src = image["src"]
        # filter empty links, anchor links and root links
        if len(src) > 0 and src[0] != "#" and src != "/":
            images.append(change_link_to_absolute(src, current_url))
    return images


def extract_documents(website, current_url):
    html = BeautifulSoup(website, "html.parser")
    a = html.find_all("a", href=True)
    documents = []
    for link in a:
        href = link["href"]
        # filter empty links, anchor links and root links
        if len(href) > 0 and href[0] != "#" and href != "/" and \
                href.upper().endswith(("."+constants.DATA_TYPE_CODE_PDF, "."+constants.DATA_TYPE_CODE_DOC,
                                       "."+constants.DATA_TYPE_CODE_DOCX, "."+constants.DATA_TYPE_CODE_PPT,
                                       "."+constants.DATA_TYPE_CODE_PPTX)):
            documents.append(change_link_to_absolute(href, current_url))
    return documents


def change_link_to_absolute(link, current_url):
    if not link.startswith("http://") and not link.startswith("https://"):
        # link is relative link
        # if have to remove a '/' else if don't have to add '/' else have to add '/'
        if current_url[-1] == "/" and link[0] == "/":
            link = link[1:]
            slash = ""
        elif current_url[-1] == "/" or link[0] == "/":
            slash = ""
        else:
            slash = "/"
        return current_url + slash + link
    else:
        # link is absolute link
        return link


# we need url to resolve relative links
def add_to_frontier(links, url):
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

def get_robots_txt(url):
    if url.endswith("/") == False :
        url = url + "/" 
    r = requests.get(url + "robots.txt")
    resp = r.text
    if r.status_code == 200:
        data = {"User-agent":[], "Disallow":[], "Allow":[], "Crawl-delay":[]}
        sitemap = []
        for line in resp.split("\n"):
            if line.find("User-agent") != -1:
                data["User-agent"].append(re.sub(r"[\n\t\s]*", "", line).split(":")[1])
            elif line.find("Disallow") != -1:
                data["Disallow"].append(re.sub(r"[\n\t\s]*", "", line).split(":")[1])
            elif line.find("Allow") != -1:
                data["Allow"].append(re.sub(r"[\n\t\s]*", "", line).split(":")[1])
            elif line.find("Crawl-delay") != -1:
                data["Crawl-delay"].append(re.sub(r"[\n\t\s]*", "", line).split(":")[1])
            elif line.find("Sitemap") != -1:
                sitemap.append(re.sub(r"[\n\t\s]*", "", line).split(":", 1)[1])
        if len(sitemap) == 0 :
            return str(data), constants.DATABASE_NULL
        return str(data), sitemap
    return constants.DATABASE_NULL, constants.DATABASE_NULL

# creates new site(domain) and adds the page to frontier
def new_site(url):
    site = get_site(url)
    #get robots.txt and parse it
    robots, sitemap = get_robots_txt(url) #robots spremenimo nazaj v dict z eval()
    site_id = db.add_site(site, robots, sitemap)
    db.add_page(site_id, url, time.time())
    #add sitemap in frontier
    if sitemap != constants.DATABASE_NULL:
        add_to_frontier(sitemap, url)


# temporary, for testing purposes
def initialize_database(db):
    db.delete_all_data()
    global FRONTIER
    FRONTIER = [canonicalize(f) for f in FRONTIER]
    for url in FRONTIER:
        new_site(canonicalize(url))


def get_image_type(url):
    binary_src_start = url.find("data:image/")
    if binary_src_start >= 0:  # image in URL
        search_string = url[binary_src_start:binary_src_start+20].upper()
        for type in (constants.IMAGE_CONTENT_TYPE_JPG, constants.IMAGE_CONTENT_TYPE_JPEG,
                     constants.IMAGE_CONTENT_TYPE_PNG, constants.IMAGE_CONTENT_TYPE_GIF,
                     constants.IMAGE_CONTENT_TYPE_TIFF, constants.IMAGE_CONTENT_TYPE_TIF,
                     constants.IMAGE_CONTENT_TYPE_RAW):
            if search_string.find(type) >= 0:
                return type
        return constants.IMAGE_CONTENT_TYPE_UNKNOWN
    else:
        res = list(filter(url.upper().endswith, ("." + constants.IMAGE_CONTENT_TYPE_JPG,
                                                 "." + constants.IMAGE_CONTENT_TYPE_JPEG,
                                                 "." + constants.IMAGE_CONTENT_TYPE_PNG,
                                                 "." + constants.IMAGE_CONTENT_TYPE_GIF,
                                                 "." + constants.IMAGE_CONTENT_TYPE_TIFF,
                                                 "." + constants.IMAGE_CONTENT_TYPE_TIF,
                                                 "." + constants.IMAGE_CONTENT_TYPE_RAW)))
        if len(res) == 0:
            return constants.IMAGE_CONTENT_TYPE_UNKNOWN
        else:
            return res[0].strip(".")


def get_document_type(url):
    res = list(filter(url.upper().endswith, ("."+constants.DATA_TYPE_CODE_PDF,
                                            "."+constants.DATA_TYPE_CODE_DOC,
                                            "."+constants.DATA_TYPE_CODE_DOCX,
                                            "."+constants.DATA_TYPE_CODE_PPT,
                                            "."+constants.DATA_TYPE_CODE_PPTX)))
    if len(res) == 0:
        return None
    else:
        return res[0].strip(".")


db = DatabaseInterface()

if __name__ == "__main__":

    initialize_database(db)


    for i in range(100):
        try:
            print("Step", i)
            page_id, site_id, url = get_next_url()
            url = canonicalize(url)
            if page_id is None:
                break
            print("URL:", url)
            website, current_url, status_code = download_website(url)
            if website is None:
                db.update_page_to_html(id=page_id, html_content=constants.DATABASE_NULL, http_status_code="408")
                continue
            current_url = canonicalize(current_url)
            if status_code >= 400:
                db.update_page_to_html(id=page_id, html_content=website, http_status_code=status_code)
                continue
            links = extract_links(website, current_url)
            print(links)
            add_to_frontier(links, url)
            db.update_page_to_html(id=page_id, html_content=website, http_status_code=status_code)

            # only parse images from initial four domains; have to add http(s) to site and canonicalize beforehand
            if canonicalize("http://"+get_site(url)) in FRONTIER or canonicalize("https://"+get_site(url)) in FRONTIER:
                images = extract_images(website, current_url)
                for image in images:
                    image = canonicalize(image)
                    print(image)
                    image_data, image_url, status_code = download_website(image)
                    if image_data is not None:
                        image_type = get_image_type(image_url)
                        db.add_image(page_id, image, image_type, image_data, time.time())

                documents = extract_documents(website, current_url)
                for document in documents:
                    document = canonicalize(document)
                    print(document)
                    document_data, document_url, status_code = download_website(document)
                    if document_data is not None:
                        document_type = get_document_type(document_url)
                        if document_type is not None:
                            db.add_page_data(page_id, document_type, document_data)
        except:
            print("FATAL ERROR: ", url)
            traceback.print_exc()

    if driver is not None:
        driver.close()


    # cannonicalize() TEST
    '''
    canonicalize("http://cs.indiana.edu:80/")
    canonicalize("http://cs.indiana.edu")
    canonicalize("http://cs.indiana.edu/People")
    canonicalize("http://cs.indiana.edu/faq.html#3")
    canonicalize("http://cs.indiana.edu/a/./b/")
    canonicalize("http://cs.indiana.edu/a/../b/")
    canonicalize("http://cs.indiana.edu/a/./../b/")
    canonicalize("http://cs.indiana.edu/index.html")
    canonicalize("http://cs.indiana.edu/%7Efil/")
    canonicalize("http://cs.indiana.edu/My File.htm")
    canonicalize("http://CS.INDIANA.EDU/People")
    '''
