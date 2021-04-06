#################################
##### Name: Cameron Milne
##### Uniqname: ccmilne
#################################

from requests_oauthlib import OAuth1
from bs4 import BeautifulSoup
import requests
import json
import time
import operator
import secrets # file that contains your API key

CACHE_FILENAME = 'cache_nps.json'
MAPQUEST_BASE_URL = 'http://www.mapquestapi.com/search/v2/radius'
CACHE_DICT = {}

client_key = secrets.API_KEY

oauth = OAuth1(client_key)

def test_oauth():
    ''' Helper function that returns an HTTP 200 OK response code and a 
    representation of the requesting user if authentication was 
    successful; returns a 401 status code and an error message if 
    not. Only use this method to test if supplied user credentials are 
    valid. Not used to achieve the goal of this assignment.'''

    MAPQUEST_BASE_URL = 'http://www.mapquestapi.com/search/v2/radius'
    auth = OAuth1(client_key, client_secret)
    authentication_state = requests.get(MAPQUEST_BASE_URL, auth=auth).json #replace json with .status_code to print out the status code
    return authentication_state

#Organizes National Site data and produces string
class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category='No Category', name='No Name', address='No Address', zipcode='No Zipcode', phone='No Phone'):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        return f"{self.name} ({self.category}): {self.address} {self.zipcode}"

#Making request to the Web API
def make_request(baseurl, params):
    '''Make a request to the Web API using the baseurl and params

    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dictionary
        A dictionary of param:value pairs

    Returns
    -------
    dict
        the data returned from making the request in the form of 
        a dictionary
    '''
    response = requests.get(baseurl, params=params)
    return response.json()

#Caching
def open_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary

    Parameters
    ----------
    None

    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict):
    ''' Saves the current state of the cache to disk

    Parameters
    ----------
    cache_dict: dict
        The dictionary to save

    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close()

#Question 1
def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''

    URL = 'https://www.nps.gov/index.htm'
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')

    search_div = soup.find(class_ ='dropdown-menu SearchBar-keywordSearch')
    lis = search_div.find_all(['li'])

    states_dictionary = {}
    url_for_concat = 'https://www.nps.gov'

    for state in lis:
        state_properties = state.find_all('a')
        for state_property in state_properties:
            #print(state_property.text)
            #print(state_property.attrs['href'])
            states_dictionary[state_property.text.lower()] = url_for_concat + state_property.attrs['href']

    return states_dictionary

#Question 2
def get_site_instance(site_url):
    '''Make an instances from a national site URL.

    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov

    Returns
    -------
    instance
        a national site instance
    '''
    #example of site_url: https://www.nps.gov/isro/index.htm
    page = requests.get(site_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    header = soup.find(class_='Hero-titleContainer clearfix')
    footer = soup.find(class_='vcard')

    #Category
    try:
        if header.find(class_='Hero-designation').text == '':
            category = 'No Category'
        elif header.find(class_='Hero-designation') != '':
            category = header.find(class_ ='Hero-designation').text.strip()
    except:
        category = 'No Category'

    #Name
    try:
        if header.find(class_ ='Hero-title').text == '':
            name = 'No Name'
        elif header.find(class_ ='Hero-title') != '':
            name = header.find(class_ ='Hero-title').text.strip()
    except:
        name = 'No Name'

    #Address
    try:
        if footer.find(itemprop='addressLocality').text == '':
            address = 'No Address'
        elif footer.find(itemprop='addressLocality') != '':
            address = footer.find(itemprop='addressLocality').text + ', ' + footer.find(itemprop='addressRegion').text
    except:
        address = 'No Address'

    #Phone
    try:
        if footer.find(class_ ='tel').text == '':
            phone = 'No Phone'
        elif footer.find(class_ ='tel') != '':
            phone = footer.find(class_ ='tel').text.strip()
    except:
        phone = 'No Phone'

    #Zipcode
    try:
        if footer.find(class_ ='postal-code'):
            zipcode = footer.find(class_ ='postal-code').string.strip()
        elif footer.find(class_ ='postal-code') == None:
            zipcode = footer.find(itemprop ='postalCode').string.strip()
    except:
        zipcode = "No Zipcode"

    site_instance = NationalSite(category=category, name=name, address=address, zipcode=zipcode, phone=phone)

    return site_instance

#Question 3
def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    #example of site_url: https://www.nps.gov/state/az/index.htm
    page = requests.get(state_url)
    soup = BeautifulSoup(page.content, 'html.parser')

    search_ul = soup.find(id="list_parks").find_all('h3')

    state_sites = []
    baseurl = 'https://www.nps.gov'
    index_portion = 'index.htm'

    for name in search_ul:
        anchors = name.find('a')
        anchors_href = anchors.get('href')
        temp_url = baseurl + anchors_href + index_portion
        state_sites.append(get_site_instance(temp_url))

    return state_sites

#Checks for cache before making new request
def make_request_with_cache(baseurl):
    '''Check the cache for a saved result for this baseurl+params:values
    combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.

    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    hashtag: string
        The hashtag to search for
    count: integer
        The number of results you request from Twitter

    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
    CACHE_DICT = open_cache() 

    if baseurl in CACHE_DICT.keys():
        print(f"fetching cached data")
        return CACHE_DICT[baseurl]
    else:
        print(f"making new request")
        CACHE_DICT[baseurl] = requests.get(baseurl)
        save_cache(CACHE_DICT)
        return CACHE_DICT[baseurl]

