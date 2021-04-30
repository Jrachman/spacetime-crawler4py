import re
from urllib.parse import urlparse
from urllib.parse import urldefrag
from bs4 import BeautifulSoup
import logging
import string
import config
from utils import get_logger
###############################################################

### GLOBAL VARIABLES ###
def initialize_globals():
    config.stopwords = [
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", "as", "at",
        "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", 
        "can't", "cannot", "could", "couldn't",
        "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", 
        "each",
        "few", "for", "from", "further",
        "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
        "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself",
        "let's",
        "me", "more", "most", "mustn't", "my", "myself",
        "no", "nor", "not",
        "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own",
        "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
        "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too",
        "under",
        "until", "up",
        "very",
        "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't",
        "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
    ]

    #CURRENT URL
    config.current_url = ""

    # Full global list of full urls we've been to
    config.all_urls_traversed = []
    config.all_url_bases = set()
    # List of bad links
    config.all_bad_links = []

    # Longest page in number of words
    config.longest_page = ("null", 0)

    # DICT OF SUBDOMAINS AND NUMBER OF UNIQUE PAGES IN EACH SUBDOMAIN, ALPHABETICALLY
    config.subdomain_counter = dict()

    # MASTERLIST OF TOKENS (TODO: Too much space taken up? Perhaps save top 50 only?)
    config.token_masterlist = [] # does not contain stopwords, does contain duplicates
    config.token_frequency_masterlist = dict() # No duplicates

    # create logger
    config.logger = get_logger("run", "run")
    config.logger.info("***** run logger initialized *****")

########################

def scraper(url, resp):
    # logging.basicConfig(filename="run.log", filemode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)
    # logging.basicConfig(level=logging.INFO, filename="output.log")

    config.current_url = url
    config.logger.info("************************")
    config.logger.info("NEW SCRAPER CALL on url: " + str(config.current_url) + " type: " + str(type(config.current_url)))
    config.logger.info("Response status: " + str(resp.status) + ", type: " + str(type(resp.status)))
    # print("************************")
    # print("NEW SCRAPER CALL on url: " + str(config.current_url) + " type: " + str(type(config.current_url)))
    # print("Response status: " + str(resp.status) + ", type: " + str(type(resp.status)))

    #POSSIBLE TODO IMPLEMENTATION: 
    if (len(config.all_urls_traversed) >= 30000):
        #TODO: One final failsafe? Cap the number of links that can be traversed at ~30,000?
        config.logger.info("TRAVERSAL LIMIT REACHED (3000 links) -- terminating.")
        # print("TRAVERSAL LIMIT REACHED (3000 links) -- terminating.")

        return []
    

    # IF the url is a new one/ has not been traversed already
    if url not in config.all_urls_traversed:
        config.logger.info("New and unique URL found")
        # print("New and unique URL found")
        # logging.debug("Response: " + str(resp.content))
        
        config.all_urls_traversed.append(url)
        config.all_url_bases.add(get_url_base())

        links = extract_next_links(url, resp)

        lst_of_valid_links = []
        for l in links:
            result = is_valid(l)
            if result["is_valid"] == True:
                lst_of_valid_links.append(result["new_url"])

        # return [link for link in links if is_valid(link)]
        return lst_of_valid_links

    else: # The URL is one we've seen before
        config.logger.info("URL ALREADY PARSED: " + str(url))
        # print("URL ALREADY PARSED: " + str(url))
        return []
    

