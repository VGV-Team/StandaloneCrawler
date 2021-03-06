from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import constants
import time
import traceback
import requests
import re
import binascii
import random
from bs4 import BeautifulSoup

class PageRetrieval:

    def __init__(self, thread_name, database_lock, stop_callback, db):
        self.name = thread_name
        self.database_lock = database_lock
        self.stop_callback = stop_callback
        #self.db = DatabaseInterface(database_lock)
        self.db = db

        '''

        self.FRONTIER = ["http://evem.gov.si",
                         "http://e-prostor.gov.si",
                         "http://e-uprava.gov.si",
                         "http://podatki.gov.si"

        '''

        self.FRONTIER = ["http://evem.gov.si",
                         "http://e-prostor.gov.si",
                         "http://e-uprava.gov.si",
                         "http://podatki.gov.si"]

        self.FRONTIER_NEW = ["http://www.gov.si",
                             "http://www.stopbirokraciji.gov.si",
                             "http://www.ukom.gov.si",
                             "http://www.gu.gov.si",
                             "http://www.fu.gov.si"]

        self.canonicalize_frontier()
        self.driver = None

        self.len_of_shingle = 8
        self.len_of_hash = 250
        self.max_shingle_id = 2 ** 32 - 1
        self.next_prime = 4294967311

        self.coeff_a = None
        self.coeff_b = None

    def canonicalize_frontier(self):
        self.FRONTIER = [self.canonicalize(f) for f in self.FRONTIER]
        self.FRONTIER_NEW = [self.canonicalize(f) for f in self.FRONTIER_NEW]

    def initialize_database(self):
        self.db.delete_all_data()
        for url in self.FRONTIER:
            self.new_site(self.canonicalize(url), None, 0)
        #for url in self.FRONTIER_NEW:
        #    self.new_site(self.canonicalize(url), None)

    def run(self):

        while not self.stop_callback.is_set():
            try:
                page_id, site_id, url, depth = self.get_next_url()
                if page_id is None or site_id is None or url is None:
                    # if frontier is empty, wait a few seconds
                    time.sleep(constants.CRAWLER_EMPTY_FRONTIER_SLEEP)
                    print(self.name + " found empty frontier, waiting...")
                    continue
                url = self.canonicalize(url)
                url_test = self.get_site(url)
                url_test = url_test[4:] if url_test.startswith("www.") else url_test
                #if self.canonicalize("http://" + url_test) in self.FRONTIER or self.canonicalize(
                #        "https://" + url_test) in self.FRONTIER:
                if "e-prostor.gov.si" in url_test or "evem.gov.si" in url_test:
                    print(self.name + " is processing URL " + url)
                    website, current_url, status_code = self.download_website(url)
                    if website is None:
                        self.db.update_page_to_html(id=page_id, html_content=constants.DATABASE_NULL,
                                                    http_status_code="408", hash=constants.DATABASE_NULL)
                        continue
                    current_url = self.canonicalize(current_url)
                    minHash = self.minHash_content(website)
                    find_duplicate = self.find_duplicate_content(minHash)
                    if find_duplicate != 0:
                        self.db.update_page_to_duplicate(id=page_id, http_status_code=status_code, hash=minHash)
                        continue
                    if status_code >= 400:
                        self.db.update_page_to_html(id=page_id, html_content=website, http_status_code=status_code,
                                                    hash=constants.DATABASE_NULL)
                        continue
                    links = self.extract_links(website, current_url)
                    self.add_to_frontier(links, page_id, depth+1)
                    if len(minHash) == 0:
                        self.db.update_page_to_html(id=page_id, html_content=website, http_status_code=status_code, hash=constants.DATABASE_NULL)
                    else:
                        self.db.update_page_to_html(id=page_id, html_content=website, http_status_code=status_code, hash=minHash)

                    # only parse images from initial four domains; have to add http(s) to site and canonicalize beforehand

                    '''
                    
                    url_test = self.get_site(url)
                    url_test = url_test[4:] if url_test.startswith("www.") else url_test
                    if self.canonicalize("http://" + url_test) in self.FRONTIER or self.canonicalize(
                            "https://" + url_test) in self.FRONTIER:

                        site_data = self.db.find_site(self.get_site(url))

                        images = self.extract_images(website, current_url)
                        for image in images:
                            image = self.canonicalize(image, ending_slash_check=False)

                            if not self.is_page_allowed(image, site_data[0][2]):
                                continue
                            print(self.name + " is parsing image " + image)
                            image_data, image_url, status_code = self.download_website(image)
                            if image_data is not None:
                                image_type = self.get_image_type(image_url)
                                if image_type is not None:
                                    self.db.add_image(page_id, image, image_type, image_data, time.time())
                                    # self.add_binary_page(url=image, site_id=site_id, from_id=page_id,
                                    #                     status_code=status_code, depth=depth)

                        documents = self.extract_documents(website, current_url)
                        for document in documents:
                            document = self.canonicalize(document, ending_slash_check=False)
                            if not self.is_page_allowed(document, site_data[0][2]):
                                continue
                            print(self.name + " is parsing document " + document)
                            document_data, document_url, status_code = self.download_website(document)
                            if document_data is not None:
                                document_type = self.get_document_type(document_url)
                                if document_type is not None:
                                    self.db.add_page_data(page_id, document_type, document_data)
                                    # self.add_binary_page(url=document, site_id=site_id, from_id=page_id,
                                    #                     status_code=status_code, depth=depth)
                                    
                                    
                    '''

            except:
                print(self.name + " encountered a FATAL ERROR at URL " + url)
                traceback.print_exc()

        if self.driver is not None:
            self.driver.close()

    def add_binary_page(self, url, site_id, from_id, status_code, depth):
        binary_page_id = self.db.add_page(site_id=site_id, url=url, accessed_time=time.time(), from_id=from_id,
                                          depth=depth)
        self.db.update_page_to_binary(id=binary_page_id, http_status_code=status_code)

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
        if len(url_split) > 3:
            url = "/".join(url_split[0:2]) + "/" + url_split[2].lower() + "/" + "/".join(url_split[3:])
        # replace ' ' with %20
        url = url.replace(" ", "%20")
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
            return data[0], data[1], data[2], data[3]
        else:
            return None, None, None, None

    def download_website(self, url):

        try:
            if self.driver is None:
                self.init_selenium()
            self.driver.get(url)

            # for status code
            request = requests.get(url)

            return self.driver.page_source, self.driver.current_url, request.status_code
        except:
            print(self.name, " got [Selenium] ERROR PARSING URL " + url)
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
        a = html.find_all(onclick=True)
        for link in a:
            onclick = link["onclick"]
            result = re.search(".*location.href=[\s]*['\"](.*)['\"][\s]*[;].*", onclick)
            if result is not None:
                print(self.name + " found onclick JS URL " + result.group(1))
                links.append(result.group(1))
                continue
            result = re.search(".*document.location=[\s]*['\"](.*)['\"][\s]*[;].*", onclick)
            if result is not None:
                print(self.name + " found onclick JS URL " + result.group(1))
                links.append(result.group(1))
                continue
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
            # if starts with '/', append link to root (site)
            if link[0] == "/":
                site = self.get_site(current_url)
                protocol = "https://" if current_url.startswith("https://") else "http://"
                return protocol + site + link
            # else if current doesn't end with '/' add it
            slash = ""
            if current_url[-1] != "/":
                slash = "/"
                cur_url = "/".join(current_url.split("/")[0:-1])
            else:
                cur_url = current_url
            return cur_url + slash + link
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
            if len(line) == 0 or line == "/":
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
                    break
            elif '*' == line[0]:
                if url.endswith(line[1:]):
                    allow = False
                    break
            elif '/' == line[0]:
                if relative_url.startswith(line):
                    allow = False
                    break
        return allow
    
    # we need url to resolve relative links
    def add_to_frontier(self, links, current_page_id, depth):
        for link in links:

            url_test = self.get_site(link)
            if url_test is not None:
                url_test = url_test[4:] if url_test.startswith("www.") else url_test
                #if self.canonicalize("http://" + url_test) in self.FRONTIER or self.canonicalize(
                #        "https://" + url_test) in self.FRONTIER:
                if "e-prostor.gov.si" in url_test or "evem.gov.si" in url_test:

                    site_data = self.db.find_site(self.get_site(link))
                    if len(site_data) == 0:
                        # new site/domain; add site to db and page to frontier
                        self.new_site(link, current_page_id, depth)
                    else:
                        # site exists in db, check for duplicate links and add page to frontier
                        site_id = site_data[0][0]
                        link = self.canonicalize(link)
                        duplicate = self.find_website_duplicate(link)
                        allowed = self.is_page_allowed(link, site_data[0][2])
                        if duplicate is None and allowed:
                            self.db.add_page(site_id=site_id, url=link, accessed_time=time.time(),
                                             from_id=current_page_id, depth=depth)

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
            minHash2 = all_pages[p][2]
            s1 = set(minHash1)
            s2 = set(minHash2)
            jaccard = len(s1.intersection(s2)) / len(s1.union(s2))
            if jaccard > 0.99:
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
        soup = BeautifulSoup(website, 'html.parser')
        text = re.sub(r"[\n\t\s]*", "", soup.get_text())
        if len(text) != 0 :
            shingles = [binascii.crc32(text[i:i+self.len_of_shingle].encode('utf-8')) & 0xffffffff
                    for i in range(len(text)-self.len_of_shingle+1)]
            if self.coeff_a == None:
                self.coeff_a = self.random_coeffitients()
                self.coeff_b = self.random_coeffitients()
            #generating minHash signature
            signature = [min([((self.coeff_a[i] * j + self.coeff_b[i]) % self.next_prime)
                          for j in shingles]) for i in range(self.len_of_hash)]
            return signature
        return []

    def get_robots_txt(self, url):
        if url.endswith("/") == False:
            url = url + "/"
        try:
            r = requests.get(url + "robots.txt")
            resp = r.text
            if r.status_code < 400:
                data = {"User-agent": [], "Disallow": [], "Allow": []}
                sitemap = []
                # Added some code to only parse relevant robots.txt segments where User-agent == *
                our_user_agent = False
                for line in resp.splitlines():
                    if line.lower().find("user-agent") != -1:
                        ua = re.sub("[\n\t\s]", "", line).split(":")[1]
                        if ua == "*":
                            data["User-agent"].append(ua)
                            our_user_agent = True
                        else:
                            our_user_agent = False
                    if our_user_agent:
                        if line.lower().find("disallow") != -1:
                            data["Disallow"].append(re.sub("[\n\t\s]", "", line).split(":")[1])
                        elif line.lower().find("allow") != -1:
                            data["Allow"].append(re.sub("[\n\t\s]", "", line).split(":")[1])
                        elif line.lower().find("crawl-delay") != -1:
                            data["Crawl-delay"] = re.sub("[\n\t\s]", "", line).split(":")[1]
                        elif line.lower().find("sitemap") != -1:
                            sitemap.append(re.sub("[\n\t\s]", "", line).split(":", 1)[1])
                if len(sitemap) == 0:
                    return str(data), constants.DATABASE_NULL, data.get("Crawl-delay", constants.DEFAULT_CRAWL_DELAY)
                return str(data), sitemap, data.get("Crawl-delay", constants.DEFAULT_CRAWL_DELAY)
        except requests.exceptions.RequestException as e:
            return constants.DATABASE_NULL, constants.DATABASE_NULL, constants.DATABASE_NULL
        return constants.DATABASE_NULL, constants.DATABASE_NULL, constants.DATABASE_NULL

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
    def new_site(self, url, current_page_id, depth):
        site = self.get_site(url)
        if site is None:
            print(self.name + " could not parse site (domain) from " + url)
        elif site.endswith(".gov.si") or site.endswith(".gov.si/"):
            # get robots.txt and parse it
            if url.startswith("https://"):
                robots_site = "https://" + site
            elif url.startswith("http://"):
                robots_site = "http://" + site
            else:
                robots_site = site
            robots, sitemap, crawl_delay = self.get_robots_txt(robots_site)  # robots spremenimo nazaj v dict z eval()
            site_id = self.db.add_site(site, robots, sitemap, crawl_delay)
            if self.is_page_allowed(url, robots):
                page_id = self.db.add_page(site_id, url, time.time(), current_page_id, depth)
            # add sitemap in frontier
            if sitemap != constants.DATABASE_NULL:
                l = self.read_sitemap(sitemap, url)
                self.add_to_frontier(l, page_id, depth+1)

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

