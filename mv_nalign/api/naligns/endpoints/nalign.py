
import logging
from flask import make_response, jsonify
from flask_restplus import Resource, Namespace, Api,marshal
from flask_restplus import fields
from flask import request,Flask
import marshmallow as ma
from mv_nalign.mvschemas.nalign import theNAlignSetFactory,coll as collection_name
from mv_nalign.api.restplus import api
from mv_nalign.mvexception.exception import MVException, ValidationException
import json
import collections
from pymongo import MongoClient
from flask_restplus import Api, Resource, fields
# from mv_nalign.app import app
import flask
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from flask import request
from pymongo import MongoClient
import requests
from mv_nalign import settings
from mv_nalign.api.naligns  import parsers
from mv_nalign.api.naligns.pagination import pagination_arguments
import werkzeug
import threading


log = logging.getLogger(__name__)
ns = Namespace('nalign', description='Music Tool API')


jsbrand = ns.model('Brand',{
	'brand_name': fields.String(description='input as brand name'),
})

jsproject = ns.model('Project',{
	'db_id':fields.String(description='id of the project'),
	'name': fields.String(description='name of the project'),
	'file_url': fields.String(description='url link of the file'),
	# 'file_type': fields.String(description='type of the file'),
	'file_duration': fields.String(description='duration of the file'),
	'file_youtube': fields.String(description='youtube or video'),
	'thumbnail_url':fields.String(description="thumbail nail for main file url"),
	'link_source':fields.String(description="video source will be internal or external"),
	# 'brand': fields.String(description='brand name attached to the project'),
	# 'product': fields.String(description='product name attached to the project'),
	'published_at':fields.DateTime(description='published datetime for the file originally at source'),
	'created_at': fields.DateTime(description='created at'),
	'updated_at': fields.DateTime(description='modified at'),
	'description':fields.String(description='describe about the video'),
	# 'image_width':fields.Integer(description="image_width"),
	# 'image_height':fields.Integer(description="image_height"),
	'mono_link' : fields.String(description="mono audio link url")
})

# jsprojrct_output = ns

jsprojectlist=ns.inherit('projectlist',jsproject,{
	'file_status':fields.Raw
	# 'multiple_video_upload_status':fields.Raw,
	# 'multiple_image_upload_status':fields.Raw,
	# 'impacts_status':fields.Raw,
	# 'impacts_count':fields.Integer(description="impacts coumt",default=0),
	# 'file_count':fields.Raw,
	# 'processMsg':fields.Raw
})

jsimpact=ns.model('Impact',{
	'ref_id':fields.String(description='id of the project'),
	'keyword':fields.String(description='keyword for the violations'),
	# 'data':fields.List(fields.Raw(),description='processed detection results',default=[])
	
})

jscaptions=ns.model('caption',{
	'link':fields.String(description='id of the project')
})


jsprojectlistpaginated=ns.model('projectlistpaginated',{
	'data':fields.List(fields.Nested(jsprojectlist)),
	'recordsFiltered':fields.Integer(),
	'recordsTotal':fields.Integer()
})

state=''


# FILTERABLE_FIELDS = ['name', 'nalign']
# TODO: Add 404 for data not found
# TODO: Validation!!!
# TODO: fix updates!!



''' 
	================================================
	Default Service Definitions
	- list
	- create
	================================================
'''

# @ns.route('/musictool_project/<string:db_id>')
# class ProjectServiceDetail(Resource):

# 	@ns.marshal_with(jsproject,skip_none=True)
# 	def get(self,db_id):

# 		""" This function defines to get the particular project details """
		
		
# 		resp=theNAlignSetFactory.get_by_id(db_id)
# 		return resp

@ns.route('/musictool_project')
class ProjectService(Resource):
	@ns.marshal_with(jsprojectlist,skip_none=True)
	@ns.expect(jsproject)
	def post(self):

		""" This function defines to create the project """
		
		payload = api.payload
		resp=theNAlignSetFactory.create_project(payload)
		print("im resp project",resp)
		return resp

	@ns.expect(pagination_arguments)
	@ns.marshal_with(jsprojectlistpaginated)
	def get(self):
		""" This function defines to list the project """
		
		args = pagination_arguments.parse_args(request)
		page = args.get('page')
		per_page = args.get('per_page')
		column = args.get('sort_field')
		order = args.get('order')
		partial=args.get('search_key')
		resp=theNAlignSetFactory.get_paginated_project_results(partial,column,order,page,per_page)
		
		return resp

