import os, requests, json, string, datetime
from os.path import join, dirname
from flask import Flask, request, render_template, redirect, url_for, session
from flask.sessions import SessionInterface
from beaker.middleware import SessionMiddleware
from watson_developer_cloud import AuthorizationV1 as Authorization
from watson_developer_cloud import SpeechToTextV1 as SpeechToText
from watson_developer_cloud import TextToSpeechV1 as TextToSpeech
import application
from random import randint
# ------------------------------------------------
# GLOBAL VARIABLES -------------------------------
# ------------------------------------------------
#####
# Hardcoded env variables defaults for testing
#####

# Bill Esposito added 7/27
SECURITY = 'ON'
# AUTHENTICATED = False

PERSONA_NAME = 'Partner'
PERSONA_IMAGE = ''
PERSONA_STYLE = 'Partner'
WATSON_IMAGE = ''
WATSON_STYLE = 'Watson'
#CHAT_TEMPLATE = 'designer-index.html'
CHAT_TEMPLATE = 'index.html'
QUESTION_INPUT = 'response-input'
SEARCH_TYPE_INPUT = 'search-type'
SEARCH_VALUE_INPUT = 'search-values'
CURSOR_INPUT = 'cursor-input'
# DIALOG_ID = '0fcd2515-2afe-4532-91ac-ea3e58cbb7a3'
#DIALOG_ID = '2bb8ec59-8d7f-4bd5-aa02-00b100073d50'
DIALOG_ID = 'a948ccb4-0334-4375-94e6-6c9c894e1e5f'
# DIALOG_USERNAME = 'a69f9fa0-2d36-42ad-a675-80c6c3dcb988'
# DIALOG_PASSWORD = '7CJUxjzYwK0Z'
DIALOG_USERNAME = 'a17ff5a8-356b-48af-9232-306c7d4eb831'
DIALOG_PASSWORD = '18CpuHOYnQZx'


TTS_USERNAME = 'f15e4f46-254e-4a34-9e5d-dddb3474ba26'
TTS_PASSWORD = 'lEgfLZl9MM9R'
STT_USERNAME = '463932cc-63e8-4936-b29f-9f8a2639164d'
STT_PASSWORD = 'q66IJE7lJmgs'
TOA_USERNAME = '5ac66713-5a37-445b-a763-f9a290ad613e'
TOA_PASSWORD = 'pEpwqyoYGFJx'

#####
# Overwrites by env variables
#####
if 'WATSON_STYLE' in os.environ:
	WATSON_STYLE = os.environ['WATSON_STYLE']
if 'PERSONA_STYLE' in os.environ:
	PERSONA_STYLE = os.environ['PERSONA_STYLE']
if 'CHAT_TEMPLATE' in os.environ:
	CHAT_TEMPLATE = os.environ['CHAT_TEMPLATE']
if 'QUESTION_INPUT' in os.environ:
	QUESTION_INPUT = os.environ['QUESTION_INPUT']
if 'CURSOR_INPUT' in os.environ:
	CURSOR_INPUT = os.environ['CURSOR_INPUT']
if 'DIALOG_ID' in os.environ:
	DIALOG_ID = os.environ['DIALOG_ID']
if 'VCAP_SERVICES' in os.environ:
	if len('VCAP_SERVICES') > 0:
		vcap_services = json.loads(os.environ['VCAP_SERVICES'])
		if 'dialog' in vcap_services.keys():
			dialog = vcap_services['dialog'][0]
			DIALOG_USERNAME = dialog["credentials"]["username"]
			DIALOG_PASSWORD = dialog["credentials"]["password"]
		if 'speech_to_text' in vcap_services.keys():
			stt = vcap_services['speech_to_text'][0]
			STT_USERNAME = stt["credentials"]["username"]
			STT_PASSWORD = stt["credentials"]["password"]
		if 'text_to_speech' in vcap_services.keys():
			tts = vcap_services['text_to_speech'][0]
			TTS_USERNAME = tts["credentials"]["username"]
			TTS_PASSWORD = tts["credentials"]["password"]
		if 'tradeoff_analytics' in vcap_services.keys():
			tts = vcap_services['tradeoff_analytics'][0]
			TOA_USERNAME = tts["credentials"]["username"]
			TOA_PASSWORD = tts["credentials"]["password"]
