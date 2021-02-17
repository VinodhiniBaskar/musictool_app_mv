
import logging
from flask import make_response, jsonify
from flask_restplus import Resource, Namespace, Api,marshal
from flask_restplus import fields
from flask import request,Flask
import marshmallow as ma
from mv_musictool.mvschemas.musictool import theNAlignSetFactory,coll as collection_name
from mv_musictool.api.restplus import api
from mv_musictool.mvexception.exception import MVException, ValidationException
import json
import collections
from pymongo import MongoClient
from flask_restplus import Api, Resource, fields
import flask
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from flask import request
from pymongo import MongoClient
import requests
from mv_musictool import settings
from mv_musictool.api.musictool  import parsers
from mv_musictool.api.musictool.pagination import pagination_arguments
import werkzeug
import threading


log = logging.getLogger(__name__)
ns = Namespace('musictool', description='Music Tool API')


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






		
		

