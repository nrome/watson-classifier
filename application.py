import os, requests, json, string, datetime, csv
from pprint import pprint
import xmltodict
from flask import session
import custom
# ------------------------------------------------
# GLOBAL VARIABLES -------------------------------
# ------------------------------------------------
#####
# Hardcoded env variables defaults for testing
#####
SOLR_CLUSTER_ID = 'sce5690497_52a7_46f0_b6a2_1341c7c2b63e'
SOLR_COLLECTION_NAME = 'arcbest-collection'
RANKER_ID = '42B250x11-rank-562'
RETRIEVE_AND_RANK_USERNAME = '2b4a1aaa-d177-47fe-8592-15a86104ce4d'
RETRIEVE_AND_RANK_PASSWORD = 'SlEx6tCborZL'
WEX_URL = 'http://10.72.19.40/vivisimo/cgi-bin/velocity.exe?v.function=query-search&v.indent=true&query=[##QUERY_STR##]&sources=LAMR-all-filesystem&v.app=api-rest&authorization-username=admin&authorization-password=admin&v.username=data-explorer-admin&v.password=TH1nk1710'
RANDR_SEARCH_ARGS = 'id,ShortDescription,Text'
#####
# Overwrites by env variables
#####
if 'SOLR_CLUSTER_ID' in os.environ:
	SOLR_CLUSTER_ID = os.environ['SOLR_CLUSTER_ID']
if 'SOLR_COLLECTION_NAME' in os.environ:
	SOLR_COLLECTION_NAME = os.environ['SOLR_COLLECTION_NAME']
if 'RANKER_ID' in os.environ:
	RANKER_ID = os.environ['RANKER_ID']
if 'VCAP_SERVICES' in os.environ:
	if len('VCAP_SERVICES') > 0:
		vcap_services = json.loads(os.environ['VCAP_SERVICES'])
		if 'retrieve_and_rank' in vcap_services.keys():
			retrieve_and_rank = vcap_services['retrieve_and_rank'][0]
			RETRIEVE_AND_RANK_USERNAME = retrieve_and_rank["credentials"]["username"]
			RETRIEVE_AND_RANK_PASSWORD = retrieve_and_rank["credentials"]["password"]
if 'WEX_URL' in os.environ:
	WEX_URL = os.environ['WEX_URL']
if 'RANDR_SEARCH_ARGS' in os.environ:
	RANDR_SEARCH_ARGS = os.environ['RANDR_SEARCH_ARGS']
#####
# Tokens
#####
SEARCH_WITH_RANDR = '[##_SEARCH_WITH_RANDR_##]'
SEARCH_WITH_WEX = '[##SEARCH_WITH_WEX##]'
#####
# Replacement Strings
#####
#PRODUCT_NAME_OPTIONS_DEFAULT = "[option value='Product_Name']...Select...[/option]"
#PRODUCT_NAME_OPTIONS_POPULATED = ''
HASH_VALUES = {}
BODY = {}

# ------------------------------------------------
# FUNCTIONS --------------------------------------
# ------------------------------------------------
#####
# in external modules
#####
populate_entity_from_randr_result = custom.populate_entity_from_randr_result
markup_randr_results = custom.markup_randr_results
populate_entity_from_wex_result = custom.populate_entity_from_wex_result
markup_wex_results = custom.markup_wex_results
get_custom_response = custom.get_custom_response

#####
# local
#####
# Encapsulate BMIX services plus helper funcs ----
def BMIX_retrieve_and_rank(question, fields_str):
	global SOLR_CLUSTER_ID, SOLR_COLLECTION_NAME, RANKER_ID, RETRIEVE_AND_RANK_USERNAME, RETRIEVE_AND_RANK_PASSWORD
	POST_SUCCESS = 200
	SOLR_HIGHLIGHTING = {}
	docs = []
	question = str(question).decode('utf-8', 'ignore')
	url = 'https://gateway.watsonplatform.net/retrieve-and-rank/api/v1/solr_clusters/' + SOLR_CLUSTER_ID + '/solr/' + SOLR_COLLECTION_NAME + '/fcselect?ranker_id=' + RANKER_ID + '&q=' + question + '&wt=json&fl=' + fields_str
	r = requests.get(url, auth=(RETRIEVE_AND_RANK_USERNAME, RETRIEVE_AND_RANK_PASSWORD), headers={'content-type': 'application/json; charset=utf8'})
	if r.status_code == POST_SUCCESS:
		docs = r.json()['response']['docs']
	return docs

def WEX_retrieve(question):
	global WEX_URL;
	POST_SUCCESS = 200
	docs = []
	query_str = format_WEX_query_str(question)
	url = WEX_URL.replace('[##QUERY_STR##]', query_str)
	r = requests.get(url)
	if r.status_code == POST_SUCCESS:
		WEX_response = xmltodict.parse(r.content)
		if len(WEX_response['query-results']) > 3:
			docs = WEX_response['query-results']['list']['document']
			if type(docs) == type(WEX_response):
				doc = docs
				docs = []
				docs.append(doc)
	return docs