#####
# Session options
#####
session_opts = {
	'session.type': 'ext:memcached',
	'session.url': 'localhost:11211',
	'session.data_dir': './cache',
	'session.cookie_expires': 'true',
	'session.type': 'file',
	'session.auto': 'true'
}
#####
# Tokens
#####
PRESENT_FORM = '[##FORM##]'
VARS_MSG_FORM = '[##VARS_MSG_FORM##]'
VARS_MSG_HELLO = '[##VARS_MSG_HELLO##]'
MISSING_FIELDS = '[##MISSING_FIELDS##]'
SUCCESS = '[##SUCCESS##]'
BLANK_VLAUE = 'THISVALUEISBLANK'
HELLO_JSON_OBJECT = 'JASON'

PERSONALITY_EXCITEMENT = 'excitement-seeking'
PERSONALITY_DUTIFUL = 'dutiful'
PERSONALITY_ADVENTUROUS = 'adventurous'
PERSONALITY_CALM = 'calm-seeking'
PERSONALITY_DUTIFUL = 'dutiful'
PERSONALITY_PHILOSPHICAL = 'philosophical'
PERSONALITY_HEDONISM = 'hedonism-high'
PERSONALITY_CAREFREE = 'carefree'


# ------------------------------------------------
# CLASSES ----------------------------------------
# ------------------------------------------------
class BeakerSessionInterface(SessionInterface):
	def open_session(self, app, request):
		session = request.environ['beaker.session']
		return session

	def save_session(self, app, session, response):
		session.save()

# ------------------------------------------------
# FUNCTIONS --------------------------------------
# ------------------------------------------------
#####
# in external modules
#####
register_application = application.register_application
get_application_response = application.get_application_response
get_search_response = application.get_search_response
get_body = application.get_body

#####
# local
#####
# Encapsulate BMIX services plus helper funcs ----
def BMIX_get_first_dialog_response_json():
	global DIALOG_ID, DIALOG_USERNAME, DIALOG_PASSWORD
	POST_SUCCESS = 201
	print('----inside')
	response_json = None
	url = 'https://gateway.watsonplatform.net/dialog/api/v1/dialogs/' + DIALOG_ID + '/conversation'
	r = requests.post(url, auth=(DIALOG_USERNAME, DIALOG_PASSWORD))
	if r.status_code == POST_SUCCESS:
		response_json = r.json()
		response_json['response'] = format_dialog_response(response_json['response'])
	return response_json

def BMIX_get_next_dialog_response(client_id, conversation_id, input):
    global DIALOG_ID, DIALOG_USERNAME, DIALOG_PASSWORD
    POST_SUCCESS = 201
    response = ''
    print('----inside ESPO')
    print(input)
    url = 'https://gateway.watsonplatform.net/dialog/api/v1/dialogs/' + DIALOG_ID + '/conversation'
    payload = {'client_id': client_id, 'conversation_id': conversation_id, 'input': input}
    r = requests.post(url, auth=(DIALOG_USERNAME, DIALOG_PASSWORD), params=payload)
    if r.status_code == POST_SUCCESS:
        response = format_dialog_response(r.json()['response'])
    else:
        response = "I'm sorry. I can't process your request at this time. Please try again in a few seconds. <span style='font-size: x-small;'>(" + str(r.status_code) + ")</span>"
#
    #response2 = requests.post("https://gateway.watsonplatform.net/personality-insights/api/v2/profile",
    #auth=("ESWjKdNqlmWF", "37ff7d59-b765-430e-839a-9be30b720c5f"),
    #headers = {"content-type": "text/plain"},
    #data=" I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone hate everyone  I hate everyone  I hate everyone  I hate everyone  I hate everyone " )
    #try:
     #   return json.loads(response.text)
    #except:
    #    raise Exception("Error processing the request, HTTP: %d" % response.status_code)

