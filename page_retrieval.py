from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.request import urlopen
from database_interface import DatabaseInterface
import constants
import time
import traceback
import requests
import re
import binascii
import random

class PageRetrieval:
    FRONTIER = ["http://evem.gov.si",
                "http://e-prostor.gov.si",
                "http://e-uprava.gov.si",
                "http://podatki.gov.si"]

    driver = None
    db = None
    name = None
    database_lock = None

    len_of_shingle = 5
    len_of_hash = 110
    max_shingle_id = 2**32-1
    next_prime = 4294967311

    coeff_a = None
    coeff_b = None
    
    def __init__(self, thread_name, database_lock):
        self.name = thread_name
        self.database_lock = database_lock
        self.db = DatabaseInterface(database_lock)

    def initialize_database(self):
        self.db.delete_all_data()
        self.FRONTIER = [self.canonicalize(f) for f in self.FRONTIER]
        for url in self.FRONTIER:
            self.new_site(self.canonicalize(url), None)

    def run(self):
        for i in range(100):
            try:
                #print(self.name, "Step", i)
                page_id, site_id, url = self.get_next_url()
                if page_id is None or site_id is None or url is None:
                    # if frontier is empty, wait a few seconds
                    time.sleep(constants.CRAWLER_EMPTY_FRONTIER_SLEEP)
                    print("Frontier empty, waiting...")
                    continue
                url = self.canonicalize(url)
                if page_id is None:
                    break
                print(self.name, "URL:", url)
                website, current_url, status_code = self.download_website(url)
                hash = "placeholder"  # TODO: this
                if website is None:
                    self.db.update_page_to_html(id=page_id, html_content=constants.DATABASE_NULL,
                                                http_status_code="408", hash=null)
                    continue
                current_url = self.canonicalize(current_url)
                if status_code >= 400:
                    self.db.update_page_to_html(id=page_id, html_content=website, http_status_code=status_code,
                                                hash=null)
                    continue
                minHash = self.minHash_content(website)
                find_duplicate = self.find_duplicate_content(minHash)
                if find_duplicate != 0:
                    self.db.update_page_to_duplicate(id=page_id, html_content=website, http_status_code=status_code, hash=minHash)
                    continue
                links = self.extract_links(website, current_url)
                #print(self.name, links)
                self.add_to_frontier(links, page_id)
                self.db.update_page_to_html(id=page_id, html_content=website, http_status_code=status_code, hash=minHash)

                # only parse images from initial four domains; have to add http(s) to site and canonicalize beforehand
                if self.canonicalize("http://" + self.get_site(url)) in self.FRONTIER or self.canonicalize(
                        "https://" + self.get_site(url)) in self.FRONTIER:
                    images = self.extract_images(website, current_url)
                    for image in images:
                        image = self.canonicalize(image, ending_slash_check=False)
                        #print(self.name, image)
                        image_data, image_url, status_code = self.download_website(image)
                        if image_data is not None:
                            image_type = self.get_image_type(image_url)
                            self.db.add_image(page_id, image, image_type, image_data, time.time())

                    documents = self.extract_documents(website, current_url)
                    for document in documents:
                        document = self.canonicalize(document, ending_slash_check=False)
                        #print(self.name, document)
                        document_data, document_url, status_code = self.download_website(document)
                        if document_data is not None:
                            document_type = self.get_document_type(document_url)
                            if document_type is not None:
                                self.db.add_page_data(page_id, document_type, document_data)
            except:
                print(self.name,"FATAL ERROR: ", url)
                traceback.print_exc()

        if self.driver is not None:
            self.driver.close()


    def canonicalize(self, url, ending_slash_check=True):
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
            replaces.append(url[parent_slash:up] + "/..")
        for r in replaces:
            url = url.replace(r, "")
        # add trailing slash if root or directory TODO: GET parameters and '.'
        if ending_slash_check and url[-1] != "/" and (url.count("/") == 2 or url[-5:].count(".") == 0):
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
        # print(url)
        return url

    def filter_javascript_link(self, link):
        if "javascript:" not in link:
            return link
        else:
            return None

    def init_selenium(self):
        options = Options()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(executable_path="webdriver/chromedriver.exe", options=options)

    def get_site(self, url):
        parse = urlparse(url)
        return parse.hostname

    def get_next_url(self, ):
        # take next page from pages table marked with frontier code order by accessed_time
        data = self.db.get_next_N_frontier(N=1)
        # 0: id (page_id), 1: site_id (FK), 2: url
        if len(data) > 0:
            data = data[0]
            return data[0], data[1], data[2]
        else:
            return None, None, None

    def download_website(self, url):

        try:
            if self.driver is None:
                self.init_selenium()
            self.driver.get(url)

            # for status code
            request = requests.get(url)

            return self.driver.page_source, self.driver.current_url, request.status_code
        except:
            print(self.name, "[Selenium] ERROR PARSING URL: ", url)
            return None, None, None

    def extract_links(self, website, current_url):
        html = BeautifulSoup(website, "html.parser")
        base = html.find_all("base", href=True)
        # base attribute specifies the 'base' url when constructing absolute links from relative paths
        if base is not None and len(base) == 1:
            current_url = base[0]["href"]
        a = html.find_all("a", href=True)
        links = []
        for link in a:
            href = link["href"]
            # filter empty links, anchor links and root links
            if len(href) > 0 and href[0] != "#" and href != "/" and self.filter_javascript_link(href) is not None and \
                    self.get_document_type(href) is None:
                links.append(self.change_link_to_absolute(href, current_url))
        # check a tags with onclick events
        a = html.find_all("a", onclick=True)
        for link in a:
            onclick = link["onclick"]
            #print(self.name, onclick)
            result = re.search(".*location.href=[\s]*['\"](.*)['\"][\s]*[;].*", onclick)
            if result is not None:
                print(self.name, "onclick JS URL found: ", result.group(1))
                links.append(result.group(1))
        return links

    def extract_images(self, website, current_url):
        html = BeautifulSoup(website, "html.parser")
        base = html.find_all("base", href=True)
        # base attribute specifies the 'base' url when constructing absolute links from relative paths
        if base is not None and len(base) == 1:
            current_url = base[0]["href"]
        a = html.find_all("img", src=True)
        images = []
        for image in a:
            src = image["src"]
            # filter empty links, anchor links and root links
            if len(src) > 0 and src[0] != "#" and src != "/" and src.find("data:image/") < 0:
                images.append(self.change_link_to_absolute(src, current_url))
        return images

    def extract_documents(self, website, current_url):
        html = BeautifulSoup(website, "html.parser")
        base = html.find_all("base", href=True)
        # base attribute specifies the 'base' url when constructing absolute links from relative paths
        if base is not None and len(base) == 1:
            current_url = base[0]["href"]
        a = html.find_all("a", href=True)
        documents = []
        for link in a:
            href = link["href"]
            # filter empty links, anchor links and root links
            if len(href) > 0 and href[0] != "#" and href != "/" and \
                    href.upper().endswith(("." + constants.DATA_TYPE_CODE_PDF, "." + constants.DATA_TYPE_CODE_DOC,
                                           "." + constants.DATA_TYPE_CODE_DOCX, "." + constants.DATA_TYPE_CODE_PPT,
                                           "." + constants.DATA_TYPE_CODE_PPTX)):
                documents.append(self.change_link_to_absolute(href, current_url))
        return documents

    def change_link_to_absolute(self, link, current_url):
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

    def is_page_allowed(self, url, robots_content):
        if robots_content == constants.DATABASE_NULL:
            return True
        robots_content = eval(robots_content)
        allow = True
        relative_url = url.split(self.get_site(url))[1]

        # Check if relative url matches any Allow directive (used for subdirectories or files of disallowed directories)
        # If true -> allow
        # else -> check Disallow directives
        for line in robots_content["Allow"]:
            if len(line) == 0:
                continue
            if line == relative_url:
                return True
            regex = "^" + line.replace("*", ".*") + "$"
            if re.match(regex, relative_url) is not None:
                return True

        # Check if relative url matches and Disallow directive
        # If true -> disallow
        # else -> allow
        for line in robots_content["Disallow"]:
            if len(line) == 0:
                continue
            regex = "^" + line.replace("*", ".*") + "$"
            if re.match(regex, relative_url) is not None:
                allow = False
                break

            if '*' == line[0] and ('*' == line[-1] or '/' == line[-1]):
                if url.find(line[1:-1]) != -1:
                    allow = False
                    # print("throwin false in first if")
                    break
            elif '*' == line[0]:
                if url.endswith(line[1:]):
                    allow = False
                    # print("throwin false in second if")
                    break
            elif '/' == line[0]:
                if relative_url.startswith(line):
                    allow = False
                    # print("throwin false in third if")
                    break
        return allow
    
    # we need url to resolve relative links
    def add_to_frontier(self, links, current_page_id):
        for link in links:
            site_data = self.db.find_site(self.get_site(link))
            if len(site_data) == 0:
                # new site/domain; add site to db and page to frontier
                self.new_site(link, current_page_id)
            else:
                # site exists in db, check for duplicate links and add page to frontier
                site_id = site_data[0][0]
                duplicate = self.find_website_duplicate(link)
                allowed = self.is_page_allowed(link, site_data[0][2])
                if duplicate is None and allowed:
                    self.db.add_page(site_id=site_id, url=link, accessed_time=time.time(), from_id=current_page_id)

    # check if URL is already in a frontier
    def find_website_duplicate(self, url):
        url1 = url
        if url.find("www") != -1:
            tmp = url.split("://www")
            url2 = tmp[0] + "://" + tmp[1]
        else:
            tmp = url.split("://")
            url2 = tmp[0] + "://www." + tmp[1]
        ids = self.db.get_duplicated_pages(url1, url2)
        if len(ids) == 0:
            return None
        return ids[0]

    def find_duplicate_content(self, minHash1):
        all_pages = self.db.get_all_page_hashes()
        for p in range(len(all_pages)):
            minHash2 = re.sub("[{}]", "", all_pages[p][2]).split(',')
            jaccard = len(list(set(minHash1) & set(minHash2)))/len(list(set(minHash1) | set(minHash2)))
            if jaccard >= 0.70:
                return 1
        return 0

    # List of k unique random values.
    def random_coeffitients(self):
        random.seed(30)
        rand_list = [] 
        for i in range(self.len_of_hash, 0, -1):
            rand_index = random.randint(0, self.max_shingle_id)
            while rand_index in rand_list:
                rand_index = random.randint(0, self.max_shingle_id)
            rand_list.append(rand_index)    
        return rand_list
    
    def minHash_content(self, website):
        #converting content of website to a set of shingles and hash each single
        shingles = [binascii.crc32(website[i:i+self.len_of_shingle].encode('utf-8')) & 0xffffffff for i in range(len(website)-self.len_of_shingle+1)]
        if self.coeff_a == None:
            self.coeff_a = self.random_coeffitients()
            self.coeff_b = self.random_coeffitients()
        #generating minHash signature
        signature = [min([((self.coeff_a[i] * j + self.coeff_b[i]) % self.next_prime) for j in shingles]) for i in range(self.len_of_hash)]
        return signature

    def get_robots_txt(self, url):
        if url.endswith("/") == False:
            url = url + "/"
        try:
            r = requests.get(url + "robots.txt")
            resp = r.text
            if r.status_code < 400:
                data = {"User-agent": [], "Disallow": [], "Allow": [], "Crawl-delay": []}
                sitemap = []
                # TODO: some robots.txt files don't parse correctly. See https://github.com/VGV-Team/StandaloneCrawler/issues/23
                # Added some code to only parse relevant robots.txt segments where User-agent == *
                our_user_agent = False
                for line in resp.split("\n"):
                    if line.lower().find("user-agent") != -1:
                        ua = re.sub(r"[\n\t\s]*", "", line).split(":")[1]
                        if ua == "*":
                            data["User-agent"].append(ua)
                            our_user_agent = True
                        else:
                            our_user_agent = False
                    if our_user_agent:
                        if line.lower().find("disallow") != -1:
                            data["Disallow"].append(re.sub(r"[\n\t\s]*", "", line).split(":")[1])
                        elif line.lower().find("allow") != -1:
                            data["Allow"].append(re.sub(r"[\n\t\s]*", "", line).split(":")[1])
                        elif line.lower().find("crawl-delay") != -1:
                            data["Crawl-delay"].append(re.sub(r"[\n\t\s]*", "", line).split(":")[1])
                        elif line.lower().find("sitemap") != -1:
                            sitemap.append(re.sub(r"[\n\t\s]*", "", line).split(":", 1)[1])
                if len(sitemap) == 0:
                    return str(data), constants.DATABASE_NULL
                return str(data), sitemap
        except requests.exceptions.RequestException as e:
            return constants.DATABASE_NULL, constants.DATABASE_NULL
        return constants.DATABASE_NULL, constants.DATABASE_NULL

    def read_sitemap(self, sitemap, url):
        l = []
        for i in sitemap:
            try:
                r = requests.get(i)
                resp = r.text
                if r.status_code == 200:
                    s = BeautifulSoup(resp, 'lxml')
                    for loc in s.findAll('loc'):
                        #checking if url in sitemap == url
                        if url.find("www") != -1:
                            tmp = url.split("://www")
                            url2 = tmp[0] + "://" + tmp[1]
                            if loc.text != url2:
                                l.append(loc.text)  
                        else:
                            tmp = url.split("://")
                            url2 = tmp[0] + "://www." + tmp[1]
                            if loc.text != url2:
                                l.append(loc.text)  
                    return l
            except requests.exceptions.RequestException as e:
                print("Can not fetch sitemap.")

    # creates new site(domain) and adds the page to frontier
    def new_site(self, url, current_page_id):
        site = self.get_site(url)
        if site.endswith(".gov.si") or site.endswith(".gov.si/"):
            # get robots.txt and parse it
            robots, sitemap = self.get_robots_txt(url)  # robots spremenimo nazaj v dict z eval()
            site_id = self.db.add_site(site, robots, sitemap)
            if self.is_page_allowed(url, robots):
                page_id = self.db.add_page(site_id, url, time.time(), current_page_id)
            # add sitemap in frontier
            if sitemap != constants.DATABASE_NULL:
                l = self.read_sitemap(sitemap, url)
                self.add_to_frontier(l, page_id)

    def get_image_type(self, url):
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

    def get_document_type(self, url):
        res = list(filter(url.upper().endswith, ("." + constants.DATA_TYPE_CODE_PDF,
                                                 "." + constants.DATA_TYPE_CODE_DOC,
                                                 "." + constants.DATA_TYPE_CODE_DOCX,
                                                 "." + constants.DATA_TYPE_CODE_PPT,
                                                 "." + constants.DATA_TYPE_CODE_PPTX)))
        if len(res) == 0:
            return None
        else:
            return res[0].strip(".")
