import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.DEBUG, filename="run.log", filemode='w', format='%(name)s - %(levelname)s - %(message)s')

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

# Full global list of full urls we've been to
all_urls_traversed = []
# CREATE A GLOBAL SET OF URLS PARSED THROUGH W/O FRAGMENT
all_url_bases = []
# List of bad links
all_bad_links = []

# DICT OF SUBDOMAINS AND NUMBER OF UNIQUE PAGES IN EACH SUBDOMAIN, ALPHABETICALLY
subdomains = dict()
# MASTERLIST OF TOKENS (TODO: Too much space taken up? Perhaps save top 50 only?)
token_masterlist = [] # does not contain stopwords, does contain duplicates
token_frequency_masterlist = dict() # No duplicates

########################

def scraper(url, resp):
    #POSSIBLE TODO IMPLEMENTATION: 
        #One final failsafe? Cap the number of links that can be traversed at ~25,000?

    print("Response URL:" + str(resp.url))

    # IF the url is a new one/ has not been traversed already
    if url not in all_urls_traversed { 
        # print("Response content:" + str(resp.raw_response.content))
        # print("Response html: " + str(resp.content))
        links = extract_next_links(url, resp)

        lst_of_valid_links = []
        for l in links:
            result = is_valid(l)
            if result["is_valid"] == True:
                lst_of_valid_links.append(result["new_url"])

        # return [link for link in links if is_valid(link)]
        return lst_of_valid_links

    } else { # The URL is one we've seen before
        print("URL ALREADY PARSED: " + str(url))
        return [] #TODO: Unsure if this is what we should be returning?
    }
    

def is_large(response_text): # We need to find a measure by which to decide if large/irrelevant
    #hello 
    return False

def is_dead_url(response_text): # 200 response = continue; 404 = add to bad list
    #hello 
    #all_bad_links
    for url in response_text:
        try:
            request = requests.get(url)
            if request.status_code == 200:
                # does something
        except:
            all_bad_links.append(url)
            
    return False

def is_similar(response_tokens):
    # create a unique token-list by getting keys of token_frequency_masterlist
    all_tokens = list(token_frequency_masterlist.keys())
    temp1 = []; 
    temp2 = [];

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
        return False
    else:
        return True

def add_tokens_globally(tokens):
    # Returns void
    for token in tokens:
        if token not in token_frequency_masterlist.keys():
            token_masterlist.append(token)
            token_frequency_masterlist[token] = 1
        else :
            token_frequency_masterlist[token] =  token_frequency_masterlist[token]+1

# TODO: might use for quality checking(?)
# def _is_english(txt, text_file_path):
#     # check if txt is english by seeing of txt can be encoded into the standard char encoding for text
#     try:
#         txt.encode("ascii")
#     except UnicodeEncodeError:
#         print("ERROR ({}): the text you are reading is not english".format(text_file_path))
#         return False

#     return True

def tokenize(full_text):
    # inital clean: lowercase everything
    txt = full_text.lower()

    # remove punctuation, control chars
    txt = re.sub(r'[{}]|\n|\t'.format(string.punctuation), " ", txt)

    # create tokens list, remove len(word) < 3
    tokens = re.findall(r"[\w]+", txt)
    
    #tokens = [t for t in word_tokens if len(t) >= 3] # TODO: Consider adding back in? but we remove stopwords later anyway
    return tokens

def extract_next_links(url, resp):
    # Implementation required.
    return_urls = []

    response_text = resp.raw_response.content
    soup_text = BeautifulSoup(response_text. 'html.parser')

    print(soup_text.p)
    print(soup_text.get_text())

    ### TOKENIZE THE TEXT ###
    raw_tokens = tokenize(soup_text.get_text())
    tokens = [token for token in raw_tokens if not token in stopwords] 

    ### QUALITY/ETC. CHECKING:
    if is_dead_url(response_text) or is_large(response_text) or is_similar(response_tokens) :
        # return an empty list of links
        return []
    
    ### PASSES QUALITY-CHECK:
    
    # Add tokens to masterlists 
    add_tokens_globally(tokens)
    
    print(return_urls, len(return_urls))

    return_urls = [a["href"] for a in soup_text.find_all('a', href=True)]
    
    return return_urls # return_urls

    # Functionality to implement: 
    # How many unique pages did we find, discard the fragment
    # What is the longest page in number of words #ritika
    # What are the 50 most common words in all the pages - ignore stopwords #ritika

    # Go through web page content -> tokenize for words, etc. 
    # if you find a URL, check is_valid(url), if yes, add to list -- Rithu

    # returns a LIST of URLS 

def complete_logs():
    sorted_tokens = {k: v for k, v in sorted(token_frequency_masterlist.items(), key=(lambda x:x[1]), reverse=True)}
    logging.info("TOP 50 TOKENS: " + print(sorted_tokens))
    #TODO: Print all final log info for the report

def is_valid(url): # need to change
    try:
        parsed = urlparse(url)
        # normalization step (https://<base>/<whatever else>)
        if parsed.scheme not in set(["http", "https"]):
            # Add base http:// etc. at the start of the string and then try again, if still invalid, return false again
            if parsed.scheme == '':
                return is_valid("http://"+url) # modify for '//www.'
            return {
                "is_valid": False,
                "new_url": url
            }
        
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
            return {
                "is_valid": False,
                "new_url": url
            }
            
        # add check to match with allowed URLs -- need to test
        if re.match(r"^.*((.ics.uci.edu|.cs.uci.edu|.informatics.uci.edu|.stat.uci.edu)\/).*") or \
            re.match(r"^(today.uci.edu/department/information_computer_sciences/\/).*"):
            return {
                "is_valid": True,
                "new_url": url
            }
        return {
            "is_valid": False,
            "new_url": url
        }


    except TypeError:
        print ("TypeError for ", parsed)
        raise