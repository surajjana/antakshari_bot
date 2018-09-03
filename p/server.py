# Configure AWS credentials for BOTO3

from bottle import Bottle, run, route, static_file, request, response, template
from pymongo import MongoClient
from bson.json_util import dumps
from bson.objectid import ObjectId
from string import Template
import json
import pymongo
import requests
import datetime
import time
import boto3
import re


app = Bottle(__name__)

# Add MongoDB URI
client = MongoClient('')

db = client.heroku_x4g5w46w

@app.hook('after_request')
def enable_cors():
	response.headers['Access-Control-Allow-Origin'] = '*'
	response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE, OPTIONS'
	response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'


@app.route('/')
def root():
	return "Antakshari Bot Py Server"

@app.route('/list/<cat>')
def list_cat(cat):

	if(cat != 'undefined'):

		msgData = {"attachment": {"type":"template", "payload":{"template_type":"generic","elements":[]}}}

		cur = db.fb_audio_log.find({"cat": cat}).sort('_id',pymongo.DESCENDING).limit(5)

		data = json.loads(dumps(cur))

		for i in range(0, len(data)):
			cur = db.fb_user_profile.find({"fb_id": data[i]['fb_id']}).limit(1)
			udata = json.loads(dumps(cur))

			if(i == 0):

				temp_res = {"buttons":[{"type":"postback","title":"Listen Now!","payload":"SONG_" + str(i) + "_" + str(data[i]['_id']['$oid'])}],"title": udata[0]['first_name'] + " | Last sung song","subtitle": "Ending with " + data[i]['ending'] + " | " + data[i]['cat'],"image_url": udata[0]['profile_pic']}

			else:

				temp_res = {"buttons":[{"type":"postback","title":"Listen Now!","payload":"SONG_" + str(i) + "_" + str(data[i]['_id']['$oid'])}],"title": udata[0]['first_name'],"subtitle": "Ending with " + data[i]['ending'] + " | " + data[i]['cat'],"image_url": udata[0]['profile_pic']}

			msgData['attachment']['payload']['elements'].append(temp_res)

		return msgData
	else:
		return {'status': 'NA'}

@app.route('/list_listen/<cat>')
def list_listen(cat):

	if(cat != 'undefined'):

		msgData = {"attachment": {"type":"template", "payload":{"template_type":"generic","elements":[]}}}

		cur = db.fb_audio_log.find({"cat": cat}).sort('_id',pymongo.DESCENDING).limit(5)

		data = json.loads(dumps(cur))

		for i in range(0, len(data)):
			cur = db.fb_user_profile.find({"fb_id": data[i]['fb_id']}).limit(1)
			udata = json.loads(dumps(cur))

			if(i == 0):

				temp_res = {"buttons":[{"type":"postback","title":"Listen Now!","payload":"LISTEN_" + str(i) + "_" + str(data[i]['_id']['$oid'])}],"title": udata[0]['first_name'] + " | Last sung song","subtitle": "Ending with " + data[i]['ending'] + " | " + data[i]['cat'],"image_url": udata[0]['profile_pic']}

			else:

				temp_res = {"buttons":[{"type":"postback","title":"Listen Now!","payload":"LISTEN_" + str(i) + "_" + str(data[i]['_id']['$oid'])}],"title": udata[0]['first_name'],"subtitle": "Ending with " + data[i]['ending'] + " | " + data[i]['cat'],"image_url": udata[0]['profile_pic']}

			msgData['attachment']['payload']['elements'].append(temp_res)

		return msgData
	else:
		return {'status': 'NA'}

@app.route('/song_listen/<doc_id>')
def song_liten(doc_id):
	cur = db.fb_audio_log.find({"_id": ObjectId(doc_id)})
	data = json.loads(dumps(cur))

	if(len(data) != 0):
		msgData = {"attachment":{"type":"audio","payload":{"url":data[0]['link']}}}

		return {'data': msgData}
	else:
		return {'status': 'NA'}

@app.route('/song_valid/<song_iter>/<doc_id>')
def song_valid(song_iter, doc_id):
	if(doc_id != 'undefined'):
		if song_iter == '0':
			cur = db.fb_audio_log.find({"_id": ObjectId(doc_id)})
			data = json.loads(dumps(cur))

			cat = data[0]['cat']

			cur = db.fb_audio_log.find({"cat": cat}).sort('_id',pymongo.DESCENDING).limit(2)

			data = json.loads(dumps(cur))

			cur = db.fb_user_profile.find({'fb_id': data[0]['fb_id']}).limit(1)

			udata = json.loads(dumps(cur))

			msgData1 = {  
				"attachment":{
			      "type":"template",
			      "payload":{
			        "template_type":"button",
			        "text":"Does this song sung by " + udata[0]['first_name'] + " start with " + data[1]['ending'],
			        "buttons":[
			          {
					    "type":"postback",
					    "title":"Yes",
					    "payload":"YES_" + str(int(data[0]['fb_id'])) + "_" + data[0]['_id']['$oid']
					  },
					  {
					    "type":"postback",
					    "title":"No",
					    "payload":"NO_" + str(int(data[0]['fb_id'])) + "_" + data[0]['_id']['$oid']
					  }
			        ]
						}
				}
			}

			msgData2 = {"attachment":{"type":"audio","payload":{"url":data[0]['link']}}}


			return {'data': [msgData1, msgData2]}
		else:
			cur = db.fb_audio_log.find({"_id": ObjectId(doc_id)})
			data = json.loads(dumps(cur))

			msgData = {"attachment":{"type":"audio","payload":{"url":data[0]['link']}}}

			return {'data': [msgData]}
	else:
		return {'status': 'NA'}

@app.get('/upload_song/<song_url>')
def upload_song(song_url):
	bucket = 'antakshari-bot'

	fb_audio_url = song_url.replace('|_|', '/')
	fb_audio_url = fb_audio_url.replace('-_', '?')

	#print fb_audio_url

	res = re.search('audioclip-(.+?)oh=', fb_audio_url).group(1)

	s3_audio_filename = 'audioclip-' + res.replace('?','')

	req_for_image = requests.get(fb_audio_url, stream=True)
	file_object_from_req = req_for_image.raw
	req_data = file_object_from_req.read()

	s3 = boto3.resource('s3', region_name='us-east-1')

	s3.Bucket(bucket).put_object(Key=s3_audio_filename, Body=req_data, ContentType='video/mp4')

	return {'status': 'OK', 'url': 'https://s3.amazonaws.com/antakshari-bot/'+s3_audio_filename}