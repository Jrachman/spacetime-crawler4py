import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import logging
import string
###############################################################

### GLOBAL VARIABLES ###

stopwords = [
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
current_url = ""

# Full global list of full urls we've been to
all_urls_traversed = []
all_url_bases = set()
# List of bad links
all_bad_links = []

# Longest page in number of words
longest_page = ("null", 0)

# DICT OF SUBDOMAINS AND NUMBER OF UNIQUE PAGES IN EACH SUBDOMAIN, ALPHABETICALLY
subdomain_counter = dict()

# MASTERLIST OF TOKENS (TODO: Too much space taken up? Perhaps save top 50 only?)
token_masterlist = [] # does not contain stopwords, does contain duplicates
token_frequency_masterlist = dict() # No duplicates

########################

def scraper(url, resp):
    # logging.basicConfig(filename="run.log", filemode='w', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO, filename="output.log")

    current_url = url
    logging.debug("************************")
    logging.debug("NEW SCRAPER CALL on url: " + str(current_url) + " type: " + str(type(current_url)))
    logging.debug("Response status: " + str(resp.status) + ", type: " + str(type(resp.status)))

    #POSSIBLE TODO IMPLEMENTATION: 
    if (len(all_urls_traversed) >= 30000):
        #TODO: One final failsafe? Cap the number of links that can be traversed at ~30,000?
        logging.debug("TRAVERSAL LIMIT REACHED (3000 links) -- terminating.")
        return []
    

    # IF the url is a new one/ has not been traversed already
    if url not in all_urls_traversed:
        logging.debug("New and unique URL found")
        # logging.debug("Response: " + str(resp.content))
        
        all_urls_traversed.append(url)
        all_url_bases.add(get_url_base())

        links = extract_next_links(url, resp)

        lst_of_valid_links = []
        for l in links:
            result = is_valid(l)
            if result["is_valid"] == True:
                lst_of_valid_links.append(result["new_url"])

        # return [link for link in links if is_valid(link)]
        return lst_of_valid_links

    else: # The URL is one we've seen before
        logging.debug("URL ALREADY PARSED: " + str(url))
        return []
    
    

def is_large(response_text, response_tokens): # We need to find a measure by which to decide if large/irrelevant, 
    # response_tokens == list, response_text == string
    logging.debug("Enter method is_large()")

    len_tokens = len(response_tokens)
    soup_text = BeautifulSoup(response_text, 'html.parser')

    # an image to text ratio of the page
    img_elems = soup_text.findall("img")
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
    logging.debug("Enter method is_dead_url()")
    # checks if the url is dead using the requests library 
    if current_url in all_bad_links:
        return True

    if resp.status != 200: #TODO: Check formatting
        all_bad_links.append(current_url)
        return True
    else: # if it's 200
        return False
    

def is_similar(response_tokens):
    logging.debug("Enter method is_similar()")
    # create a unique token-list by getting keys of token_frequency_masterlist
    all_tokens = list(token_frequency_masterlist.keys())
    temp1 = []
    temp2 = []

    # form a set containing keywords of both strings 
    rvector = all_tokens.union(response_tokens) 
    for w in rvector:
        if w in all_tokens: temp1.append(1) # create a vector
        else: temp1.append(0)
        if w in response_tokens: temp2.append(1)
        else: temp2.append(0)
    c = 0
    
    # cosine formula 
    for i in range(len(rvector)):
        c+= temp1[i]*temp2[i]
    cosine = c / float((sum(temp1)*sum(temp2))**0.5)
    print("similarity: ", cosine)

    #TODO: CHECK ON THESE VALUES/IF THEY'RE REASONABLE!!
    if (cosine > 0.80):
        return True
    else:
        return False

def get_url_base():
    baseList = current_url.split("/")
    if len(baseList) > 1:
        base = baseList[0] + "//" +  baseList[1]
        return base

    logging.error("Current URL: " + current_url + " doesn't have multiple elements")
    return baseList[0]
    

def add_tokens_globally(tokens):
    unique_tokens_added = 0
    logging.debug("Enter method: add_tokens_globally()")
    # Returns void
    for token in tokens:
        if token not in token_frequency_masterlist.keys():
            unique_tokens_added += 1
            logging.debug("NEW TOKEN")
            token_masterlist.append(token)
            token_frequency_masterlist[token] = 1
        else :
            logging.debug("Old token")
            token_frequency_masterlist[token] =  token_frequency_masterlist[token]+1
    logging.debug("Tokens added to masterlists. Total of tokens: " + str(len(token_masterlist)) + 
                    " | Num of unique tokens from this page: " + str(unique_tokens_added)) 

def tokenize(full_text):
    logging.debug("Enter method tokenize()")
    # inital clean: lowercase everything
    txt = full_text.lower()

    # remove punctuation, control chars
    txt = re.sub(r'[{}]|\n|\t'.format(string.punctuation), " ", txt)

    # create tokens list
    tokens = re.findall(r"[\w]+", txt)
    
    #tokens = [t for t in word_tokens if len(t) >= 3] # TODO: Consider adding back in? but we remove stopwords later anyway
    
    #Check to see if largest page
    if(len(tokens) > longest_page[1]):
        logging.debug("Overrode longest page of " + str(longest_page[1]) + " tokens")
        longest_page = (current_url, len(tokens))

    logging.debug("Num of tokens: " + str(len(tokens)))
    return tokens

def extract_next_links(url, resp):
    logging.debug("Enter method extract_next_links()")
    return_urls = []

    response_text = resp.raw_response.content
    soup_text = BeautifulSoup(response_text, 'html.parser')

    # logging.debug("Article Title:" + soup_text.title)

    # IDEALLY: no link will be traversed twice 
    base = get_url_base()
    if base in subdomain_counter: 
        subdomain_counter[base] = subdomain_counter[base] + 1
        logging.debug("--subdomain counter incremented-- " + str(base) + " : " + str(subdomain_counter[base]))
    else:
        subdomain_counter[base] = 1
        logging.debug("--subdomain counter added-- " + str(base) + " : " + str(subdomain_counter[base]))

    ### TOKENIZE THE TEXT ###
    raw_tokens = tokenize(soup_text.get_text())
    tokens = [token for token in raw_tokens if not token in stopwords] 

    ### QUALITY/ETC. CHECKING:
    if is_dead_url(resp) or is_large(response_text, response_tokens) or is_similar(response_tokens):
        # return an empty list of links
        logging.debug("URL did not pass preprocessing step. Return [] ")
        return []
    
    ### POST-QUALITY CHECKS
    # Add tokens to masterlists 
    add_tokens_globally(tokens)
    
    print(return_urls, len(return_urls))

    return_urls = [a["href"] for a in soup_text.find_all('a', href=True)]
    logging.debug("RETURN_URLS: " + str(return_urls))
        
    return return_urls

def complete_logs():
    ### UNIQUE PAGES
    logging.info("NUMBER OF UNIQUE PAGES: " + str(len(all_url_bases)))

    ### LONGEST PAGE
    logging.info("LONGEST PAGE FOUND: url = " + str(longest_page[0]) + " , num of tokens = " + str(longest_page[1]))
    
    ### TOP 50 most common words
    sorted_tokens = {k: v for k, v in sorted(token_frequency_masterlist.items(), key=(lambda x:x[1]), reverse=True)}
    top_tokens = dict()
    index = 0
    for key, value in sorted_tokens():
        if(index > 50):
            break
        else:
            top_tokens[key] = value
    
    logging.info("TOP 50 TOKENS: " + str(top_tokens))
    
    ### HOW MANY SUBDOMAINS in the ics.uci.edu domain:
    special_subdomains = dict()
    for key in subdomain_counter.keys():
        if ".ics.uci.edu" in key:
            logging.debug(key + " is in ics.uci.edu subdomain")
            special_subdomains[key] = subdomain_counter[key]
        else:
            logging.debug("Not in ics.uci.edu subdomain.")

    logging.info("NUMBER OF SUBDOMAINS OF ics.uci.edu: " + str(len(special_subdomains)))
    logging.info(special_subdomains)



def is_valid(url): # need to change
    logging.debug("Enter method is_valid()")
    # scenarios:
    # (leave) https://www.ics.uci.edu/hello-world (good!)
    # (https needed) www.ics.uci.edu/hello-world (needs https)
    # (leave) https://ics.uci.edu/hello-world (base is partially right, needs www)
    # (https needed) ics.uci.edu/hello-world (missing full base and https)
    # (https and base needed) /hello-world (missing base and https)
    url_base = get_url_base()
    logging.debug("Input URL: "+ str(url))
    try:
        parsed = urlparse(url)

        logging.debug("Parsed scheme :"+ str(parsed.scheme))
        logging.debug("Parsed netloc: "+ str(parsed.netloc))
        logging.debug("Parsed path: "+ str(parsed.path))
        
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
                logging.debug("is_valid is FALSE; url : " + url)
                return {
                    "is_valid": False,
                    "new_url": url
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
            logging.debug("is_valid is FALSE; url : " + url)
            return {
                "is_valid": False,
                "new_url": url
            }
        
        # add check to match with allowed URLs -- need to test
        if re.match(r"^.*((.ics.uci.edu|.cs.uci.edu|.informatics.uci.edu|.stat.uci.edu)\/).*",url) or \
            re.match(r"^.*(today.uci.edu/department/information_computer_sciences\/).*",url):
            logging.debug("is_valid is TRUE; url : " + url)
            return {
                "is_valid": True,
                "new_url": url
            }

        logging.debug("is_valid is FALSE; url : " + url)
        return {
            "is_valid": False,
            "new_url": url
        }


    except TypeError:
        print ("TypeError for ", parsed)
        raise