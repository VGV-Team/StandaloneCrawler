# cannonicalize() TEST
import re
def canonicalize(url, ending_slash_check=True):
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
    url = "/".join(url_split[0:2]) + "/" + url_split[2].lower() + "/" + "/".join(url_split[3:])
    print(url)
    return url

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
