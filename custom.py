import os, requests, json, string, datetime, csv
from os.path import join, dirname
from flask import Flask, request, render_template, redirect, url_for, session
from flask.sessions import SessionInterface
from beaker.middleware import SessionMiddleware
from pprint import pprint
import xmltodict
# ------------------------------------------------
# GLOBAL VARIABLES -------------------------------
# ------------------------------------------------
#####
# Hardcoded env variables defaults for testing
#####
#CLASSIFIER_ID = 'cd6374x52-nlc-967'
#CLASSIFIER_USERNAME = '22e377fc-6a7a-4516-8a2e-574161aa4670'
#CLASSIFIER_PASSWORD = '5sY4nrSCuSaL'

CLASSIFIER_ID = '17aa09x78-nlc-8'
CLASSIFIER_USERNAME = 'f5f18277-dcda-401e-9bb1-30491157c2da'
CLASSIFIER_PASSWORD = 'M8zbBJWZ0HhQ'

#####
# Tokens
#####
CLASSIFY_UTTERANCE = '[##CLASSIFY##]'

# ------------------------------------------------
# FUNCTIONS --------------------------------------
# Encapsulate BMIX services plus helper funcs ----
def BMIX_classify(utterance, threshold):
	global CLASSIFIER_ID, CLASSIFIER_USERNAME, CLASSIFIER_PASSWORD
	POST_SUCCESS = 200
	
	class_name = ''
	url = 'https://gateway.watsonplatform.net/natural-language-classifier/api/v1/classifiers/' + CLASSIFIER_ID + '/classify'
	r = requests.post(url, auth=(CLASSIFIER_USERNAME, CLASSIFIER_PASSWORD), headers={'content-type': 'application/json'}, data=json.dumps({'text': utterance}))

	#if r.status_code == POST_SUCCESS:
	#	classes = r.json()['classes']
	#	if len(classes) > 0:
	#		confidence = classes[0]['confidence']
	#		if (confidence > threshold):
	#			class_name = classes[0]['class_name']
	
	#return class_name
	return r
	
# R&R search helper funcs ------------------------
def populate_entity_from_randr_result(doc):
	entity = {}
	entity['id'] = doc['id']
	entity['ShortDescription'] = doc['ShortDescription'][0]
	entity['Text'] = doc['Text'][0]
	return entity

def markup_randr_result(entity):
	return ('<p><b>' + entity['ShortDescription'] + '</b><br><u>Text:</u> ' + entity['Text'] + '<br><u>Document id:</u> ' + entity['id']+ '</p>')
		
def markup_randr_results(search_results, cursor):
	application_response = "I'm unable to find what you're looking for. Can you rephrase the question or ask something else?"
	if (len(search_results) > 0):
		entity = search_results[cursor]
		application_response = "I've retrieved <b>" + str(len(search_results)) + " routers</b> that may be of interest. You're viewing router number <b>#" + str(cursor + 1) + "</b>"
		application_response = application_response + markup_randr_result(entity)
		application_response = application_response + '<form action="/page" method="POST"><input type="submit" name="cursor-input" value="Next"/> <input type="submit" name="cursor-input" value="Prev"/> <input type="submit" type="submit" name="cursor-input" value="Accept"/> <input type="hidden" name="search-type" value="RANDR"></form>'
	return application_response
	
# WEX search helper funcs ------------------------
def populate_entity_from_wex_result(doc):
	entity = {}
	entity['Url'] = doc['@url']
	entity['FileType'] = doc['@filetypes']
	entity['Snippet'] = ""
	entity['FileName'] = ""
	contents = doc['content']
	for content in contents:
		name = content['@name']
		if name == 'snippet':
			entity['Snippet'] = content['#text']
		if name == 'filename':
			entity['FileName'] = content['#text']
	return entity
		
def markup_wex_results(search_results, cursor):
	application_response = "I'm unable to find what you're looking for. Can you rephrase the question or ask something else?"
	if (len(search_results) > 0):
		entity = search_results[cursor]
		application_response = "I've found the answer to your question in <b>" + str(len(search_results)) + " documents</b> with the most probable answers shown first. You're viewing answer <b>#" + str(cursor + 1) + "</b>"
		url = entity['Url']
		application_response = application_response + '<p style="font-size: small;"><i>' + entity['Snippet'] + '</i> <a href="' + url + '" style="font-size: small;" target="_blank">View document</a></p>'
		application_response = application_response + '<form action="/page" method="POST"><input type="submit" name="cursor-input" value="Next"/> <input type="submit" name="cursor-input" value="Prev"/> <input type="submit" type="submit" name="cursor-input" value="Accept"/> <input type="hidden" name="search-type" value="WEX"></form>'
	return application_response
	
def get_custom_response(application_response):
	#call out for any customer specific logic to 'intercept' a repsonse
	global CLASSIFY_UTTERANCE;
	POST_SUCCESS = 200
	
	classify_list = []
	custom_response = application_response
	#randr search requested
	if (application_response.startswith(CLASSIFY_UTTERANCE)):
		utterance = application_response.replace(CLASSIFY_UTTERANCE, '')
		print('--utterance')
		utterances = utterance.split('|')
		for word in utterances:
				print ('call before')
				r = BMIX_classify(word, 20)
				print(r.status_code)
				if r.status_code == POST_SUCCESS:
					classes = r.json()['classes']
					if len(classes) > 0:
						confidence = classes[0]['confidence']
						class_name = classes[0]['class_name']
						confidence1 = classes[1]['confidence']
						class_name1 = classes[1]['class_name']
					
				#		if (confidence > 20):
						classify_list.append(class_name)
						classify_list.append(confidence)
						classify_list.append('<br>')
				#		if (confidence1 > 20):
						classify_list.append(class_name1)
						classify_list.append(confidence1)
						classify_list.append('<br><br>')
	#		print(class_name)
		custom_response = class_name
	return classify_list