from page_retrieval import is_page_allowed

'''
rc = "{'Disallow': ['/iskanje', '/bin/', '/lbin/', '/adserver/', '*modal:*']}"
urls = ["https://www.24ur.com/iskanje", "https://www.24ur.com/iskanje?q=asdasdasd", "https://www.24ur.com/novice",
        "https://www.24ur.com/novice/gospodarstvo", "https://www.24ur.com/bin/gospodarstvo", "https://www.24ur.com/bin/",
       "https://www.24ur.com/qeqwe/bin/", "https://www.24ur.com/bin"]
'''

rc = "{'User-agent': ['*'], 'Disallow': ['/fileadmin/global/', '*no_cache*', '/t3lib/Disallow', '/*cHash', '/typo3/', '/urednik/', '/typo3conf/', '/typo3temp/', '/*?id=*', '/*&type=98', '/*&type=100'], 'Allow': ['/', '/fileadmin/global/neki/*'], 'Crawl-delay': []}"
urls = ["http://www.e-prostor.gov.si/", "http://www.e-prostor.gov.si/fileadmin/qwe",
        "http://www.e-prostor.gov.si/fileadmin/global", "http://www.e-prostor.gov.si/fileadmin/global/",
        "http://www.e-prostor.gov.si/fileadmin/global/neki/qwe.html",
        "http://www.e-prostor.gov.si/fileadmin/qwe/no_cache/qwe.html",
        "http://www.e-prostor.gov.si/neki_cHash", "http://www.e-prostor.gov.si/neki_cHashqwe",
        "http://www.e-prostor.gov.si/neki_cHash/qwe",
        "http://www.e-prostor.gov.si/neki/neki/qwe/asd?id=123&kaj_vrne=false",
        "http://www.e-prostor.gov.si/neki/asd?kva=true", "http://www.e-prostor.gov.si/neki/asd?kva=false&type=98"]

for u in urls:
    print(u, " ---- ", is_page_allowed(u, rc))