#   
    return response

def callTwitterandPI(dialog_rsponse):
    print(dialog_rsponse)
# This only works if user type "My handle is..  -- Will fix this
	
    atPosition = dialog_rsponse.find('@')
    sliced = dialog_rsponse[atPosition+1:len(dialog_rsponse)]
	
	#sliced = dialog_rsponse[str.find('@')13:len(dialog_rsponse)]
	
    print(sliced)
    
    try:
        import json
    except ImportError:
        import simplejson as json

    import tweepy

# Variables that contains the user credentials to access Twitter API 
    ACCESS_TOKEN = '29478265-PwD3iF2s5ASyS4PeAJZh4ZaXRfM8hb50eGV69ZKX5'
    ACCESS_SECRET = '9g93dja88xvHzd6x35oSZzdTm81wbxTf8ip4DxaOiCFbh'
    CONSUMER_KEY = 'ypWv1pxaGQ9AOiT9Q35gwmGlP'
    CONSUMER_SECRET = 'rhAeVSx6Pww0qi6rNlJNjWIFzlxvWkPHFnc58td2z7LVVmePDu'


# Variables that contains the user credentials to access Twitter API 
#ACCESS_TOKEN = '92360011-PieTjvukofiPhDoKYTl5jxMi7B3vAvsY8VpxaJulP'
#ACCESS_SECRET = '6DJeg5VgjyeADiy5S8CA4zosF39M64aRLZEA5NYIa1e0f'
#CONSUMER_KEY = 'kgk1RbniI6NBPgznR1q9b8o7Q'
#CONSUMER_SECRET = 'zVpmuCb1p0oT3D2zn5pTyjr59rSc7yyxI9d7p2L8YS9t9SIUfh'


    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

    api = tweepy.API(auth)

    public_tweets = api.home_timeline()

# Get the User object for twitter...
    user = api.get_user(sliced)
# Models contain the data and some helper methods which we can then use:

    print(user.screen_name)
 #   print user.followers_count
    print(user.description)

    classifytext = user.description + '. ' 

 #   for friend in user.friends():
 #       print friend.screen_name

    
    for status in tweepy.Cursor(api.user_timeline,id=user.screen_name).items(100):
  #      print (' for loop' + status.text.encode('cp437', errors='replace'))
  #       print tweet.text.encode('cp437', errors='replace')
        classifytext = classifytext + '. ' + status.text
    
    print("\n\n\n\n\n")

    import requests,json
    response = requests.post("https://gateway.watsonplatform.net/personality-insights/api/v2/profile",
         auth=("37ff7d59-b765-430e-839a-9be30b720c5f", "ESWjKdNqlmWF"),
         headers = {"content-type": "text/plain"},
         data=classifytext.encode("utf8")
         )
         
#    f = open('espoBMW.json','w')
#f.write(response.text)
#    f.write(response.text)
    pi_format = get_PI(response.text)
	
    print ('Print at the end ' + classifytext.encode("utf8"))
# python will convert \n to os.linesep
#    f.close() # you can omit in most cases as the destructor will call it
#    print (response.text)
    return pi_format
	
def BMIX_get_resolution(body):
	global TOA_USERNAME, TOA_PASSWORD
	POST_SUCCESS = 200
	resolution = {}
	url = 'https://gateway.watsonplatform.net/tradeoff-analytics/api/v1/dilemmas/'
	r = requests.post(url, auth=(TOA_USERNAME, TOA_PASSWORD), headers={'content-type': 'application/json', 'accept': 'application/json'}, data=json.dumps(body))
	if r.status_code == POST_SUCCESS:
		resolution = r.json()['resolution']
	return resolution
	
# Chat presentation funcs ------------------------
def create_post(style, icon, text, datetime, name):
	post = {}
	post['style'] = style
	post['icon'] = icon
	post['text'] = text
	post['datetime'] = datetime
	post['name'] = name
	return post