def is_large(response_text, response_tokens): # We need to find a measure by which to decide if large/irrelevant, 
    # response_tokens == list, response_text == string
    config.logger.info("Enter method is_large()")
    # print("Enter method is_large()")

    len_tokens = len(response_tokens)
    soup_text = BeautifulSoup(response_text, 'html.parser')

    # an image to text ratio of the page
    img_elems = soup_text.find_all("img")
    if (len(img_elems)/len_tokens > 0.5): #TODO: Percent?
        return True    

    # limit by amount of tokens - overestimate first
    if len(response_tokens) > 1750:
        # should overestimate to make sure we don't throw out good links 
        # thought process:
        # - a 5-page essay is about 2.5k words
        # - unique words equal approximately 10-20% of the total words in an essay 
        #   (e.g., 2.5k x 0.1 = 250)
        # - with this, we determined ~double a 5-page essay and 25% unique words would be too large
        #   (e.g., 2.5k x 2 = 5k x 0.25 = 1750 tokens max)
        return True

    return False

def is_dead_url(resp): # 200 response = continue; 404 = add to bad list
    config.logger.info("Enter method is_dead_url()")
    # print("Enter method is_dead_url()")
    # checks if the url is dead using the requests library 
    if config.current_url in config.all_bad_links:
        return True

    if resp.status != 200: #TODO: Check formatting
        config.all_bad_links.append(config.current_url)
        return True
    else: # if it's 200
        return False
    

def is_similar(response_tokens):
    config.logger.info("Enter method is_similar()")
    #print("Enter method is_similar()")
    # create a unique token-list by getting keys of token_frequency_masterlist
    all_tokens = list(config.token_frequency_masterlist.keys())
    temp1 = []
    temp2 = []

    X_set = set(w for w in all_tokens)
    Y_set = set(w for w in response_tokens)

    # form a set containing keywords of both strings 
    rvector = X_set.union(Y_set)
    for w in rvector:
        if w in X_set: 
            temp1.append(1) 
        else: 
            temp1.append(0)
        if w in Y_set: 
            temp2.append(1)
        else: 
            temp2.append(0)
    c = 0
    
    # cosine formula 
    for i in range(len(rvector)):
        c+= temp1[i]*temp2[i]
    
    denom = float((sum(temp1)*sum(temp2))**0.5)
    if denom == 0:
        config.logger.error("DENOM is 0")        
        print("DENOM is 0")
        return False

    cosine = c / denom
    # print("similarity: ", cosine) 
    config.logger.info("similarity: " + str(cosine))

    #TODO: CHECK ON THESE VALUES/IF THEY'RE REASONABLE!!
    if (cosine > 0.80):
        return True
    else:
        return False

def get_url_base():
    print("in get_url_base()")
    config.logger.info("in get_url_base()")
    baseList = config.current_url.split("/")
    if len(baseList) > 1:
        base = baseList[0] + "//" +  baseList[1]
        return base

    config.logger.error("Current URL: " + config.current_url + " doesn't have multiple elements")
    # print("Current URL: " + config.current_url + " doesn't have multiple elements")
    return baseList[0]
    

def add_tokens_globally(tokens):
    unique_tokens_added = 0
    config.logger.info("Enter method: add_tokens_globally()")
    #print("Enter method: add_tokens_globally()")
    # Returns void
    for token in tokens:
        if token not in config.token_frequency_masterlist.keys():
            unique_tokens_added += 1
            config.logger.info("NEW TOKEN")
            #print("NEW TOKEN")
            config.token_masterlist.append(token)
            config.token_frequency_masterlist[token] = 1
        else :
            config.logger.info("Old token")
            #print("Old token")
            config.token_frequency_masterlist[token] =  config.token_frequency_masterlist[token]+1
    config.logger.info("Tokens added to masterlists. Total of tokens: " + str(len(config.token_masterlist)) + 
                    " | Num of unique tokens from this page: " + str(unique_tokens_added)) 
    # print("Tokens added to masterlists. Total of tokens: " + str(len(config.token_masterlist)) + 
                    # " | Num of unique tokens from this page: " + str(unique_tokens_added)) 

