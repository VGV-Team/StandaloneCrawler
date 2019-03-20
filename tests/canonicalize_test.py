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