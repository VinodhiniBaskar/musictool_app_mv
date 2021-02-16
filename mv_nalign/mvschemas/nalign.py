# -*- coding: utf-8 -*-
# import tracemalloc
import os
import logging
import uuid
import datetime
import json
import sys
import getopt
import time
import traceback
import random
import re
import timeit
import pickle
import csv
import subprocess
import pafy
from pydub import AudioSegment
from mhyt import yt_download
import cv2
from functools import wraps
from flask import abort
import marshmallow as ma
from urllib.error import ContentTooShortError
from marshmallow import Schema, post_load, validate
from mv_nalign.mvmodels.Projects import Project,ProjectFile,TempFileStorage,NeuroAnalysis,Feedback
from mv_nalign.mvexception.exception import MVException, ValidationException,Test
from mongoengine.queryset.visitor import Q
from flask import Flask,jsonify
from flask_pymongo import PyMongo
from flask_restplus import Api, Resource, fields
from bson import ObjectId
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from mv_nalign import settings
from mv_nalign.api import utils
from pymongo import MongoClient
import threading
from PIL import Image
import boto3
import asyncio
from humanfriendly import format_timespan
from google.cloud import storage
import concurrent.futures as fu

from werkzeug.utils import secure_filename


print (sys.getdefaultencoding())

log = logging.getLogger(__name__)
""" Db initialization """
local=MongoClient()
db=local['test_youtube_db']
coll=db["test_youtube_account"]


WATCH_URL = "https://www.youtube.com/watch?v="
pafy.set_api_key("AIzaSyDb6YEmYxpBPA4il0VmEqxYUC2qovIuJGo")


DEFAULT_UPLOAD_PATH = settings.MEDIA_PATH+"/"
BASE_MEDIA_PATH = "mv_nalign/static/media/"
THUMBNAIL_JPG = "_thumbnail.jpg"

#TODO handle mv exception
class ProjectSchema(Schema):
    db_id = ma.fields.Str(allow_none=True)
    name = ma.fields.Str(required=False)
    description = ma.fields.Str(required=False, default='')
    file_url = ma.fields.Str(required=False, default='')
    file_duration = ma.fields.Str(required=False, default='')
    file_youtube = ma.fields.Str(required=False, default='')
    deleted = ma.fields.Boolean(required=False, default=False)
    # brand = ma.fields.Str(required=False)
    # product = ma.fields.Str(required=False)
    file_status = ma.fields.Dict(required=False)
    # multiple_video_upload_status = ma.fields.Dict(required=False)
    # multiple_image_upload_status = ma.fields.Dict(required=False)
    thumbnail_url = ma.fields.Str(required=False)
    file_type= ma.fields.Str(required=False)
    # impacts_count=ma.fields.Int(required=False)
    published_at = ma.fields.DateTime()
    created_at = ma.fields.DateTime()
    updated_at = ma.fields.DateTime()
    # impacts_status =ma.fields.Dict(required=False)
    captions = ma.fields.Str(required=False)
    # image_width = ma.fields.Int(required=False)
    # image_height= ma.fields.Int(required=False)
    mono_link = ma.fields.Str(required=False)


    @post_load
    def make_project(self, data):
        return Project(**data)

class ProjectFileSchema(Schema):
    db_id = ma.fields.Str(allow_none=True)
    ref_id = ma.fields.Str(required=False)
    image_url = ma.fields.Str(required=False, default='')
    image_timestamp = ma.fields.Str(required=False, default='')
    created_at = ma.fields.DateTime()
    updated_at = ma.fields.DateTime()
    violations = ma.fields.List(ma.fields.Dict(required=False))
    @post_load
    def make_project_file(self, data):
        return ProjectFile(**data)

'''
    ==============================================
    nalign - Class Factory
    ================================================
'''