def post_watson_response(response):
	global WATSON_STYLE, WATSON_IMAGE 
	now = datetime.datetime.now()
	post = create_post(WATSON_STYLE, WATSON_IMAGE, response, now.strftime('%Y-%m-%d %H:%M'), 'Watson')
	g('POSTS',[]).append(post)
	return post

def post_user_input(input):
	global PERSONA_STYLE, PERSONA_IMAGE, PERSONA_NAME
	now = datetime.datetime.now()
	post = create_post(PERSONA_STYLE, PERSONA_IMAGE, input, now.strftime('%Y-%m-%d %H:%M'), PERSONA_NAME)
	g('POSTS',[]).append(post)
	return post

def get_chat_response(dialog_response):
	global PRESENT_FORM
	chat_response = dialog_response
	if PRESENT_FORM in dialog_response:
		responses = dialog_response.split(PRESENT_FORM)
		chat_response = responses[0]
	return chat_response
	
# Form presentation funcs ------------------------
def get_form(dialog_response):
	global PRESENT_FORM, BLANK_VLAUE
	form = ''
	if PRESENT_FORM in dialog_response:
		responses = dialog_response.split(PRESENT_FORM)
		form = responses[1]
		form = form.replace(BLANK_VLAUE, '')
	return form

def	set_selected_values(form, option_value):
	option = '<option value="' + option_value + '">' + option_value + '</option>'
	if option_value != None:
		if option_value != '':
			form = form.replace(option, '<option value="' + option_value + '" selected="selected">' + option_value + '</option>')
	return form

# Dialog helper funcs ----------------------------
def format_dialog_response(dialog_responses):
	dialiog_response = ''
	if dialog_responses:
		for dialiog_response_line in dialog_responses:
			if str(dialiog_response_line) != '':
				if len(dialiog_response) > 0:
					dialiog_response = dialiog_response + ' ' + dialiog_response_line
				else:
					dialiog_response = dialiog_response_line
	return dialiog_response

def blank_token_if_empty(str):
	global BLANK_VLAUE
	value = str
	if str is None or str == '':
		value = BLANK_VLAUE
	return value

def format_vars_msg_hello(data):
	global VARS_MSG_HELLO
	msg = ''
	#lpuid = blank_token_if_empty(data.get('LPUID', ''))
	#contact_csn = blank_token_if_empty(data.get('ContactCSN', ''))
	#account_csn = blank_token_if_empty(data.get('AccountCSN', ''))
	#account_name = blank_token_if_empty(data.get('AccountName', ''))
	#contact_id = blank_token_if_empty(data.get('ContactID', ''))
	#account_id = blank_token_if_empty(data.get('AccountID', ''))
	#msg = VARS_MSG_HELLO + ' LPUID: {' + lpuid + '} ContactCSN: {' + contact_csn + '} AccountCSN: {' + account_csn + '} AccountName: {' + account_name + '} ContactID: {' + contact_id + '} AccountID: {' + account_id + '}'
	return msg

def format_vars_msg_form(data):
	global VARS_MSG_FORM
	msg = ''
	#first_name = blank_token_if_empty(data.get('First_Name', ''))
	#last_name = blank_token_if_empty(data.get('Last_Name', ''))
	#email = blank_token_if_empty(data.get('Email', ''))
	#product_name = blank_token_if_empty(data.get('Product_Name', ''))
	#product_year = blank_token_if_empty(data.get('Product_Year', ''))
	#serial = blank_token_if_empty(data.get('Serial', ''))
	#request_code = blank_token_if_empty(data.get('Request_Code', ''))
	#msg = VARS_MSG_FORM + ' First_Name: {' + first_name + '} Last_Name: {' + last_name + '} Email: {' + email + '} ProductName: {' + product_name + '} Product_Year: {' + product_year + '} Serial: {' + serial + '} Request_Code: {' + request_code + '}'
	return msg

# TOA helper functions ---------------------------
def get_model_image(key, options):
	image_url = ''
	for i, option in enumerate(options):
		if option['key'] == key:
			image_url = option['values']['image_url']
			break
	return image_url;

