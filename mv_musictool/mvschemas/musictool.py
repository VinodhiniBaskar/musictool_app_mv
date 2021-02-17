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
from pytube import YouTube
from pydub import AudioSegment
from mhyt import yt_download
import cv2
from functools import wraps
from flask import abort
import marshmallow as ma
from urllib.error import ContentTooShortError
from marshmallow import Schema, post_load, validate
from mv_musictool.mvmodels.Projects import Project,ProjectFile,TempFileStorage
from mv_musictool.mvexception.exception import MVException, ValidationException,Test
from mongoengine.queryset.visitor import Q
from flask import Flask,jsonify
from flask_pymongo import PyMongo
from flask_restplus import Api, Resource, fields
from bson import ObjectId
from mv_musictool import settings
from mv_musictool.api import utils
from pymongo import MongoClient
import threading
from werkzeug.utils import secure_filename


print (sys.getdefaultencoding())

log = logging.getLogger(__name__)
""" Db initialization """
local=MongoClient()
db=local['test_youtube_db']
coll=db["test_youtube_account"]


WATCH_URL = "https://www.youtube.com/watch?v="
# pafy.set_api_key("AIzaSyDb6YEmYxpBPA4il0VmEqxYUC2qovIuJGo")


DEFAULT_UPLOAD_PATH = settings.MEDIA_PATH+"/"
BASE_MEDIA_PATH = "mv_musictool/static/media/"
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
    file_status = ma.fields.Dict(required=False)
    thumbnail_url = ma.fields.Str(required=False)
    file_type= ma.fields.Str(required=False)
    published_at = ma.fields.DateTime()
    created_at = ma.fields.DateTime()
    updated_at = ma.fields.DateTime()
    captions = ma.fields.Str(required=False)
    mono_link = ma.fields.Str(required=False)

    @post_load
    def make_project(self, data):
        return Project(**data)

'''
    ==============================================
    musictool - Class Factory
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
        # if 'db_id' in data:
        #     if data["db_id"]:
        #         proj_obj = self.update_project(data)
        if not proj_obj:
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
                prefix_folder = BASE_MEDIA_PATH
                try:
                    yt_download(proj_obj["file_url"],prefix_folder+music_file_name ,ismusic=True)
                    yt_download(proj_obj["file_url"],prefix_folder+video_file_name)
                    subprocess.call(["ffmpeg", "-i",prefix_folder+music_file_name,music_file_name_wav])
                    sound = AudioSegment.from_wav(music_file_name_wav)
                    sound = sound.set_channels(1)
                    sound = sound.set_frame_rate(44100)
                    export_path = sound.export(BASE_MEDIA_PATH+music_file_name_wav, format="wav")
                    print(export_path)
                    video = pafy.new(proj_obj["file_url"], basic=True)
                    # get_video_duration = YouTube(proj_obj["file_url"]) -- Option
                    print("video thumb",video.thumb)
                    proj_obj["thumbnail_url"] = video.thumb
                    proj_obj["file_duration"] = str(video.duration)
                    proj_obj["mono_link"]='/static/media/'+proj_obj["db_id"]+'.wav'
                    proj_obj["updated_at"] = datetime.datetime.now() 
                    proj_obj["captions"] = ""
                    proj_obj.save() 
                    schema=ProjectSchema()
                    retdata,error = schema.dump(proj_obj)
                    print("im erorr",retdata)
                    return retdata   
                except Exception as exc:
                    print("im heref",exc)
                    return res
                   
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
        return {'data': query_result, 'recordsTotal': total_results, 'recordsFiltered': filtered_results}

    
theNAlignSetFactory = NAlignSetFactory()