class NAlignSetFactory(object):

    # db connect in __init__?
    def __init__(self):
        # log.debug ('init')
        pass

    def get_marshalled_schema(self,obj):
        if obj:
            schema=ProjectSchema()
            retdata = schema.dump(obj)
            return retdata
    
    def create_project(self,data):
        i = 0
        proj_obj ={}
        res =[]
        if 'db_id' in data:
            if data["db_id"]:
                proj_obj = self.update_project(data)
        if "multiple_image_upload_status" in data:
            print("file_upload_count data",data["multiple_image_upload_status"])
        if not proj_obj:
            # print("im inside , th case")
            if "link_source"  in data:
                link_source=data["link_source"]
            if "file" in data:
                file = data["file"]
                print("file name", file)
            proj_obj, error = ProjectSchema().load(data)
            print("",proj_obj,error)
            proj_obj["db_id"] = uuid.uuid4().hex
            proj_obj["created_at"] = datetime.datetime.now()
            proj_obj['multiple_video_upload_status'] = {"status":"processing"}
            
            if proj_obj["file_url"] != None and proj_obj["file_url"] != '': 
            
                music_file_name = proj_obj["db_id"]+'.mp3'
                video_file_name = proj_obj["db_id"]+'.mp4'
                music_file_name_wav = proj_obj["db_id"]+'.wav'
                prefix_folder = settings.BASE_MEDIA_PATH
                from urllib.error import HTTPError

                try:
                    print("im herefzdfds000")
                    yt_download(proj_obj["file_url"],prefix_folder+music_file_name ,ismusic=True)
                    yt_download(proj_obj["file_url"],prefix_folder+video_file_name)
                    subprocess.call(["ffmpeg", "-i",prefix_folder+music_file_name,music_file_name_wav])
                    sound = AudioSegment.from_wav(music_file_name_wav)
                    sound = sound.set_channels(1)
                    sound = sound.set_frame_rate(44100)
                    export_path = sound.export(BASE_MEDIA_PATH+music_file_name_wav, format="wav")
                    print(export_path)
                    video = pafy.new(proj_obj["file_url"], basic=True)
                    print("video thumb",video.thumb)
                    proj_obj["thumbnail_url"] = video.thumb
                    proj_obj['mono_link']='/static/media/'+proj_obj["db_id"]+'.wav'
                    proj_obj["updated_at"] = datetime.datetime.now() 
                    proj_obj["captions"] = ""
                    proj_obj.save() 
                    schema=ProjectSchema()
                    retdata,error = schema.dump(proj_obj)
                    print("im erorr",retdata)
                    # print("im retdata",retdata)
                    return retdata   
                except Exception as exc:
                    print("im heref",exc)
                    return res
                    # proj_obj['mono_link']='Error Occurred while downloading'
                
                
                # result = BASE_MEDIA_PATH+music_file_name_wav
                            
            
                # print(error)
                # proj_obj["thumbnail_url"] = ''
                # proj_obj['mono_link']='Error Occcured While downloading'
                # proj_obj["updated_at"] = datetime.datetime.now() 
                # proj_obj["captions"] = ""
                # proj_obj.save()
        

    def get_by_id(self,db_id):
        """ This gives project based on id """
        project = Project.objects().filter(db_id = db_id).first()
        if project:
            return project
        else:
            raise MVException("project id %s doesn't exist"%(db_id))

    def get_project_by_id(self,db_id):

        """ This gives marshalled project result """
        if db_id:
            project=self.get_by_id(db_id)
            if project:
                return self.get_marshalled_schema(project)


    def  get_all_project(self):
        project = Project.objects().order_by('-updated_at')
       
        if project:

            schema=ProjectSchema()
            retdata = schema.dump(project,many=True)
            return retdata

        else:
            return []

    def get_query_order(self,order,column):
        order=order.lower()
        if order=="asc":
            order='+'
        elif order=="desc":
            order="-"
        return order+column


    def get_paginated_project_results(self,partial,column,order,page_number,limit):
        num_offset = (page_number - 1) * limit
        num_limit = num_offset + limit
        if num_offset < 0:
            raise MVException("Cannot go any further back")

        total_results = Project.objects(deleted=False).count()
        query_ordered_by = self.get_query_order(order,column)
        filtered_results = Project.objects(
            name__icontains=partial, deleted=False).count()
        if limit == -1:
            query_result = Project.objects(name__icontains=partial, deleted=False).order_by(query_ordered_by)[:]
        else:
            query_result = Project.objects(name__icontains=partial, deleted=False).order_by(query_ordered_by)[
                num_offset:num_limit]
            if query_ordered_by == '+name':
                query_result = Project.objects(name__icontains=partial,
                    deleted=False).order_by(query_ordered_by)
                query_result = sorted(query_result, key=lambda k: k["name"].lower())[
                    num_offset:num_limit]
            if query_ordered_by == '-name':
                query_result = Project.objects(name__icontains=partial,
                    deleted=False).order_by(query_ordered_by)
                query_result = sorted(query_result, key=lambda k: k["name"].lower(), reverse=True)[
                    num_offset:num_limit]
            print("total result",total_results)
            # retlist = []
            # for i in query_result:
            #     i.processMsg=self.get_progress_bar(i.db_id)
            #     retlist.append(i)
        return {'data': query_result, 'recordsTotal': total_results, 'recordsFiltered': filtered_results}

    def update_project(self,data):
        proj_obj=self.get_by_id(data["db_id"])
        if proj_obj:
            # print("im updated vino")
            if "name" in data:
                proj_obj["name"]=data["name"]
            if "description" in data:
                proj_obj["description"]=data["description"]
            if "file_url" in data:
                proj_obj["file_url"]=data["file_url"]
            if "file_duration" in data:
                proj_obj["file_duration"]=data["file_duration"]
            if "thumbnail_url" in data:
                proj_obj["thumbnail_url"]=data["thumbnail_url"]
            if "brand" in data:
                proj_obj["brand"]=data["brand"]
            if "product" in data:
                proj_obj["product"]=data["product"]
            if "image_width" in data:
                proj_obj["image_width"]=data["image_width"]
            if "image_height" in data:
                proj_obj["image_height"]=data["image_height"]
            if "updated_at" in data:
                proj_obj["updated_at"]=datetime.datetime.now()
            if "link_source" in data:
                link_source=data["link_source"].upper()
                if link_source == "EXTERNAL":
                    proj_obj["file_status"] = {"status":"Processing"} #video yet to be uploaded
                else:
                    proj_obj["file_status"] = {"status":"Completed"} #video uploaded already
            proj_obj.save()
        return proj_obj

theNAlignSetFactory = NAlignSetFactory()