def get_PI(body):
	data = json.loads(body)
	pp_map = dict() 
	big5_data = data["tree"]["children"][0]
	needs_data = data["tree"]["children"][1]
	values_data = data["tree"]["children"][2]
	
	outer_parent = big5_data["children"]
	needs_parent = needs_data["children"]
	
	returnPI = '---BIG Five---<br>'
	returnPI = returnPI + outer_parent[0]["name"] + ' percentage ' + str(outer_parent[0]["percentage"]) + '<br>'

	for parent in outer_parent[0]["children"]:
        # print all parents names and percentages
		print("---Parent---")
		pp_map[parent["name"]] = parent["percentage"]
		returnPI = returnPI + parent["name"] + ' percentage ' + str(parent["percentage"]) + '<br>'
        # print all children names and percentages
		print("---Children---")
		for child in parent["children"]:
			pp_map[child["name"]] = child["percentage"]
			returnPI = returnPI + child["name"] + ' precentage ' + str(child["percentage"]) + '<br>'
	
	returnPI = returnPI + '---Needs---<br>'
	returnPI = returnPI + needs_parent[0]["name"] + ' percentage ' + str(needs_parent[0]["percentage"]) + '<br>'
	pp_map[needs_parent[0]["name"]] = needs_parent[0]["percentage"]
	
	  # print all children names and percentages
	print("---Children---")
	for child in needs_parent[0]["children"]:
		pp_map[child["name"]] = child["percentage"]
		returnPI = returnPI + child["name"] + ' precentage ' + str(child["percentage"]) + '<br>'

   	returnPI = returnPI + '---- TOP 3----<br>'		
	for key in sorted(pp_map, key=pp_map.get, reverse=True)[:3]:
		returnPI = returnPI + key + '--' + str(pp_map[key]) + '<br>'
			
			
			
	return returnPI
		
def get_model(body, personality, power, passengers, budget):
	for index in range(len(body['columns'])):
		if body['columns'][index]['key'] == 'personality':
			preference = [personality]
			#body['columns'][index]['preference'].append(series)
			body['columns'][index]['preference'] = preference
			print('--restricting preference ESPO ')
			print(personality)
			print(body['columns'][index]['preference'])
			print('--end')
		if body['columns'][index]['key'] == 'price':
			if budget == '2':
				body['columns'][index]['is_objective'] = False
			elif  budget == '1':
				body['columns'][index]['is_objective'] = True
				body['columns'][index]['goal'] = 'min'
			elif  budget == '3':
				body['columns'][index]['is_objective'] = True
				body['columns'][index]['goal'] = 'max'
		if body['columns'][index]['key'] == 'horsepower':
			if power == '2':
				body['columns'][index]['is_objective'] = False
			elif  power == '1':
				body['columns'][index]['is_objective'] = True
				body['columns'][index]['goal'] = 'min'
			elif  power == '3':
				body['columns'][index]['is_objective'] = True
				body['columns'][index]['goal'] = 'max'
	options = body['options']
	print('calling Tradeoff')
	resolution = BMIX_get_resolution(body) 
	solutions = resolution['solutions']
	model = {}
	models = []
	for solution in solutions:
		if solution['status'] == 'FRONT':
			model = {}
			model['key'] = solution['solution_ref']
			model['image'] = get_model_image(model['key'], options)
			models.append(model)
	print('--models')
	print(models)
	if len(models) > 0:
		i = randint(0,len(models)-1)
		model = models[i]
		print('--model')
		print(model)
	return model
	
# Session var set and get funcs ------------------
def s(key, value):
	session[key] = value
	return session[key]

def g(key, default_value):
	if not key in session.keys():
		session[key] = default_value
	return session[key]

# ----------------s('AUTHENTICATED', true)--------------------------------
# FLASK ------------------------------------------
app = Flask(__name__)
register_application(app)

