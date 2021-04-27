import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup

#Example usage of beautifulsoup4:
# soup = BeautifulSoup("<p>Some<b>bad<i>HTML")
# print(soup.prettify())

###############################################################

# GLOBAL VARIABLES
# Full global list of urls we've been to
# CREATE A GLOBAL SET OF URLS PARSED THROUGH W/O FRAGMENT
# DICT OF SUBDOMAINS AND NUMBER OF UNIQUE PAGES IN EACH SUBDOMAIN, ALPHABETICALLY

def scraper(url, resp):
    print("Response URL:" + str(resp.url))
    # print("Response content:" + str(resp.raw_response.content))
    # print("Response html: " + str(resp.content))
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def is_large(response_text): # We need to find a measure by which to decide if large/irrelevant
    #hello
    return False

def is_dead_url(response_text):
    #hello
    return False

def already_parsed(response_text):
    #hello
    return False

def extract_next_links(url, resp):
    # Implementation required.
    return_urls = []

    response_text = resp.raw_response.content
    soup_text = BeautifulSoup(response_text)

    if already_parsed(response_text):
        # exit function
        pass

    if is_large(response_text) or is_dead_url(response_text):
        # do nothing
        pass
    else:
        return_urls.extend([a["href"] for a in soup_text.find_all('a', href=True)])
    

    # for link in return_urls:
    #     if is_valid(link):
    #         print("Link is valid")
    #     else:
    #         print("Link not valid")
    
    print(return_urls, len(return_urls))
    
    return [] # return_urls

    # Functionality to implement: 
    # How many unique pages did we find, discard the fragment
    # What is the longest page in number of words
    # What are the 50 most common words in all the pages - ignore stopwords

    # Go through web page content -> tokenize for words, etc. 
    # if you find a URL, check is_valid(url), if yes, add to list

    # returns a LIST of URLS 

    return list()

def is_valid(url): # need to change
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise