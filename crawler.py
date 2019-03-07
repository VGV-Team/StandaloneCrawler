


def initialize_frontier():
    # do initial parsing of frontier URLs
    pass

def download_website(url):
    # retrieve and render website content
    # consider failed websites
    return "this is my website"

def extract_data(website):
    # extract web site content
    documents = extract_documents(website)
    return "images", documents, "urls"

def find_website_duplicate(url, website):
    # check if URL is already in a frontier
    return "duplicate url or None"

def parse_domain(url):
    # extract domain from url
    return "website domain"

def does_domain_exist(domain):
    # check if domain already exists
    return True

def store_data(site_id, website = None, images = None, documents = None, urls = None, is_binary = False, duplicate_link = None):
    # update current website page record (use site_id
    url = "one from urls"
    domain = parse_domain(url)
    if not does_domain_exist(domain):
        # create new domain in site table
        # parse robots.txt if it exists
        pass
    # add website to page table

def get_next_url():
    # take next page from pages table marked with frontier code order by accessed_time
    return "next url from page table"

def is_website_binary(website):
    # check if website is binary or HTML
    return False

def extract_documents(website):
    # extract binary document(s) from website
    return "extracted documents"

def main():
    url, site_id = get_next_url()
    website = download_website(url)
    link = find_website_duplicate(url, website)

    if link is not None: # this means it is duplicate
        store_data(site_id, duplicate_link=link)
    else:
        images = list()
        urls = list()
        is_binary = is_website_binary(website)
        if is_binary:
            # retrieve document and store it in appropriate table
            documents = extract_documents(website)
        else:
            images, documents, urls = extract_data(website)
        store_data(site_id, website, images, documents, urls, is_binary)

# TODO: database class/object

print("qwe")