# Search helper funcs ----------------------------
def get_search_response(search_type, shift):
	search_response = ''
	if search_type == "RANDR":
		s('RANDR_CURSOR', shift_cursor(g('RANDR_SEARCH_RESULTS', []), g('RANDR_CURSOR', 0), shift))
		search_response = markup_randr_results(g('RANDR_SEARCH_RESULTS', []), g('RANDR_CURSOR', 0))
	elif search_type == "WEX":
		s('WEX_CURSOR', shift_cursor(g('WEX_SEARCH_RESULTS', []), g('WEX_CURSOR', 0), shift))
		search_response = markup_wex_results(g('WEX_SEARCH_RESULTS', []), g('WEX_CURSOR', 0))
	return search_response

def search_randr(question):
	global RANDR_SEARCH_ARGS
	randr_search_results = []
	randr_cursor = 0
	application_response = ''
	docs = BMIX_retrieve_and_rank(question, RANDR_SEARCH_ARGS)
	i = 0
	for doc in docs:
		i += 1
		entity = populate_entity_from_randr_result(doc)
		randr_search_results.append(entity)
	application_response = markup_randr_results(randr_search_results, randr_cursor)
	s('RANDR_SEARCH_RESULTS', randr_search_results)
	s('RANDR_CURSOR', randr_cursor)
	return application_response

def search_wex(question):
	wex_search_results = []
	wex_cursor = 0
	application_response = ''
	docs = WEX_retrieve(question)
	i = 0
	for doc in docs:
		i += 1
		entity = populate_entity_from_wex_result(doc)
		wex_search_results.append(entity)
	application_response = markup_wex_results(wex_search_results, wex_cursor)
	s('WEX_SEARCH_RESULTS', wex_search_results)
	s('WEX_CURSOR', wex_cursor)
	return application_response

def format_WEX_query_str(question):
	query_str = ''
	strip_tokens = '_HOW_A_IS_WHAT_THE_WHICH_WHO_IN_THAT_THAN_THEN_OF_WITH_WITHIN_FOR_MUST_'
	question = question.replace('?','')
	question = question.replace('%','')
	tokens = question.split()
	for token in tokens:
		if strip_tokens.find('_' + token.upper() + '_') == -1:
			query_str = query_str + token + ' '
	return query_str.strip().replace(' ', '%20')
	
def shift_cursor(search_results, cursor, shift):
	cursor = cursor + shift
	if cursor < 0:
		cursor = max(len(search_results)-1,0)
	elif cursor >= len(search_results):
		cursor = 0
	return cursor
	
# Replacement str funcs --------------------------
def load_hash_values(app):
	hash_values = {}
	with app.open_resource('hash.csv') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			hash_values[row['key']] = row['value']
	return hash_values

def build_options(app, file_name, var_name):
	options = ''
	with app.open_resource(file_name) as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			options = options + '[option value="' + row[var_name] + '"]' + row[var_name] + '[/option]'
	return options
	
# TOA helper func --------------------------------
def load_body(app):
	body = {}
	with app.open_resource('body.json', 'r') as myfile:
		json_data = myfile.read()
		body = json.loads(json_data)
	return body

def get_body():
	global BODY
	return BODY

# Session var set and get funcs ------------------
def s(key, value):
	session[key] = value
	return session[key]

def g(key, default_value):
	if not key in session.keys():
		session[key] = default_value
	return session[key]

# Application funcs ------------------------------
def register_application(app):
	#global HASH_VALUES, PRODUCT_NAME_OPTIONS_POPULATED
	global HASH_VALUES, BODY
	#PRODUCT_NAME_OPTIONS_POPULATED = build_options(app, 'Product-Names.csv', 'Product_Name')
	HASH_VALUES = load_hash_values(app)
	BODY = load_body(app)
	return app
	
def get_application_response(dialog_response):
	#global HASH_VALUES, PRODUCT_NAME_OPTIONS_DEFAULT, PRODUCT_NAME_OPTIONS_POPULATED
	global HASH_VALUES
	application_response = dialog_response
	for key in HASH_VALUES:
		value = HASH_VALUES[key]
		application_response = application_response.replace(key, value)
	#randr search requested
	if (dialog_response.startswith(SEARCH_WITH_RANDR)):
		question = dialog_response.replace(SEARCH_WITH_RANDR, '')
		application_response = search_randr(question)
	#wex search requested
	elif (dialog_response.startswith(SEARCH_WITH_WEX)):
		question = dialog_response.replace(SEARCH_WITH_WEX, '')
		application_response = search_wex(question)
	application_response = get_custom_response(application_response)
	application_response = string.replace(application_response, '[', '<')
	application_response = string.replace(application_response, ']', '>')
	return application_response