@app.route('/')
def Index():
    global CHAT_TEMPLATE, STT_USERNAME, STT_PASSWORD, TTS_USERNAME, TTS_PASSWORD
    if SECURITY == 'ON' and g('AUTHENTICATED',0) != True:
        return redirect(url_for('.Login'))
#	Initialize SST & TTS tokens
    stt_token = Authorization(username=STT_USERNAME, password=STT_PASSWORD).get_token(url=SpeechToText.default_url)
    tts_token = Authorization(username=TTS_USERNAME, password=TTS_PASSWORD).get_token(url=TextToSpeech.default_url)
    s('STT_TOKEN', stt_token)
    s('TTS_TOKEN', tts_token)
#	Initialize chat
    s('POSTS',[])
    response = ''
    response_json = BMIX_get_first_dialog_response_json()
    if response_json != None:
        s('DIALOG_CLIENT_ID', response_json['client_id'])
        s('DIALOG_CONVERSATION_ID', response_json['conversation_id'])
        response = response_json['response']
    post_watson_response(response)
    return render_template(CHAT_TEMPLATE, posts=g('POSTS',[]), form='', stt_token=stt_token, tts_token=tts_token)

@app.route('/', methods=['POST'])
def Index_Post():
    global CHAT_TEMPLATE, QUESTION_INPUT, PERSONALITY_ADVENTUROUS, PERSONALITY_CALM, PERSONALITY_CAREFREE, PERSONALITY_DUTIFUL, PERSONALITY_EXCITEMENT, PERSONALITY_HEDONISM, PERSONALITY_PHILOSPHICAL
    if SECURITY == 'ON' and g('AUTHENTICATED',0) != True:
        return redirect(url_for('.Login'))
    question = request.form[QUESTION_INPUT]
#	Display original question
    post_user_input(question)
#	Reset display
    application_response = ''
    form = ''
#	Orchestrate services
    if len(question) == 0:
        application_response = "C'mon, you have to say something!"
    else:
        dialog_response = BMIX_get_next_dialog_response(g('DIALOG_CLIENT_ID', 0), g('DIALOG_CONVERSATION_ID', 0), question)
 
# Esposito Call Twitter API and PI.  Probably need a more reliable test here for this
 
        if (question.startswith('My handle is') or '@' in question):
            piResponse = callTwitterandPI(question)
 #           for doc in piResponse['tree']:
 #               print(doc[0]['name'])
            post_watson_response(piResponse)
        
        application_response = get_application_response(get_chat_response(dialog_response))
        form = get_application_response(get_form(dialog_response))
        if application_response == PERSONALITY_ADVENTUROUS or application_response == PERSONALITY_CALM or application_response == PERSONALITY_CAREFREE or application_response == PERSONALITY_DUTIFUL or application_response == PERSONALITY_EXCITEMENT or application_response == PERSONALITY_HEDONISM or application_response == PERSONALITY_PHILOSPHICAL:
            s('CUSTOMER_PROFILE', application_response)
            dialog_response = BMIX_get_next_dialog_response(g('DIALOG_CLIENT_ID', 0), g('DIALOG_CONVERSATION_ID', 0), application_response)
			#back_channel = BMIX_get_next_dialog_response(g('DIALOG_CLIENT_ID', 0), g('DIALOG_CONVERSATION_ID', 0), '[##INSIGHT##] xxx ' + application_response)
			#print('--back_channel')
			#print(back_channel)
            print('IS IT GOING IN HERE')
            application_response = get_application_response(get_chat_response(dialog_response))
            form = get_application_response(get_form(dialog_response))
			
#	Display application_response
    post_watson_response(application_response)
    return render_template(CHAT_TEMPLATE, posts=g('POSTS',[]), form=form, stt_token=g('STT_TOKEN', ''), tts_token=g('TTS_TOKEN', ''))

@app.route('/login', methods=['GET', 'POST'])
def Login():
    global AUTHENTICATED
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'bmwadmin' or request.form['password'] != 'bmw_admin$':
            error = 'Invalid Credentials. Please try again.'
        else:
            s('AUTHENTICATED',True)
            return redirect(url_for('.Index'))
    return render_template('login.html', error=error)