def tokenize(full_text):
    config.logger.info("Enter method tokenize()")
    # print("Enter method tokenize()")
    # inital clean: lowercase everything
    txt = full_text.lower()

    # remove punctuation, control chars
    txt = re.sub(r'[{}]|\n|\t'.format(string.punctuation), " ", txt)

    # create tokens list
    tokens = re.findall(r"[\w]+", txt)
    
    #tokens = [t for t in word_tokens if len(t) >= 3] # TODO: Consider adding back in? but we remove stopwords later anyway
    
    #Check to see if largest page
    if (len(tokens) > config.longest_page[1]):
        config.logger.info("Overrode longest page of " + str(config.longest_page[1]) + " tokens")
        # print("Overrode longest page of " + str(config.longest_page[1]) + " tokens")

        config.longest_page = (config.current_url, len(tokens))

    config.logger.info("Num of tokens: " + str(len(tokens)))
    # print("Num of tokens: " + str(len(tokens)))
    return tokens

def extract_next_links(url, resp):
    config.logger.info("Enter method extract_next_links()")
    # print("Enter method extract_next_links()")
    return_urls = []

    response_text = resp.raw_response.content
    soup_text = BeautifulSoup(response_text, 'html.parser')

    # logging.debug("Article Title:" + soup_text.title)

    # IDEALLY: no link will be traversed twice 
    base = get_url_base()
    if base in config.subdomain_counter: 
        config.subdomain_counter[base] = config.subdomain_counter[base] + 1
        config.logger.info("--subdomain counter incremented-- " + str(base) + " : " + str(config.subdomain_counter[base]))
        # print("--subdomain counter incremented-- " + str(base) + " : " + str(config.subdomain_counter[base]))
    else:
        config.subdomain_counter[base] = 1
        config.logger.info("--subdomain counter added-- " + str(base) + " : " + str(config.subdomain_counter[base]))
        # print("--subdomain counter incremented-- " + str(base) + " : " + str(config.subdomain_counter[base]))

    ### TOKENIZE THE TEXT ###
    raw_tokens = tokenize(soup_text.get_text())
    tokens = [token for token in raw_tokens if not token in config.stopwords] 

    ### QUALITY/ETC. CHECKING:
    if is_dead_url(resp) or is_large(response_text, tokens) or is_similar(tokens):
        # return an empty list of links
        config.logger.info("URL did not pass preprocessing step. Return [] ")
        # print("URL did not pass preprocessing step. Return [] ")
        return []
    
    ### POST-QUALITY CHECKS
    # Add tokens to masterlists 
    add_tokens_globally(tokens)
    
    print(return_urls, len(return_urls))

    return_urls = [a["href"] for a in soup_text.find_all('a', href=True)]
    config.logger.info("RETURN_URLS: " + str(return_urls))
    # print("RETURN_URLS: " + str(return_urls))
        
    return return_urls

def complete_logs():
    ### UNIQUE PAGES
    config.logger.info("NUMBER OF UNIQUE PAGES: " + str(len(config.all_url_bases)))
    # print("NUMBER OF UNIQUE PAGES: " + str(len(config.all_url_bases)))

    ### LONGEST PAGE
    config.logger.info("LONGEST PAGE FOUND: url = " + str(config.longest_page[0]) + " , num of tokens = " + str(config.longest_page[1]))
    # print("LONGEST PAGE FOUND: url = " + str(config.longest_page[0]) + " , num of tokens = " + str(config.longest_page[1]))
    
    ### TOP 50 most common words
    sorted_tokens = {k: v for k, v in sorted(config.token_frequency_masterlist.items(), key=(lambda x:x[1]), reverse=True)}
    top_tokens = dict()
    index = 0
    for key, value in sorted_tokens():
        if(index > 50):
            break
        else:
            top_tokens[key] = value
    
    config.logger.info("TOP 50 TOKENS: " + str(top_tokens))
    # print("TOP 50 TOKENS: " + str(top_tokens))
    
    ### HOW MANY SUBDOMAINS in the ics.uci.edu domain:
    special_subdomains = dict()
    for key in config.subdomain_counter.keys():
        if ".ics.uci.edu" in key:
            config.logger.info(key + " is in ics.uci.edu subdomain")
            special_subdomains[key] = config.subdomain_counter[key]
        else:
            config.logger.info("Not in ics.uci.edu subdomain.")

    config.logger.info("NUMBER OF SUBDOMAINS OF ics.uci.edu: " + str(len(special_subdomains)))
    config.logger.info(special_subdomains)
    # print("NUMBER OF SUBDOMAINS OF ics.uci.edu: " + str(len(special_subdomains)))
    # print(special_subdomains)