#Parsing the dictionaries
def parse_dictionary(dictionary_item):
    '''Takes in a dictionary result from the API request and parses its contents
    in order to return the nearby sites of a national park as a list.

    Parameters
    ----------
    dictionary_item: dictionary
        Dictionary of the get_nearby_places object

    Returns
    -------
    list
        the results of the dictionary search results as NationalSite instances
        in a list format
    '''
    API_LIST = []
    searchResults = dictionary_item['searchResults']

    for search_result in searchResults:
        #check to see if results are there
        temp_name = search_result['name']

        if search_result['fields']['group_sic_code_name_ext']:
            temp_category = search_result['fields']['group_sic_code_name_ext']
        else:
            temp_category = 'No Category'

        if search_result['fields']['address']:
            temp_address = search_result['fields']['address']
        else:
            temp_address = 'No Address'

        if search_result['fields']['postal_code']:
            temp_zipcode = search_result['fields']['postal_code']
        else:
            temp_zipcode = 'No Zipcode'

        site_info_instance = NationalSite(category=temp_category, name=temp_name, address=temp_address, zipcode=temp_zipcode)

        API_LIST.append(site_info_instance.info())

    return API_LIST

#Question 4
def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.

    Parameters
    ----------
    site_object: object
        an instance of a national site

    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    unique_key = site_object.zipcode

    temporary_params = {'key': client_key,
                        'origin': unique_key,
                        'radius': 10,
                        'maxMatches': 10,
                        'ambiguities': 'ignore',
                        'outFormat': 'json',}

    if unique_key in CACHE_DICT.keys():
        print("Using Cache")
        return CACHE_DICT[unique_key]

    else:
        print("Fetching")
        CACHE_DICT[unique_key] = make_request(MAPQUEST_BASE_URL, params=temporary_params)
        save_cache(CACHE_DICT)
        return CACHE_DICT[unique_key]


if __name__ == "__main__":


    state_site_list = []

    #User input section
    while True:
        # state_site_list = []
        state_urls = build_state_url_dict()

        entry = input(f'\nEnter a state name (e.g. Michigan, michigan) or "exit": ')
        user_input = entry.lower().strip()

        if user_input == 'exit':
            print(f'\nBye!')
            quit()

        elif user_input in state_urls.keys():
            state_url = state_urls[user_input]
            print('-' * 35)
            print(f"List of national sites in {entry}")
            print('-' * 35)

            sites_for_state = get_sites_for_state(state_url)

            for i, site in enumerate(sites_for_state, start=1):
                state_site_list.append(site.info()) #in order to retrieve the site details if requested
                print(f'[{i}] {site.info()}')
                pass

            while True:
                entry2 = input(f'\nChoose the number for detail search or "exit" or "back": ')
                string_option = entry2.lower().strip()
                if string_option == 'exit':
                    print(f'\nBye!')
                    quit()

                elif string_option == 'back':
                    break

                elif entry2.isdigit():
                    detail_search = int(entry2)
                    location_of_choice = sites_for_state[detail_search - 1]
                    nearby_sites = get_nearby_places(location_of_choice)
                    nearby_sites_neat = parse_dictionary(nearby_sites)

                    print('-' * 35)
                    print(f"Places near {location_of_choice.name}")
                    print('-' * 35)

                    for i, site in enumerate(nearby_sites_neat, start=1):
                        print(f'[{i}] {site}')

                else:
                    print(f'\nError: Choose the number for detail search or "exit" or "back": ')

        else:
            print(f"\n[Error] Enter proper state name")