@ns.route('/authorize')
class Authorize(Resource):

	""" This defines authorize the Oauth in google youtube data api """

	def get(self):
	# Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.

		flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
				settings.CLIENT_SECRETS_FILE, scopes=settings.SCOPES)

		# The URI created here must exactly match one of the authorized redirect URIs
		# for the OAuth 2.0 client, which you configured in the API Console. If this
		# value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
		# error.
		flow.redirect_uri = flask.url_for('api.nalign_o_auth2_call_back', _external=True)
		
		authorization_url, state = flow.authorization_url(
				# Enable offline access so that you can refresh an access token without
				# re-prompting the user for permission. Recommended for web server apps.
				access_type='offline',
				# Enable incremental authorization. Recommended as a best practice.
				include_granted_scopes='true')  
					  # Store the state so the callback can verify the auth server response.
		
		print(authorization_url)
		data={}
		if authorization_url:
			data["status"]="Success"
			data["message"]="Please visit this url to allow user access permissions "+authorization_url

		return data

@ns.route('/oauth2callback',doc = False)
class OAuth2CallBack(Resource):

	def get(self):
		# Specify the state when creating the flow in the callback so that it can
		# verified in the authorization server response.
		#TODO state has been need to store somewhere
		global state
		state = str(state)
		flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
				settings.CLIENT_SECRETS_FILE, scopes=settings.SCOPES, state=state)
		flow.redirect_uri = flask.url_for('api.nalign_o_auth2_call_back', _external=True)
		# print("oerking ",flow.redirect_uri)
		# Use the authorization server's response to fetch the OAuth 2.0 tokens.
		authorization_response = flask.request.url
		print(authorization_response)
		flow.fetch_token(authorization_response=authorization_response)

		# Store credentials in the session.
		# ACTION ITEM: In a production app, you likely want to save these
		#              credentials in a persistent database instead.
		credentials = flow.credentials
	
		#add credentials to data base
		cred_obj=collection_name.insert(credentials_to_dict(credentials))  
   
		
		return credentials_to_dict(credentials)


@ns.route('/revoke',doc=False)
class Revoke(Resource):
	def get(self):
		credentials = theNAlignSetFactory.get_credentials()

		revoke = requests.post('https://oauth2.googleapis.com/revoke',
				params={'token': credentials["token"]},
				headers = {'content-type': 'application/x-www-form-urlencoded'})

		status_code = getattr(revoke, 'status_code')
		if status_code == 200:
			return('Credentials successfully revoked.' + print_index_table())
		else:
			return('An error occurred.' + print_index_table())



def credentials_to_dict(credentials):
	return {'token': credentials.token,
					'refresh_token': credentials.refresh_token,
					'token_uri': credentials.token_uri,
					'client_id': credentials.client_id,
					'client_secret': credentials.client_secret,
					'scopes': credentials.scopes}
def print_index_table():
	return ('<table>' +
					'<tr><td><a href="/test">Test an API request</a></td>' +
					'<td>Submit an API request and see a formatted JSON response. ' +
					'    Go through the authorization flow if there are no stored ' +
					'    credentials for the user.</td></tr>' +
					'<tr><td><a href="/authorize">Test the auth flow directly</a></td>' +
					'<td>Go directly to the authorization flow. If there are stored ' +
					'    credentials, you still might not be prompted to reauthorize ' +
					'    the application.</td></tr>' +
					'<tr><td><a href="/revoke">Revoke current credentials</a></td>' +
					'<td>Revoke the access token associated with the current user ' +
					'    session. After revoking credentials, if you go to the test ' +
					'    page, you should see an <code>invalid_grant</code> error.' +
					'</td></tr>' +
					'<tr><td><a href="/clear">Clear Flask session credentials</a></td>' +
					'<td>Clear the access token currently stored in the user session. ' +
					'    After clearing the token, if you <a href="/test">test the ' +
					'    API request</a> again, you should go back to the auth flow.' +
					'</td></tr></table>')




		
		