@app.route('/hello/', methods=['POST'])
def Index_Hello_Post():
	response_json = BMIX_get_first_dialog_response_json()
	if response_json != None:
		g('DIALOG_CLIENT_ID', response_json['client_id'])
		g('DIALOG_CONVERSATION_ID', response_json['conversation_id'])
#	Retrieve data object from payload
	data = json.loads(request.data)[HELLO_JSON_OBJECT]
#	set vars from data payload
#	dialog_response = BMIX_get_next_dialog_response(g('DIALOG_CLIENT_ID',0), g('DIALOG_CONVERSATION_ID',0), format_vars_msg_hello(data))
	return redirect(url_for('Index'))

	#@app.route('/helloPI/', methods=['POST'])
#def Index_Hello_PI():
#At what point would the performance be a problem with the additional series and models.  How about training set data limits and training ?
#  
#  "url": "https://gateway.watsonplatform.net/personality-insights/api",
#   "password": "ESWjKdNqlmWF",
 #   "username": "37ff7d59-b765-430e-839a-9be30b720c5f"
	
#	response_json_PI = BMIX_test_PI_CALL()
	
#	if response_json != None:
	#	g('DIALOG_CLIENT_ID', response_json['client_id'])
	#	g('DIALOG_CONVERSATION_ID', response_json['conversation_id'])
#	Retrieve data object from payload
	#data = json.loads(request.data)[HELLO_JSON_OBJECT]
#	set vars from data payload
#	dialog_response = BMIX_get_next_dialog_response(g('DIALOG_CLIENT_ID',0), g('DIALOG_CONVERSATION_ID',0), format_vars_msg_hello(data))
	#return redirect(url_for('Index'))
	
@app.route('/page', methods=['POST'])
def Page_Post():
	global CHAT_TEMPLATE, CURSOR_INPUT, SEARCH_TYPE_INPUT
	form = ''
	tips = ''
#	Set vars from hidden form fields
	action = request.form[CURSOR_INPUT]
	search_type = request.form[SEARCH_TYPE_INPUT]
	possible_actions = {'Accept': 0, 'Next': 1, 'Prev': -1, 'Explore': 0}
	shift = possible_actions[action]
	if shift != 0:
		application_response = get_search_response(search_type, shift)
	elif action == 'Accept':
		application_response = 'Thank you for helping to make Watson smarter! What else can I help you with?'
#	Display application_response
	post_watson_response(application_response)
	return render_template(CHAT_TEMPLATE, posts=g('POSTS',[]), form='', stt_token=g('STT_TOKEN', ''), tts_token=g('TTS_TOKEN', ''))

@app.route('/decide', methods=['POST'])
def Index_Decide_Post():
	global CHAT_TEMPLATE, PERSONALITY_ADVENTUROUS
#	Reset display
	application_response = ''
	form = ''
#	Get body
	body = get_body()
#	Get answers from form
	power = request.form.get('power', '')
	passengers = request.form.get('passengers', '')
	budget = request.form.get('budget', '')
#	Get series from session
	series = g('CUSTOMER_PROFILE', PERSONALITY_ADVENTUROUS)
	print('--series')
	print(series)
#	Get model
	model = get_model(body, series, power, passengers, budget)
	print('--model')
	print(model)
#	Display model and image
	application_response = "There's no one quite like you, and I can see you enjoying yourself behind the wheel of a <b>" + model['key'] + "</b>."
	form = "<h1>Your best BM'er</h1><h3>The BMW " + model['key'] + "</h3><image src='" + model['image'] + "' alt='" + model['key'] + "' height='129' length='304'>"
	
	post_watson_response(application_response)
	return render_template(CHAT_TEMPLATE, posts=g('POSTS',[]), form=form)
	
port = os.getenv('PORT', '5000')
if __name__ == "__main__":
	app.wsgi_app = SessionMiddleware(app.wsgi_app, session_opts)
	app.session_interface = BeakerSessionInterface()
	app.run(host='0.0.0.0', port=int(port))