def is_valid(url): # need to change
    config.logger.info("Enter method is_valid()")
    print("Enter method is_valid()")
    # scenarios:
    # (leave) https://www.ics.uci.edu/hello-world (good!)
    # (https needed) www.ics.uci.edu/hello-world (needs https)
    # (leave) https://ics.uci.edu/hello-world (base is partially right, needs www)
    # (https needed) ics.uci.edu/hello-world (missing full base and https)
    # (https and base needed) /hello-world (missing base and https)
    url_base = get_url_base()
    config.logger.info("Input URL: "+ str(url))
    #print("Input URL: "+ str(url))
    try:
        parsed = urlparse(url)

        config.logger.info("Parsed scheme :"+ str(parsed.scheme))
        config.logger.info("Parsed netloc: "+ str(parsed.netloc))
        config.logger.info("Parsed path: "+ str(parsed.path))
        # print("Parsed scheme :"+ str(parsed.scheme))
        # print("Parsed netloc: "+ str(parsed.netloc))
        # print("Parsed path: "+ str(parsed.path))
        
        if parsed.scheme == '' and parsed.netloc == '' and parsed.path == '':
            config.logger.info("is_valid is FALSE; url : " + url)
            #print("is_valid is FALSE; url : " + url)
            return {
                "is_valid": False,
                "new_url": urldefrag(url).url
            }

        # normalization step (https://<base>/<whatever else>)
        if parsed.scheme not in set(["http", "https"]):
            # Add base http:// etc. at the start of the string and then try again, if still invalid, return false again
            
            # handles missing base and https
            if parsed.scheme == '' and parsed.netloc == '' and parsed.path[0:3] != 'www':
                if parsed.path[0] == '/':
                    return is_valid(url_base + url)
                else:
                    return is_valid('https://www.' + url)
            # handles missing 'https://'
            elif parsed.scheme == '' and parsed.netloc == '':
                return is_valid("https://" + url)
            # handles missing 'https:'
            elif parsed.scheme == '':
                return is_valid("https:" + url)
            else:
                config.logger.info("is_valid is FALSE; url : " + url)
                #print("is_valid is FALSE; url : " + url)
                return {
                    "is_valid": False,
                    "new_url": urldefrag(url).url
                }
        # handles missing 'www.'
        if parsed.path[0:3] != 'www' and parsed.netloc[0:3] != 'www':
            url = url[0:url.index(':')+3]+'www.'+url[url.index(':')+3:]

        # checking step (return false if not a webpage)
        if re.match( # need to 
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
            config.logger.info("is_valid is FALSE; url : " + url)
            #print("is_valid is FALSE; url : " + url)
            return {
                "is_valid": False,
                "new_url": urldefrag(url).url
            }
        
        # add check to match with allowed URLs -- need to test
        if re.match(r"^.*((.ics.uci.edu|.cs.uci.edu|.informatics.uci.edu|.stat.uci.edu)\/).*",url) or \
            re.match(r"^.*(today.uci.edu/department/information_computer_sciences\/).*",url):
            config.logger.info("is_valid is TRUE; url : " + url)
            #print("is_valid is TRUE; url : " + url)
            return {
                "is_valid": True,
                "new_url": urldefrag(url).url
            }

        config.logger.info("is_valid is FALSE; url : " + url)
        #print("is_valid is FALSE; url : " + url)
        return {
            "is_valid": False,
            "new_url": urldefrag(url).url
        }


    except TypeError:
        print ("TypeError for ", parsed)
        raise