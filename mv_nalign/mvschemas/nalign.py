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
from pydub import AudioSegment
from mhyt import yt_download
import cv2
from functools import wraps
from flask import abort
import marshmallow as ma
from marshmallow import Schema, post_load, validate
# from mv_nalign.mvmodels.Brands import BrandCategoryGroup
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
# from mv_nalign.utility import upload_to_s3,object_detection,detect_text,upload_to_gcp
# from mv_nalign.utility.src.aws_helper_service import AwsHelperService
# from mv_nalign.analysis import analysis,analysis_main
from pymongo import MongoClient
import threading
from PIL import Image
import boto3
import asyncio
from humanfriendly import format_timespan
from google.cloud import storage
import concurrent.futures as fu
# from mv_nalign.analysis.src.aws_helper_service import AwsHelperService
# from mv_nalign.analysis.src.principle.gaze import gaze
# from mv_nalign.analysis.src.principle.text_position import text_over_face, text_relative_position
# from mv_nalign.analysis.src.principle.numerosity import numerosity_principle
# from mv_nalign.analysis.src.principle.background import background_principle
# from mv_nalign.analysis.src.principle.variation import variation_in_terrain
# from mv_nalign.analysis.src.principle.body_parts import body_parts
# from mv_nalign.analysis.src.principle.logo import logo
# from mv_nalign.analysis.src.principle.humanity import humanity_focused as hf, close_proximity as cp, family_interactions as fm, \
#     women_close_proximity as wcp
# from mv_nalign.analysis.src.data_preloader import PreLoader
from werkzeug.utils import secure_filename
# from dotenv import load_dotenv
# load_dotenv() 
 
#Removed dotenv

print (sys.getdefaultencoding())

log = logging.getLogger(__name__)
""" Db initialization """
local=MongoClient()
db=local['test_youtube_db']
coll=db["test_youtube_account"]


WATCH_URL = "https://www.youtube.com/watch?v="
AMAZON_BASE_URL="https://machine-vantage-inc-images.s3.us-east-2.amazonaws.com/"
AMAZON_VIDEO_BASE_URL="https://machine-vantage-inc-video.s3.us-east-2.amazonaws.com/"
DEFAULT_CAPTIONS_STRING = "No Captions Available"

ELEVEN_PRINCIPLE = ['','','','','','','','TWO CONSISTENT CHARACTERS','WOMEN TOGETHER','','FAMILY INTERACTIONS','']
DEFAULT_UPLOAD_PATH = settings.MEDIA_PATH+"/"
BASE_MEDIA_PATH = "mv_nalign/media/"
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


# class NeuroAnalysisSchema(Schema):

#     db_id = ma.fields.Str(required=False)
#     ref_id = ma.fields.Str(required=False)
#     file_name = ma.fields.Str(required=False)
#     created_date = ma.fields.DateTime()
#     violation_status = ma.fields.Str(required=False)
#     file_type = ma.fields.Str(required=False)
#     title_name = ma.fields.Str(required=False)
#     more_than_two_consistent_characters = ma.fields.Dict(required = False)
#     women_together = ma.fields.Dict(required = False)
#     lack_of_family_interactions = ma.fields.Dict(required = False)
#     text_on_face = ma.fields.Dict(required = False)
#     images_on_right_words_to_left = ma.fields.Dict(required = False)
#     eyes_contact = ma.fields.Dict(required= False)
#     more_than_three_visual_clusters = ma.fields.Dict(required= False)
#     interrupt_flow_storyline = ma.fields.Dict(required= False)
#     overlay_text_background = ma.fields.Dict(required= False)
#     variation_in_terrain = ma.fields.Dict(required= False)
#     body_part_isolation = ma.fields.Dict(required= False)

#     @post_load
#     def make_neuro_analysis(self, data):
#         return NeuroAnalysis(**data)


# class FeedbackSchema(Schema):
#     db_id = ma.fields.Str(required=False)
#     ref_id = ma.fields.Str(required=False)
#     violation_name=ma.fields.Str(required=False)
#     feedbacks=ma.fields.List(ma.fields.Str(required=False),required=False)
#     file_type=ma.fields.Str(required=False,default="image")
#     is_violation=ma.fields.Boolean(required=False)
#     created_at = ma.fields.DateTime()
#     updated_at = ma.fields.DateTime()



#     @post_load
#     def make_feedback(self, data):
#         return Feedback(**data)


'''
    ==============================================
    nalign - Class Factory
    ================================================
'''


class BulkUploadThread(threading.Thread):
    def __init__(self,ref_id):
        self.ref_id = ref_id
        threading.Thread.__init__(self)

    def run(self):
        print("my thread",self.ref_id)
        project_threading=theNAlignSetFactory.bulk_upload_video(self.ref_id)

class BulkUploadThread_Image(threading.Thread):
    def __init__(self,ref_id):
        self.ref_id = ref_id
        threading.Thread.__init__(self)

    def run(self):
        print("my thread",self.ref_id)
        project_threading_image=theNAlignSetFactory.bulk_upload_image(self.ref_id)

class ProcessVideoThread(threading.Thread):
    def __init__(self,ref_id):
        self.ref_id = ref_id
        threading.Thread.__init__(self)

    def run(self):
        c=theNAlignSetFactory.generate_impacts(self.ref_id)


def process_project(ref_id):
    print('process project', ref_id)
    print("Project Threading started")
    BulkUploadThread(ref_id).start()

def process_video(ref_id):
    print("Threading started")
    ProcessVideoThread(ref_id).start()

def process_image(ref_id):
    print("Threading started")
    BulkUploadThread_Image(ref_id).start()

class NAlignSetFactory(object):

    # db connect in __init__?
    def __init__(self):
        # log.debug ('init')
        pass

    def get_brand(self):

        """ This function defines that brand and category group """

        brd_obj= BrandCategoryGroup.objects().distinct('brand')
        brd = []
        if brd_obj:
            for k in brd_obj:
                brd.append(k)
        return sorted(brd)

    def get_product_by_brand(self,brand_name):
        cat_obj= BrandCategoryGroup.objects(brand = brand_name).distinct('category')
        cat = []
        if cat_obj:
            for k in cat_obj:
                cat.append(k)
        else:
            raise MVException("brand doesn't exist")

        return sorted(cat)

    def get_marshalled_schema(self,obj):
        if obj:
            schema=ProjectSchema()
            retdata = schema.dump(obj)
            return retdata
    
    def bulk_upload_video(self,ref_id):
        proj_obj=self.get_by_id(ref_id)
        up_load=upload_to_s3.upload_file(proj_obj['file_url'], settings.VIDEO_BUCKET_NAME,proj_obj['file_url'].split('/')[-1])
        file_url = AMAZON_VIDEO_BASE_URL+proj_obj['file_url'].split('/')[-1]
        proj_obj["file_url"] =file_url
        file_name_thumbnail = ref_id+THUMBNAIL_JPG
        org_img_to_s3 = upload_to_s3.upload_file(settings.BASE_MEDIA_PATH+file_name_thumbnail,settings.IMAGE_BUCKET_NAME,file_name_thumbnail)
        proj_obj["thumbnail_url"] =AMAZON_BASE_URL+file_name_thumbnail
        proj_obj['multiple_video_upload_status'] = {"status":"Completed"}
        proj_obj.save()
        if proj_obj['multiple_video_upload_status'] == {"status":"Completed"}:
            process_video(proj_obj.db_id)
        schema=ProjectSchema()
        retdata,error = schema.dump(proj_obj)
        return retdata
    
    def bulk_upload_image(self,ref_id):
        proj_obj=self.get_by_id(ref_id)
        t_file = BASE_MEDIA_PATH+ref_id+THUMBNAIL_JPG
        up_load=upload_to_s3.upload_file(t_file, settings.IMAGE_BUCKET_NAME,t_file.split('/')[-1])
        # print("om upload",up_load)
        thumbnail_url = AMAZON_BASE_URL+t_file.split('/')[-1]
        # print("thumbnail_url",thumbnail_url)
        proj_obj["thumbnail_url"] =thumbnail_url
        filename = proj_obj["db_id"]+'.'+thumbnail_url.split('.')[-1]
        org_img_to_s3 = upload_to_s3.upload_file(settings.BASE_MEDIA_PATH+filename,settings.IMAGE_BUCKET_NAME,filename)
        print("org_img uploaded successfully")
        proj_obj["file_url"] =AMAZON_BASE_URL+filename
        # up_load=upload_to_s3.upload_file(proj_obj['file_url'], settings.VIDEO_BUCKET_NAME,proj_obj['file_url'].split('/')[-1])
        # file_url = AMAZON_VIDEO_BASE_URL+proj_obj['file_url'].split('/')[-1]
        # proj_obj["file_url"] =file_url
        # file_name_thumbnail = ref_id+THUMBNAIL_JPG
        # org_img_to_s3 = upload_to_s3.upload_file(settings.BASE_MEDIA_PATH+file_name_thumbnail,settings.IMAGE_BUCKET_NAME,file_name_thumbnail)
        # proj_obj["thumbnail_url"] =AMAZON_BASE_URL+file_name_thumbnail
        proj_obj['multiple_video_upload_status'] = {"status":"Completed"}
        proj_obj.save()
        if proj_obj['multiple_video_upload_status'] == {"status":"Completed"}:
            process_video(proj_obj.db_id)
        schema=ProjectSchema()
        retdata,error = schema.dump(proj_obj)
        return retdata

    def create_project(self,data):
        #handling upsert operation here
        link_source = 'INTERNAL'
        # print("im data",data['db_id'])
        ## Commented print
        i = 0
        proj_obj ={}
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
            
            # schema=ProjectSchema()
            # retdata,error = schema.dump(proj_obj)
        # UPDATE STATUS
        # link source External means user uploaded a video in youtube and then get the metadata information
        # link source Internal means user using youtube link to get the metadata information

            # if proj_obj["file_type"] =="video" and (proj_obj["file_url"]=='' or proj_obj["file_url"]==None):
            #     t_file_split=self.generate_video_storage(file,proj_obj["db_id"])
            #     t_file = t_file_split.split('@')[0]
            #     t_duration = t_file_split.split('@')[1]
            #     proj_obj["file_url"] = t_file
            #     file_name_thumbnail = ''
            #     proj_obj["thumbnail_url"] = file_name_thumbnail
            #     proj_obj["file_duration"]= str(t_duration)
            # proj_obj.save()

            if proj_obj["file_url"] != None and proj_obj["file_url"] != '': 
                # video_not_yt_download = proj_obj["file_url"].split('.')[0]
                # url_check = BASE_MEDIA_PATH+proj_obj["db_id"]
                # if video_not_yt_download == url_check and video_not_yt_download !='':
                #     proj_obj["file_youtube"]= "No"
                #     process_project(proj_obj.db_id)
                # elif video_not_yt_download == 'https://www' and video_not_yt_download !='' :
                #     proj_obj["file_youtube"]= "Yes"
                # print("file_name",file)
                music_file_name = proj_obj["db_id"]+'.mp3'
                video_file_name = proj_obj["db_id"]+'.mp4'
                music_file_name_wav = proj_obj["db_id"]+'.wav'
                prefix_folder = settings.BASE_MEDIA_PATH
                yt_download(proj_obj["file_url"],prefix_folder+music_file_name ,ismusic=True)
                yt_download(proj_obj["file_url"],prefix_folder+video_file_name)
                subprocess.call(["ffmpeg", "-i",prefix_folder+music_file_name,music_file_name_wav])
                sound = AudioSegment.from_wav(music_file_name_wav)
                sound = sound.set_channels(1)
                export_path = sound.export(BASE_MEDIA_PATH+music_file_name_wav, format="wav")
                print(export_path)
                result = BASE_MEDIA_PATH+music_file_name_wav
                proj_obj["thumbnail_url"] = prefix_folder+video_file_name
                proj_obj['mono_link']=result
            proj_obj.save()

            if link_source:
                if link_source.upper() == "EXTERNAL":
                    proj_obj["file_status"] = {"status":"Processing"} #video yet to be uploaded
                else:
                    proj_obj["file_status"] = {"status":"Completed"} #video uploaded already

            proj_obj["updated_at"] = datetime.datetime.now() 
            proj_obj["impacts_status"] = {"status":"processing"}

            proj_obj["captions"] = ""
            if proj_obj["file_type"] =="image" and (proj_obj["file_url"]=='' or proj_obj["file_url"]==None):
                t_file_split=self.generate_thumbnail_image(file,proj_obj["db_id"])
                t_file = t_file_split.split('@')[0]
                t_file_width = t_file_split.split('@')[1].split(',')[0]
                t_file_height = t_file_split.split('@')[1].split(',')[1]
                # print("file",t_file.split('/')[-1])
                # print("file width",t_file_width)
                # print("file width",t_file_height)
                if t_file_split:
                    proj_obj["file_url"] = t_file
                    # file_name_thumbnail = ''
                    # proj_obj["thumbnail_url"] = file_name_thumbnail
                    proj_obj["file_youtube"]= "Null"
                    proj_obj["image_width"]=t_file_width
                    proj_obj["image_height"]=t_file_height
                    up_load=upload_to_s3.upload_file(t_file, settings.IMAGE_BUCKET_NAME,t_file.split('/')[-1])
                    # thumbnail_url = AMAZON_BASE_URL+t_file.split('/')[-1]
                    proj_obj["thumbnail_url"] =''
                    process_image(proj_obj.db_id)
                    # filename = proj_obj["db_id"]+'.'+thumbnail_url.split('.')[-1]
                    # org_img_to_s3 = upload_to_s3.upload_file(settings.BASE_MEDIA_PATH+filename,settings.IMAGE_BUCKET_NAME,filename)
                    # print("org_img uploaded successfully")
                    # proj_obj["file_url"] =AMAZON_BASE_URL+filename
                    proj_obj["file_status"] = {"status":"Completed"}
            proj_obj.save()
        
        if (proj_obj["file_youtube"]== "Null" or proj_obj["file_youtube"]== "Yes")  and proj_obj["impacts_status"]["status"]=="processing":
            # print("im inside impacts")
            process_video(proj_obj.db_id)
        schema=ProjectSchema()
        retdata,error = schema.dump(proj_obj)
        print("im erorr",error)
        # print("im retdata",retdata)
        return retdata

    def generate_video_storage(self,video_file,ref_id):
        default_thumbnail_size = (700,400)
        file_extn = video_file.filename.split('.')[-1]
        filename=ref_id+"."+file_extn
        print("storage", filename)
        path= os.path.join(BASE_MEDIA_PATH)
        video_file.save(path+filename)
        video_file.close()
        # ImportFiles.get_video_metadata()
        vidcap = cv2.VideoCapture(BASE_MEDIA_PATH+filename)
        fps = vidcap.get(cv2.CAP_PROP_FPS)      # OpenCV2 version 2 used "CV_CAP_PROP_FPS"
        frame_count = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count/fps
        # print("im duration",duration)
        if duration <= 60:
            seconds = round(duration%60,1)
            vid_duration= str(seconds)+' seconds'
        if duration > 60:
            seconds = round(duration // 60,2)
            vid_duration= str(seconds)+' minutes'
        print("im convert", seconds)
        vidcap.set(cv2.CAP_PROP_POS_MSEC,1000)      # just cue to 20 sec. position
        success,image = vidcap.read()
        if success:
            cv2.imwrite(os.path.join(path , ref_id+THUMBNAIL_JPG), image)     # save frame as JPEG file
        return settings.BASE_MEDIA_PATH+filename+'@'+ vid_duration

    def generate_thumbnail_image(self,image_file,ref_id):
        # print(image_file)
        default_thumbnail_size = (700,400)
        # print("1 image_dile",image_file)
        file_extn = image_file.filename.split('.')[-1]
        filename=ref_id+".jpg" #+file_extn
        path= os.path.join(BASE_MEDIA_PATH)
        im = Image.open(image_file)
        rgb_im = im.convert('RGB')
        rgb_im.save(path+filename)
        
        # print("image_dile",image_file)
        # image_file.save(path+filename)
        # path= os.path.join(BASE_MEDIA_PATH)
        im = Image.open(path+filename)
        width, height = im.size
        # print("im widht",width)
        # print("im height", height)
        # print("path file naem",path+filename)
        im.thumbnail(default_thumbnail_size)
        thumbnail_file_name = ref_id+"_thumbnail.jpg"#+file_extn # THUMBNAIL_JPG #"_thumbnail."+file_extn
        im.save(path+thumbnail_file_name)
        im.close()

        return settings.BASE_MEDIA_PATH+thumbnail_file_name+'@'+str(width)+','+str(height)

    # def generate_impacts(self,project_id):
    #     proj_obj=self.get_by_id(project_id)
    #     file_type = proj_obj.file_type
    #     yt_downloads = ''
    #     video_not_yt_download = proj_obj.file_url.split('.')[0]
    #     title_file_name = proj_obj.name
    #     print(title_file_name)
    #     created_at = proj_obj.created_at
    #     print(created_at)
    #     if file_type=="video": 
    #         if video_not_yt_download != 'https://machine-vantage-inc-video':
    #             yt_downloads = self.download_youtube_video(proj_obj.file_url,project_id,file_type)
    #         else:
    #             yt_downloads = proj_obj.file_url
    #             print("video downloaded")
    #         if  not proj_obj.is_uploaded:
    #             if yt_downloads:
    #                 proj_obj.is_uploaded=True
    #                 proj_obj.save()
    #                 file_name_url=yt_downloads
    #                 file_name_url=file_name_url.split('/')[-1]
    #         elif proj_obj.is_uploaded:
    #             proj_obj.is_uploaded=True
    #             proj_obj.save()
    #             file_name_url=yt_downloads
    #             file_name_url=file_name_url.split('/')[-1]
    #         bucket=settings.VIDEO_BUCKET_NAME
    #     else:
    #         file_name_url = proj_obj.file_url.split('/')[-1]
    #         bucket=settings.IMAGE_BUCKET_NAME

    #     neuro = NeuroAnalysis.objects(ref_id=project_id).first()
    #     if not neuro:
    #         payload = {}
    #         payload["db_id"] = uuid.uuid4().hex
    #         payload["ref_id"] = project_id
    #         payload["file_name"]=file_name_url
    #         payload["title_name"] = title_file_name
    #         payload["created_at"]= created_at
    #         payload["violation_status"]= 'Processing'
    #         payload["file_type"] = file_type
    #         neuro,error = NeuroAnalysisSchema().load(payload)
    #         print("im error",error)
    #         neuro.save()

    #     role_arn = 'arn:aws:iam::274822417273:role/AmazonRekognitionServiceRoleCopy'
    #     pickle_path = "./mv_nalign/var/preloader_models/" + re.sub("[^a-zA-Z0-9\.]", "_", '%s_%s.pickle' % (bucket, file_name_url))
    #     print("pickle",pickle_path)
    #     try:
    #         with open(pickle_path, 'rb') as handle:
    #             print('[%s] Loading pickled data...\n' % time.time())
    #             p = pickle.load(handle)
    #             p.update_public_aws_path()
    #     except FileNotFoundError:
    #         print('[%s] Loading AWS data...\n' % time.time())
    #         p = PreLoader(file_name_url, bucket)
    #         p.preload()
        
    #     try:
    #         with fu.ThreadPoolExecutor() as ex:
    #             launches = []
    #         # Eye Contact
    #             print("file type",file_type)
    #             if file_type=='video' or file_type=='image':
    #                 try: 
    #                     start = time.time()
    #                     analyzer = gaze.Gaze(p)
    #                     launches.append(ex.submit(analyzer))
    #                     res_1 = analyzer.run()
    #                     res_json = json.dumps(res_1)
    #                     json_object = json.loads(res_json)
    #                     stop = time.time()
    #                     time_capture = format_timespan(stop - start)
    #                     if analyzer != '':
    #                         results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,project_id,analyzer_type="Eye",scenario='search_for_eyes_contact')
    #                         neuro.no_eyes_contact={"analysis_result":json_object,"results":results,'timeduration':time_capture}
    #                         neuro.save()
    #                         self.get_progress_bar(project_id)
    #                     else:
    #                         neuro.no_eyes_contact={"analysis_result":json_object,"results":[],'timeduration':time_capture}
    #                         neuro.save()
    #                 except (ValueError, KeyError) as e:
    #                     neuro.no_eyes_contact={"analysis_result":[],"results":[],'timeduration':[]}
    #                     neuro.save()

    #             if file_type=='video' or file_type=='image':
    #                 try:
    #                     start = time.time()
    #                     analyzer = hf.HumanityFocused(p) #C
    #                     launches.append(ex.submit(analyzer))
    #                     res_1 = analyzer.run()
    #                     res_json = json.dumps(res_1)
    #                     json_object = json.loads(res_json)
    #                     stop = time.time()
    #                     time_capture = format_timespan(stop - start)
    #                     if analyzer != '':
    #                         results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,project_id,analyzer_type="Women",scenario='search_for_more_than_two_consistent_characters')
    #                         neuro.more_than_two_consistent_characters={"analysis_result":json_object,"results":results,'timeduration':time_capture}
    #                         neuro.save()
    #                         self.get_progress_bar(project_id)
    #                     else:
    #                         neuro.more_than_two_consistent_characters={"analysis_result":json_object,"results":[],'timeduration':time_capture}
    #                         neuro.save()
    #                 except (ValueError, KeyError) as e:
    #                     neuro.more_than_two_consistent_characters={"analysis_result":[],"results":[],'timeduration':[]}
    #                     neuro.save() 
                
    #             if file_type=='video' or file_type=='image':
    #                 try:
    #                     start = time.time()
    #                     analyzer = fm.FamilyInteractions(p) #C
    #                     launches.append(ex.submit(analyzer))
    #                     res_1 = analyzer.run()
    #                     res_json = json.dumps(res_1)
    #                     json_object = json.loads(res_json)
    #                     stop = time.time()
    #                     time_capture = format_timespan(stop - start)
    #                     if analyzer != '':
    #                         results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,project_id,analyzer_type="Women",scenario='search_for_more_than_two_consistent_characters')
    #                         neuro.lack_of_family_interactions={"analysis_result":json_object,"results":results,'timeduration':time_capture}
    #                         neuro.save()
    #                         self.get_progress_bar(project_id)
    #                     else:
    #                         neuro.lack_of_family_interactions={"analysis_result":json_object,"results":[],'timeduration':time_capture}
    #                         neuro.save()
    #                 except (ValueError, KeyError) as e:
    #                     neuro.lack_of_family_interactions={"analysis_result":[],"results":[],'timeduration':[]}
    #                     neuro.save()

    #             if file_type=='video' or file_type=='image':
    #                 try:
    #                     start = time.time()
    #                     analyzer = text_relative_position.TextObjectsRelative(p)
    #                     launches.append(ex.submit(analyzer))
    #                     res_1 = analyzer.run()
    #                     res_json = json.dumps(res_1)
    #                     json_object = json.loads(res_json)
    #                     print("im object",json_object)
    #                     stop = time.time()
    #                     time_capture = format_timespan(stop - start )
    #                     if analyzer != '':
    #                         results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,project_id,analyzer_type="TRP",scenario='search_for_images_on_right_words_to_left')
    #                         neuro.images_on_right_words_to_left={"analysis_result":json_object,"results":results,'timeduration':time_capture}
    #                         neuro.save()
    #                         self.get_progress_bar(project_id)
    #                     else:
    #                         neuro.images_on_right_words_to_left={"analysis_result":json_object,"results":[],'timeduration':time_capture}
    #                         neuro.save()
    #                 except (ValueError, KeyError) as e:
    #                     neuro.images_on_right_words_to_left={"analysis_result":[],"results":[],'timeduration':[]}
    #                     neuro.save()
                
    #             if file_type=='video' or file_type=='image':
    #                 try:
    #                     start = time.time()
    #                     analyzer = text_over_face.TextOverFace(p)
    #                     launches.append(ex.submit(analyzer))
    #                     res_1 = analyzer.run()
    #                     res_json = json.dumps(res_1)
    #                     json_object = json.loads(res_json)
    #                     stop = time.time()
    #                     time_capture = format_timespan(stop - start )
    #                     if analyzer != '':
    #                         results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,project_id,analyzer_type="TRP",scenario='search_for_images_on_right_words_to_left')
    #                         neuro.text_on_face={"analysis_result":json_object,"results":results,'timeduration':time_capture}
    #                         neuro.save()
    #                         self.get_progress_bar(project_id)
    #                     else:
    #                         neuro.text_on_face={"analysis_result":json_object,"results":[],'timeduration':time_capture}
    #                         neuro.save()
    #                 except (ValueError, KeyError) as e:
    #                     neuro.text_on_face={"analysis_result":[],"results":[],'timeduration':[]}
    #                     neuro.save() 
                
    #             if file_type=='video' or file_type=='image':
    #                 try:
    #                     start = time.time()
    #                     analyzer = numerosity_principle.NumerosityPrinciple(p)
    #                     launches.append(ex.submit(analyzer))
    #                     res_1 = analyzer.run()
    #                     res_json = json.dumps(res_1)
    #                     json_object = json.loads(res_json)
    #                     stop = time.time()
    #                     time_capture = format_timespan(stop - start)
    #                     if analyzer != '':
    #                         results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,project_id,analyzer_type="TRP",scenario='search_for_numerosity_principle')
    #                         neuro.more_than_three_visual_clusters={"analysis_result":json_object,"results":results,'timeduration':time_capture}
    #                         neuro.save()
    #                         self.get_progress_bar(project_id)
    #                     else:
    #                         neuro.more_than_three_visual_clusters={"analysis_result":json_object,"results":[],'timeduration':time_capture}
    #                         neuro.save()
    #                 except (ValueError, KeyError) as e:
    #                     neuro.more_than_three_visual_clusters={"analysis_result":[],"results":[],'timeduration':[]}
    #                     neuro.save() 
                
    #             if file_type=='video' or file_type=='image':
    #                 try:
    #                     start = time.time()
    #                     analyzer = cp.CloseProximity(p) #C
    #                     launches.append(ex.submit(analyzer))
    #                     res_1 = analyzer.run()
    #                     res_json = json.dumps(res_1)
    #                     json_object = json.loads(res_json)
    #                     stop = time.time()
    #                     time_capture = format_timespan(stop - start)
    #                     if analyzer != '':
    #                         results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,project_id,analyzer_type="CP",scenario='search_for_more_than_two_people_in_close_proximity')
    #                         neuro.more_than_two_people_in_close_proximity={"analysis_result":json_object,"results":results,'timeduration':time_capture}
    #                         neuro.save()
    #                         self.get_progress_bar(project_id)
    #                     else:
    #                         neuro.more_than_two_people_in_close_proximity={"analysis_result":json_object,"results":[],'timeduration':time_capture}
    #                         neuro.save()
    #                 except (ValueError, KeyError) as e:
    #                     neuro.more_than_two_people_in_close_proximity={"analysis_result":[],"results":[],'timeduration':[]}
    #                     neuro.save()

    #             if file_type=='video' or file_type=='image':
    #                 try:
    #                     start = time.time()
    #                     analyzer = wcp.WomenCloseProximity(p) #C
    #                     launches.append(ex.submit(analyzer))
    #                     res_1 = analyzer.run()
    #                     res_json = json.dumps(res_1)
    #                     json_object = json.loads(res_json)
    #                     stop = time.time()
    #                     time_capture = format_timespan(stop - start)
    #                     if analyzer != '':
    #                         results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,project_id,analyzer_type="CP",scenario='search_for_more_than_two_people_in_close_proximity')
    #                         neuro.women_apart_not_in_close_physicalproximity={"analysis_result":json_object,"results":results,'timeduration':time_capture}
    #                         neuro.save()
    #                         self.get_progress_bar(project_id)
    #                     else:
    #                         neuro.women_apart_not_in_close_physicalproximity={"analysis_result":json_object,"results":[],'timeduration':time_capture}
    #                         neuro.save()
    #                 except (ValueError, KeyError) as e:
    #                     neuro.women_apart_not_in_close_physicalproximity={"analysis_result":[],"results":[],'timeduration':[]}
    #                     neuro.save()

    #             if file_type=='video' or file_type=='image':
    #                 try:
    #                     start = time.time()
    #                     analyzer = background_principle.BackgroundPrinciple(p)
    #                     launches.append(ex.submit(analyzer))
    #                     res_1 = analyzer.run()
    #                     res_json = json.dumps(res_1)
    #                     json_object = json.loads(res_json)
    #                     stop = time.time()
    #                     time_capture = format_timespan(stop - start)
    #                     if analyzer != '':
    #                         results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,project_id,analyzer_type="Background",scenario='search_txt_bkg')
    #                         neuro.overlay_text_background={"analysis_result":json_object,"results":results,'timeduration':time_capture}
    #                         neuro.save()
    #                         self.get_progress_bar(project_id)
    #                     else:
    #                         neuro.overlay_text_background={"analysis_result":json_object,"results":[],'timeduration':time_capture}
    #                         neuro.save()
    #                 except (ValueError, KeyError) as e:
    #                     neuro.overlay_text_background={"analysis_result":[],"results":[],'timeduration':[]}
    #                     neuro.save()
    #             print(file_type)
    #             if file_type=='video':
    #                 try:
    #                     start = time.time()
    #                     analyzer = variation_in_terrain.VariationInTerrainPrinciple(p)
    #                     launches.append(ex.submit(analyzer))
    #                     res_1 = analyzer.run()
    #                     res_json = json.dumps(res_1)
    #                     json_object = json.loads(res_json)
    #                     stop = time.time()
    #                     time_capture = format_timespan(stop - start)
    #                     if json_object['ViolationFound'] == True:
    #                         results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,project_id,analyzer_type="Terrain",scenario='search_txt_bkg')
    #                         neuro.variation_in_terrain={"analysis_result":json_object,"results":results,'timeduration':time_capture}
    #                         neuro.save()
    #                         self.get_progress_bar(project_id)
    #                     else:
    #                         neuro.variation_in_terrain={"analysis_result":json_object,"results":[],'timeduration':time_capture}
    #                         neuro.save()
    #                 except (ValueError, KeyError) as e:
    #                     neuro.variation_in_terrain={"analysis_result":[],"results":[],'timeduration':[]}
    #                     neuro.save()

    #             if file_type=='video' or file_type=='image':
    #                 try:
    #                     start = time.time()
    #                     analyzer = body_parts.BodyParts(p)
    #                     launches.append(ex.submit(analyzer))
    #                     res_1 = analyzer.run()
    #                     res_json = json.dumps(res_1)
    #                     json_object = json.loads(res_json)
    #                     stop = time.time()
    #                     time_capture = format_timespan(stop - start)
    #                     if analyzer != '':
    #                         results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,project_id,analyzer_type="Body",scenario='search_body_parts')
    #                         neuro.body_part_isolation={"analysis_result":json_object,"results":results,'timeduration':time_capture}
    #                         neuro.save()
    #                         self.get_progress_bar(project_id)
    #                     else:
    #                         neuro.body_part_isolation={"analysis_result":json_object,"results":[],'timeduration':time_capture}
    #                         neuro.save()
    #                 except (ValueError, KeyError) as e:
    #                     neuro.body_part_isolation={"analysis_result":[],"results":[],'timeduration':[]}
    #                     neuro.save()

    #             if file_type=='video':
    #                 try:
    #                     start = time.time()
    #                     analyzer = logo.LogoPrinciple(p)
    #                     launches.append(ex.submit(analyzer))
    #                     res_1 = analyzer.run()
    #                     res_json = json.dumps(res_1)
    #                     json_object = json.loads(res_json)
    #                     stop = time.time()
    #                     time_capture = format_timespan(stop - start)
    #                     if analyzer != '':
    #                         results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,project_id,analyzer_type="Logo")
    #                         neuro.interrupt_flow_storyline={"analysis_result":json_object,"results":results,'timeduration':time_capture}
    #                         neuro.save()
    #                         self.get_progress_bar(project_id)
    #                     else:
    #                         neuro.interrupt_flow_storyline={"analysis_result":json_object,"results":[],'timeduration':time_capture}
    #                         neuro.save()
    #                 except (ValueError, KeyError) as e:
    #                     neuro.interrupt_flow_storyline={"analysis_result":[],"results":[],'timeduration':[]}
    #                     neuro.save()
    #         fu.wait(launches)
    #         print('[%s] Finished\n' % time.time())
    #     except IOError as e:
    #         print('[%s] Error: FS Operation failed: %s' % (time.time(), e.strerror))

    #     if file_type=="image":
    #         attrs = vars(neuro)
    #         print(', '.join("%s: %s" % item for item in attrs.items()))
    #         print("im neuro inside",vars(neuro))
    #         if 'more_than_two_people_in_close_proximity' in neuro and 'women_apart_not_in_close_physicalproximity' in neuro and 'lack_of_family_interactions' in neuro and 'images_on_right_words_to_left' in neuro and \
    #             'more_than_three_visual_clusters' in neuro and 'more_than_two_consistent_characters' in neuro and 'text_on_face' in neuro and 'no_eyes_contact' in neuro and 'overlay_text_background' in neuro and 'body_part_isolation' in neuro:
    #             proj_obj.impacts_status={"status":"completed"}
    #             proj_obj.impacts_count=self.get_total_impacts(self.get_impacts_count(project_id))
    #             proj_obj.updated_at=datetime.datetime.now()
    #             proj_obj.save()
    #             neuro.created_at=datetime.datetime.now()
    #             neuro.violation_status = 'Completed'
    #             neuro.file_type = file_type
    #             neuro.save()
    #             print("IMPACT CALCULATIONS COMPLETED")
    #             print("im neuro check",neuro)
    #     else:
    #         proj_obj.impacts_status={"status":"completed"}
    #         proj_obj.multiple_video_status={"status":"completed"}
    #         proj_obj.impacts_count=self.get_total_impacts(self.get_impacts_count(project_id))
    #         proj_obj.updated_at=datetime.datetime.now()
    #         proj_obj.save()
    #         neuro.created_at=datetime.datetime.now()
    #         neuro.violation_status = 'Completed'
    #         neuro.file_type = file_type
    #         neuro.save()
    #         print("IMPACT CALCULATIONS COMPLETED")

    #     return None

    def upload_image_to_s3_from_input(self,image_file,ref_id):
        file_extn = image_file.filename.split('.')[-1]
        filename=ref_id+"."+file_extn
        resp=upload_to_s3.upload_fileobj(image_file,settings.IMAGE_BUCKET_NAME,filename)
        if resp:
            resp = AMAZON_BASE_URL+filename
            return resp

    def does_check_duplicate_project_name(self,name,db_id=None):
        
        return False

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
            retlist = []
            for i in query_result:
                i.processMsg=self.get_progress_bar(i.db_id)
                retlist.append(i)
        return {'data': retlist, 'recordsTotal': total_results, 'recordsFiltered': filtered_results}

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

    def get_credentials(self):
        yt_credentials = coll.find({},{'_id':0})
        credentials={}
        for yt_cred in yt_credentials:
            credentials=yt_cred
        return credentials


    def upload_video_in_yt(self,file_data,video_details):
        credentials=self.get_credentials()
        print(credentials)
        # Load credentials from the data store.
        ext = file_data.filename.split('.')[-1]
        file_path=uuid.uuid4().hex+"."+ext
        f=file_data.save(file_path)

        credentials = google.oauth2.credentials.Credentials(
            **credentials)
        youtube = build(
            settings.API_SERVICE_NAME, settings.API_VERSION, credentials=credentials,cache_discovery=False)
        print(youtube)
        print(video_details)
        insert_request =youtube.videos().insert(
                part="snippet,status,contentDetails",
                
                body={
                    "snippet": {
                        "categoryId": "22",
                        "description": video_details["description"],
                        "title": video_details["title"]
                    },
                    "status": {
                        "privacyStatus": "private"
                    },

                     "contentDetails":{
                        "caption":True
                    }
                },


                    # TODO: For this request to work, you must replace "YOUR_FILE"
                    #       with a pointer to the actual file you are uploading.
                    media_body=MediaFileUpload(file_path,chunksize=-1,resumable=True)
        )
        insert_request.execute()
        
        data={}
        print(file_path)

        try:

            status,response=self.resumable_upload(insert_request)
            
            if 'id' in response:
                print("id exsit")
                payload = {
                    "db_id":None,
                    "name" : video_details["title"],
                    "description" : video_details["description"],
                    "file_url": WATCH_URL+response["id"],
                    "published_at": response["snippet"]["publishedAt"],
                    "link_source" : "external"
                    }
                created_response = self.create_project(payload)
                data["status"]= "Success"
                data["response"] = created_response
                #put entry into db for keep track

            else:
                data["status"]= "Failure"
                data["message"] = "Something went wrong"
        except Exception as e :
            # os.remove(file_path)

            raise MVException(str(e))
        os.remove(file_path)

        return data


    def get_list_upload_video(self):

        yt_credentials = coll.find({},{'_id':0})
        for yt_cred in yt_credentials:
            credentials=yt_cred

        print(credentials)
        credentials = google.oauth2.credentials.Credentials(
            **credentials)
        youtube = build(
            settings.API_SERVICE_NAME, settings.API_VERSION, credentials=credentials)
        print("kdjshdkhsd")
        request = youtube.videos().list(
            part="status"
,           id = "FuRNAOE50tE"
            )
        response = request.execute()
        return {"response":response}

    def resumable_upload(self,insert_request):
        response = None
        error = None
        retry = 0
        while response is None:
            try:
                print ("Uploading file...")
                status, response = insert_request.next_chunk()
                # print(json.dumps(response))
                if response is not None:
                    if 'id' in response:
                        print ("Video id '%s' was successfully uploaded." % response['id'])
                    else:
                        exit("The upload failed with an unexpected response: %s" % response)
            except utils.HttpError as e:
                if e.resp.status in utils.RETRIABLE_STATUS_CODES:
                    error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                                        e.content)
                else:
                    raise
            except utils.RETRIABLE_EXCEPTIONS as  e:
                error = "A retriable error occurred: %s" % e

        if error is not None:
            print (error)
            retry += 1
            if retry > utils.MAX_RETRIES:
                exit("No longer attempting to retry.")

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print ("Sleeping %f seconds and then retrying..." % sleep_seconds)
            time.sleep(sleep_seconds)

        return status,response


    def get_video_caption(self):
        yt_credentials = coll.find({},{'_id':0})
        for yt_cred in yt_credentials:
            credentials=yt_cred

        print(credentials)
        credentials = google.oauth2.credentials.Credentials(
            **credentials)
        youtube = build(
            settings.API_SERVICE_NAME, settings.API_VERSION, credentials=credentials)


        request = youtube.captions().list(
            part="snippet",
            videoId="blQb-64X_c4"
        )
        response = request.execute()
       
        return response


    def add_caption(self):
        """ adding a caption for the specific video id """

        yt_credentials = coll.find({},{'_id':0})
        for yt_cred in yt_credentials:
            credentials=yt_cred

        print(credentials)
        credentials = google.oauth2.credentials.Credentials(
            **credentials)
        youtube = build(
            settings.API_SERVICE_NAME, settings.API_VERSION, credentials=credentials)
        print("kdjshdkhsd")
        request = youtube.captions().insert(
           part="snippet",
           sync=True,
           body={
          "snippet": {

            "language": "en",
            "name": "",

            "videoId": "U74SZ0HciHE"
          }
        },

        # TODO: For this request to work, you must replace "YOUR_FILE"
        #       with a pointer to the actual file you are uploading.
        media_body=MediaFileUpload("sub.txt")
            )
        response = request.execute()


        return {"response":response}


    def update_video(self):

        yt_credentials = coll.find({},{'_id':0})
        for yt_cred in yt_credentials:
            credentials=yt_cred

        print(credentials)
        credentials = google.oauth2.credentials.Credentials(
            **credentials)
        youtube = build(
            settings.API_SERVICE_NAME, settings.API_VERSION, credentials=credentials)
        
        insert_request = youtube.captions().insert(
            part="snippet",
            sync=True,
        body={
          "snippet": {
            "language": "en",
            "name": "Eng2",
            "videoId": "H-CH0ept6dk",

          }

        },

        # TODO: For this request to work, you must replace "YOUR_FILE"
        #       with a pointer to the actual file you are uploading.
        media_body=MediaFileUpload("caption1.txt")
    )

        response = insert_request.execute()

        return {"response":response}




    def get_video_status_by_project_id(self,project_id):

        proj_obj = self.get_by_id(project_id)

        if proj_obj:
            video_id=proj_obj.file_url.split('watch?v=')[1]   #split url and get video_id at last index of array
            print(video_id)

            if proj_obj.file_status["status"]!="completed":
                # print(json.dumps(resp))
                resp=self.get_video_status_by_video_id(video_id)
                if "processingDetails" in resp:
                    if resp["processingDetails"]["processingStatus"]=="succeeded":
                       proj_obj.file_status={"status":"completed"}
                       proj_obj.save()
                else:
                    proj_obj.file_status={"status":"failed","message":resp["error"]}
                    proj_obj.save()
                    raise MVException(resp["error"])

            return proj_obj


    def get_video_status_by_video_id(self,video_id):

        """ This function defines to getting an uploaded video status
            by using video_id
        """
        yt_credentials = coll.find({},{'_id':0})
        for yt_cred in yt_credentials:
            credentials=yt_cred

        print(credentials)
        credentials = google.oauth2.credentials.Credentials(
            **credentials)
        youtube = build(
            settings.API_SERVICE_NAME, settings.API_VERSION, credentials=credentials,cache_discovery=False)

        # try:
        request = youtube.videos().list(
        part="status,processingDetails"
,           id = video_id
        )
        response=request.execute()
        print(response)
        if len(response["items"]) > 0:
            #success
            return response["items"][0]
        else:
            return {"error":"video may be failed uploading due to duplicate,copyright etc.,"}
 

    def download_youtube_video(self,link,project_id,file_type):
        try:
            print("im download",file_type)
            if file_type=='video':
                file_name = project_id+".mp4"
                prefix_folder = settings.BASE_MEDIA_PATH
                print("Im herefh",os.getcwd())
                if not os.path.exists(prefix_folder):
                    print("folder not found")
                    os.mkdir(prefix_folder)
                file_name = project_id
                try:
                    yt = yt_download(link,prefix_folder+file_name+".mp4")
                except:
                    yt = yt_download(link,prefix_folder+file_name+".mp4")
                # except RuntimeError:
                #     yt = yt_download(link,prefix_folder+file_name+".mp4")
                # except TypeError:
                #     yt = yt_download(link,prefix_folder+file_name+".mp4")
                # except NameError:
                #     yt = yt_download(link,prefix_folder+file_name+".mp4")
                # except ValueError:
                #     yt = yt_download(link,prefix_folder+file_name+".mp4")
                # print("im check the path",os.path.isfile('./'+prefix_folder+file_name+".mp4"))
                bucket = settings.VIDEO_BUCKET_NAME
                file_path=prefix_folder+file_name+".mp4"
                upld_s3 =  upload_to_s3.upload_file(file_path,bucket,file_name+".mp4")
                # print("im upld",upld_s3)
                if upld_s3==True :
                    #TODO does file exist means return True else False
                    if os.path.isfile(file_path) and os.access(file_path, os.R_OK):
                        return file_path
                    else:
                        return False
                # upld_gcp = ''
                # if scenario == 'search_for_logo_intervention':
                #     upld_gcp = upload_to_gcp.upload_blob(file_path,bucket,file_name+".mp4")
                # elif scenario=='search_for_numerosity_principle' or scenario=='search_for_overlay_text_background' or scenario=='search_for_women_apart_not_in_close_physicalproximity' or scenario=='search_for_images_on_right_words_to_left' or scenario=='search_for_text_on_face' or scenario=='search_for_more_than_two_people_in_close_proximity' or scenario=='search_for_more_than_two_consistent_characters' or scenario=='search_for_eyes_contact' or scenario == 'search_for_lack_of_family_interactions' or scenario=='search_for_variation_in_terrain' or scenario=='search_for_body_parts' or scenario=='search_for_text_relative_position': #or scenario == 'search_for_overlay_text_background' or scenario=='search_for_numerosity_principle'
                #     print("im scenario for voe",scenario)
                #     upld_s3 =  upload_to_s3.upload_file(file_path,bucket,file_name+".mp4")
                #     print("im checkingh",file_path,upld_s3)
                #     print("im upld",upld_s3)
                # else:
                #     # upld_gcp = False
                #     upld_s3 = False
                # if upld_gcp == True or upld_s3==True :
                #     #TODO does file exist means return True else False
                #     if os.path.isfile(file_path) and os.access(file_path, os.R_OK):
                #         return file_path
                #     else:
                #         return False
        except:
                print("im here")

    def upload_image(self,ufile,filename):
        from PIL import Image
        im = Image.fromarray(ufile)
        print(filename)
        im.save(settings.MEDIA_PATH+"/"+filename, filename)
        return settings.MEDIA_PATH+"/"+filename

    def extract_image_from_video(self,video_file,ref_id):
        print("##########",BASE_MEDIA_PATH+ref_id+".mp4")
        vidcap = cv2.VideoCapture(BASE_MEDIA_PATH+"test_pledge.mp4")
        success,image = vidcap.read()
        print(success,image)
        count = 0
        
        while success:
            # vidcap.set(cv2.CAP_PROP_POS_MSEC,(count*1000))    # if anyone does not want to extract every frame but wants to extract frame every one second
            success,image = vidcap.read()
            print ('Read a new frame: ', success)
            if vidcap.get(cv2.CAP_PROP_POS_MSEC)%500==0:
                if success:###Tabs
                    upld_img = self.upload_image(image,ref_id+"_frame%d_%d.jpg" % (count,vidcap.get(cv2.CAP_PROP_POS_MSEC)))
                    file_obj=ProjectFile()
                    file_obj.db_id = uuid.uuid4().hex
                    file_obj.ref_id = ref_id
                    file_obj.image_url =upld_img
                    file_obj.created_at = datetime.datetime.now()
                    file_obj.updated_at = datetime.datetime.now()
                    file_obj.save()
            # cv2.imwrite( path + "frame%d.jpg" % count, image)     # save frame as JPEG file
            count = count + 1


    def time_to_label(self,project_video_obj,timestamps):
        positive_impacts={}
        s=eval(project_video_obj.video_analysis)
        # print("^^^^^^^^^",s)
        for t in timestamps:
            if str(t) in s:
                for k in s[str(t)]:
                    if str(t) in positive_impacts:
                        positive_impacts[str(t)].append(k)
                    else:
                        positive_impacts[str(t)]=[k]
        return positive_impacts


    def get_total_impacts(self,impacts):
        # count = 0
        # for imp in impacts:
        #     count+=len(imp["impact_results"])
        count=0
        for imp in impacts:
            count+=imp["total_count"]

        # print(count)
        return count

    def generate_impact_and_violations(self,ref_id,scenario):

        proj_obj=self.get_by_id(ref_id)
        if proj_obj:
            yt_download = self.download_youtube_video(proj_obj.file_url,ref_id,scenario)
        # # yt_download = self.download_youtube_video("dfd",ref_id)
        if yt_download:
            print("video downloaded")
            # print(yt_download)
            video_file=yt_download
            # return {"message":"download success"}
            # TODO upload video to s3 bucket for label detection and then delete the file
            # video_file= os.getcwd()+"/mv_nalign"+settings.MEDIA_PATH+"/"+proj_obj.db_id+".mp4"
            # video_file= settings.BASE_MEDIA_PATH+"s3_test.mp4"
            # res = self.extract_image_from_video(video_file,proj_obj.db_id)


        #     pass

        #calculate bounding boxes

        neuro = NeuroAnalysis.objects(ref_id=ref_id).first()
        if not neuro:
            print("Not analysis found")
            neuro=NeuroAnalysis()
            neuro.db_id=uuid.uuid4().hex
            neuro.ref_id=ref_id
            neuro.video_name=video_file.split('/')[-1]
            neuro.video_data={}
            neuro.video_analysis={}
            neuro.text_data={}
            neuro.text_analysis={}
            neuro.positive_impacts = {}
            neuro.negative_impacts = {}
            neuro.final_positive_impacts = []
            neuro.final_negative_impacts = []
            neuro.save()
        print("Analysis metadata added")
        if not (neuro.video_data and neuro.video_analysis and neuro.text_data and neuro.text_analysis):
            # if not (neuro.video_data and neuro.video_analysis):
            vid_analysis_res = analysis.analyze_video(neuro,neuro.video_name)
            neuro.video_data=vid_analysis_res["video_data"]
            neuro.video_analysis=vid_analysis_res["video_analysis"]
            neuro.save()
            print("Video analysis done")
        # i=analysis.calculateImpact(neuro)
        # if not (neuro.text_data and neuro.text_analysis):
            text_analysis_res = analysis.analyze_text(neuro,neuro.video_name)
            neuro.text_data=text_analysis_res["text_data"]
            neuro.text_analysis=text_analysis_res["text_analysis"]
            neuro.save()
            print("Text analysis done")

        # calculate impact

        #POSITVE IMPACT -SINGLE PERSON IN AN IMAGE
        impacts_obj = []
        if not neuro.positive_impacts:
            print("initiated - POSITVE IMPACT -SINGLE PERSON IN AN IMAGE ")
            person_positive_impacts =  analysis.positive_impact_person(neuro)
            #For person impacts we get an timestamp so that it convert time to label
            person_positive_impacts = self.time_to_label(neuro,person_positive_impacts)
            print("person impacts",person_positive_impacts)
            neuro.positive_impacts = []
            if person_positive_impacts:
                print("POSITIVE IMPACTS - PERSON FOUND")
                neuro.positive_impacts.append({"impact_name":"Single person in an image","impacts_results":person_positive_impacts})
            else:
                neuro.positive_impacts.append({"impact_name":"Single person in an image","impacts_results":{}})

                # neuro.save()
            print("initiated - POSITVE IMPACT - BABY ")
            # For baby impacts we get an direct json output
            baby_positive_impacts =  analysis.positive_impact_baby(neuro)
            # print("BABY IMPACTS - RESULT ",baby_positive_impacts)
            if baby_positive_impacts:
                print("POSITIVE IMPACTS - BABY FOUND")
                neuro.positive_impacts.append({"impact_name":"Positive impacts baby","impacts_results":json.loads(baby_positive_impacts)})
            else:
                neuro.positive_impacts.append({"impact_name":"Positive impacts baby","impacts_results":{}})

            print("initiated - NEGATIVE IMPACT - TEXT ON FACE ")
            # For baby impacts we get an direct json output
            text_on_face_obj =  analysis.negative_impact_text_face(neuro)
            print("NEGATIVE IMPACT - TEXT ON FACE - RESULT ",text_on_face_obj)
            if text_on_face_obj:
                print("NEGATIVE IMPACT - TEXT ON FACE FOUND")
                neuro.positive_impacts.append({"impact_name":"Negative impacts text on face","impacts_results":json.loads(text_on_face_obj)})
            else:
                neuro.positive_impacts.append({"impact_name":"Negative impacts text on face","impacts_results":{}})



            # baby_positive_impacts =  analysis.positive_impact_baby(neuro)
            # if baby_positive_impacts:
            #     neuro.positive_impacts.append({"impact_name":"Positive impacts baby","impacts_results":json.loads(baby_positive_impacts)})


                # neuro.save()
            # negative_impacts =  analysis.negative_impact_text_face(neuro)
            # neuro.negative_impacts = negative_impacts
            neuro.save()
            print("Impacts added to the Mongo")
            # i=analysis.calculateImpact(neuro)
        # neuro = NeuroAnalysis.objects(ref_id=ref_id).first()
        timestamp = set()
        if neuro:
            for impacts in neuro.positive_impacts:

                for k in impacts["impacts_results"]:
                    print("key is ",type(k))
                    timestamp.add(k)

            # for d in neuro.negative_impacts:
            #     timestamp.add(d["timestamp"])

        vidcap = cv2.VideoCapture(BASE_MEDIA_PATH+neuro.video_name)

        # vidcap = cv2.VideoCapture(video_file)
        url = AMAZON_BASE_URL
        bucket = settings.IMAGE_BUCKET_NAME
        # label = sorted(list(label1)+list(label2))
        # file_objects = []
        print(timestamp)
        for time in timestamp:
            vidcap.set(cv2.CAP_PROP_POS_MSEC,int(time))    # just cut to time msec. position
            success,image = vidcap.read()
            f_obj = ProjectFile.objects().filter(ref_id=ref_id,image_timestamp=time).first()
            # print("file exist or not",f_obj)
            if not f_obj:
                print("initialize")
                if success:
                    cv2.imwrite(BASE_MEDIA_PATH+ref_id+"_frame_%s.jpg" % (time),image)
                    upload_to_s3.upload_file(BASE_MEDIA_PATH+ref_id+"_frame_%s.jpg" % (time),bucket,ref_id+"_frame_%s.jpg" % (time))
                    file_obj=ProjectFile()
                    file_obj.db_id = uuid.uuid4().hex
                    file_obj.ref_id = ref_id
                    file_obj.image_url =url+ref_id+"_frame_%s.jpg"%(time)
                    file_obj.image_timestamp=time
                    file_obj.created_at = datetime.datetime.now()
                    file_obj.updated_at = datetime.datetime.now()
                    file_obj.save()
        # impacts["positive_impacts"] = []
        print("im here neuro",neuro.positive_impacts)

        f_obj = ProjectFile.objects().filter(ref_id=ref_id)
        impacts = []
        for v in neuro.positive_impacts:
            impacts_obj = {}
            impacts_obj["impact_name"] = v["impact_name"]
            print("impact name is",v["impact_name"])
            bounding = []
            for s in v["impacts_results"]:
                imp_res = v["impacts_results"][s]
                inner_impacts = {}

                # f_obj = ProjectFile.objects().filter(ref_id=ref_id,image_timestamp=str(v["timestamp"])).first()
                # print(")))))))))))))))))",f_obj)
                for fl in f_obj:
                    if fl.image_timestamp == s:
                        fl_obj=fl
                        break

                if fl_obj:
                #its for single person in an image
                    inner_impacts["image_url"] =fl_obj.image_url
                    inner_impacts["bounding_results"] = imp_res
                    bounding.append(inner_impacts)
            impacts_obj["impact_results"] = bounding
            impacts.append(impacts_obj)

        neuro.final_positive_impacts = impacts
        neuro.save()

        if neuro.final_positive_impacts:
            proj_obj = self.get_by_id(ref_id)
            proj_obj.impacts_status = {"status":"completed"}
            print("impacts count",neuro.final_positive_impacts)
            proj_obj.impacts_count =  self.get_total_impacts(neuro.final_positive_impacts)
            print("imimpach vound",self.get_total_impacts(neuro.final_positive_impacts))
            proj_obj.save()

        print("IMPACTS PROCESS COMPLETED")

        return True

    def calculate_overlap(self,co_ordinates1,co_ordinates2):
        if (co_ordinates1['x2'] < co_ordinates2['x1']) and (co_ordinates1['y2'] < co_ordinates2['y1']):
            #not overlap
            return True
        #overlap
        return False

    def check_impacts_status(self,ref_id):

        proj_obj=self.get_by_id(ref_id)
        neuro = NeuroAnalysis.objects(ref_id=ref_id).first()
        result ={}
        if neuro:
            print(not ( neuro.text_analysis and neuro.text_data))
            if not (neuro.video_analysis and neuro.video_data):
                # print("dfdlkjf")
                v_an=analysis.analyseVideo(neuro)
            if  not ( neuro.text_analysis and neuro.text_data):
                t_an=analysis.analyseText(neuro)

            if not ( neuro.video_data and neuro.text_data and neuro.video_analysis and neuro.text_analysis):
                return {"impacts_status":{"status":"processing"}}
            else:


                if proj_obj.impacts_status=={"status":"processing"}:

                    if not neuro.positive_impacts:
                        i=analysis.calculateImpact(neuro)
                    neuro = NeuroAnalysis.objects(ref_id=ref_id).first()
                    timestamp = set()
                    if neuro:
                        for k in neuro.positive_impacts:
                            timestamp.add(k["timestamp"])

                        for d in neuro.negative_impacts:
                            timestamp.add(d["timestamp"])


                        vidcap = cv2.VideoCapture(BASE_MEDIA_PATH+neuro.video_name)

                        # vidcap = cv2.VideoCapture(video_file)
                        url = AMAZON_BASE_URL
                        bucket = settings.IMAGE_BUCKET_NAME
                        # label = sorted(list(label1)+list(label2))
                        # file_objects = []
                        print(timestamp)
                        for time in timestamp:
                            vidcap.set(cv2.CAP_PROP_POS_MSEC,time)    # just cut to time msec. position
                            success,image = vidcap.read()
                            f_obj = ProjectFile.objects().filter(ref_id=ref_id,image_timestamp=str(time)).first()
                            print("initialize result",f_obj)
                            if not f_obj:
                                print("initialize")
                                if success:
                                    cv2.imwrite(BASE_MEDIA_PATH+ref_id+"_frame_%d.jpg" % (time),image)
                                    upload_to_s3.upload_file(BASE_MEDIA_PATH+ref_id+"_frame_%d.jpg" % (time),bucket,ref_id+"_frame_%d.jpg" % (time))

                                    file_obj=ProjectFile()
                                    file_obj.db_id = uuid.uuid4().hex
                                    file_obj.ref_id = ref_id
                                    file_obj.image_url =url+ref_id+"_frame_%d.jpg"%(time)
                                    file_obj.image_timestamp=str(time)


                                    file_obj.created_at = datetime.datetime.now()
                                    file_obj.updated_at = datetime.datetime.now()
                                    file_obj.save()

                        impacts = {}
                        impacts["positive_impacts"] = []

                        print(neuro.positive_impacts)
                        for v in neuro.positive_impacts:
                            pos_impacts = {}
                            f_obj = ProjectFile.objects().filter(ref_id=ref_id,image_timestamp=str(v["timestamp"])).first()
                            print(")))))))))))))))))",f_obj)
                            if f_obj:
                            #its for single person in an image
                                print(v)
                                pos_impacts["impact_name"] = "single person in an image"
                                pos_impacts["image_url"] =f_obj.image_url
                                pos_impacts["object_detection"] = v
                                pos_impacts["text_detection"] =[]

                                impacts["positive_impacts"].append(pos_impacts)


                    neuro.final_positive_impacts =impacts
                    neuro.save()
                    if neuro.final_positive_impacts:
                        proj_obj.impacts_status = {"status":"completed"}
                        proj_obj.save()
                        result["impacts_status"] = "completed"
                        result["impacts"] = impacts

                else:
                    neuro = NeuroAnalysis.objects(ref_id=ref_id).first()
                    print(neuro.final_positive_impacts)
                    result["impacts_status"] = {"status":"completed"}
                    impacts = neuro.final_positive_impacts
                    result["impacts"] = impacts

        else:
            return {"impacts_status":{"status":"processing"}}



        return result

    def get_neuro_excel(self):
        neuro_obj = NeuroAnalysis.objects({})
        # neuro_obj = NeuroAnalysis.objects(ref_id=ref_id).first()
        # print("im neruo objec",neuro_obj)
        # print(neuro_obj)
        if neuro_obj:
            return neuro_obj
        return False

    def get_neuro_by_ref_id(self,ref_id):
        neuro_obj = NeuroAnalysis.objects(ref_id=ref_id).first()
        # print("im neruo objec",neuro_obj)
        if neuro_obj:
            return neuro_obj
        return False

    def get_impacts_based_on_keyword(self,ref_id,keyword,data=None):
        neuro_obj = self.get_neuro_by_ref_id(ref_id)
        resp = []
        if neuro_obj:
            #Again corner case
            proj_obj=self.get_by_id(ref_id)
            print(proj_obj)
            print(keyword.lower().replace(' ','_'))
            kwd=keyword.lower().replace(' ','_')
            #corner_case
            # kwd_alias={'more_than_two_consistent_characters':'two_consistent_characters','women_together':"woman_together"}
            # if kwd in kwd_alias:
            # 	kwd=kwd_alias[kwd]
            print(kwd)
            if  kwd in neuro_obj:
                print("Im getting neuro",neuro_obj[kwd]["results"])
                if len(neuro_obj[kwd]["results"])>0:
                    resp=neuro_obj[kwd]["results"]
                else:
                    #corner case - when no results found for that impact/violations, would like to show just image
                    if proj_obj.file_type=="image":
                        resp= [{"image_url":proj_obj.file_url,'bounding_results':[]}]
        return resp

    def get_captions(self,id):
        proj_obj = self.get_by_id(id)
        if proj_obj.captions == DEFAULT_CAPTIONS_STRING:
            link = proj_obj.file_url
            if "www.youtube.com" in link:
                print("Youtube link found")
                source = yt_download(link)
                en_caption = source.captions.get_by_language_code('en')
                en_caption_convert_to_srt =(en_caption.generate_srt_captions())
                json_string = json.dumps(en_caption_convert_to_srt)
                if en_caption_convert_to_srt:
                    proj_obj.captions=json_string
                    proj_obj.save()
                    print("Captions Added To Mongo")

        return {"data":proj_obj.captions}


    def calculate_inner_impacts(self,results):

        b_count=0
        for res in results:
            if len(res["bounding_results"])>0:
                b_count+=1

        return b_count


    def get_feedback_violation_flag(self,ref_id,violation_name):
        fdback=Feedback.objects(ref_id=ref_id,violation_name=violation_name).first()
        if fdback:
            print(fdback.is_violation)
            print("violation value",fdback.is_violation)
            return fdback.is_violation
        else:
            return False

    def get_screen_count(self,ref_id):
        try:
            url = "https://machine-vantage-inc-images.s3.us-east-2.amazonaws.com/"
            filepath = BASE_MEDIA_PATH+ref_id+'.mp4'
            s3_client = boto3.client('s3')
            storing_screenplay = []
            cap = cv2.VideoCapture(filepath)
            count = 0
            success = True
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            while success:
                success,image = cap.read()
                if success:
                    # response = s3_client.upload_file(file_name, bucket, object_name)
                    cv2.imwrite(BASE_MEDIA_PATH+ref_id+'_stryframe{:d}.jpg'.format(count), image)
                    image_string = cv2.imencode('.jpg', image)[1].tostring()
                    s3_client.put_object(Bucket="machine-vantage-inc-images", Key = ref_id+'_stryframe{:d}.jpg'.format(count), Body=image_string)
                    # s3_client.upload_file(url,"machine-vantage-inc-images",ref_id+'_stryframe{:d}.jpg'.format(count))
                    storing_screenplay.append(url+ref_id+'_stryframe{:d}.jpg'.format(count))
                    # print(storing_screenplay)
                    count += 30 # i.e. at 30 fps, this advances one second
                    cap.set(1, count)
                else:
                    cap.release()
                    break
                count+=1
            return storing_screenplay
        except KeyError as e:
            print(e)
            
        # print("i mhimage",image)
    def get_progress_bar(self,ref_id):
        
            # neuro_obj = self.get_neuro_by_ref_id(ref_id)    
            # print(neuro_obj)
        neuro_obj = self.get_neuro_by_ref_id(ref_id)
        # print(neuro_obj)
        # d= 
        resp = []
        # d   = 12
        if neuro_obj:
            # principle_count=''
            if 'no_eyes_contact' in neuro_obj:
                resp.append({'processMsg':'P1'})
            if 'more_than_two_people_in_close_proximity' in neuro_obj:
                resp.append({'processMsg':'P2'})
            if 'lack_of_family_interactions' in neuro_obj:
                resp.append({'processMsg':'P3'})
            if 'images_on_right_words_to_left' in neuro_obj:
                resp.append({'processMsg':'P4'})
            if 'text_on_face' in neuro_obj:
                resp.append({'processMsg':'P5'})
            if 'more_than_three_visual_clusters' in neuro_obj:
                resp.append({'processMsg':'P6'})
            if 'more_than_two_people_in_close_proximity' in neuro_obj:
                resp.append({'processMsg':'P7'})
            if 'women_apart_not_in_close_physicalproximity' in neuro_obj:
                resp.append({'processMsg':'P8'})
            if 'overlay_text_background' in neuro_obj:
                resp.append({'processMsg':'P9'})
            if 'variation_in_terrain' in neuro_obj:
                resp.append({'processMsg':'P10'})
            if 'body_part_isolation' in neuro_obj:
                resp.append({'processMsg':'P11'})
            if 'interrupt_flow_storyline' in neuro_obj:
                resp.append({'processMsg':'P12'})
            # resp_1 = json.dumps(resp)
            # json_ob = json.loads(resp_1)                        
            # json_ob.update({'a':'a'})
        return {'data':resp,'principle_cnt':12}

    def get_impacts_count(self,ref_id):
        # print("",ref_id)
        neuro_obj = self.get_neuro_by_ref_id(ref_id)
        print("im neuro",neuro_obj)
        # print("im object",neuro_obj)
        neuros = []
        if neuro_obj:
            ###DB update 
            ### Added new Parameter as Pname
            if "interrupt_flow_storyline" in neuro_obj:
                impact_details = {}
                impact_details["impact_name"]="Interrupt flow storyline"
                impact_details["principle_name"] = "Intervening product shots that interrupt the flow of the visual storyline"
                impact_details["total_count"]= len(neuro_obj.interrupt_flow_storyline["results"])
                impact_details["is_violation"]=self.get_feedback_violation_flag(ref_id,impact_details["impact_name"])
                neuros.append(impact_details)
            if "women_apart_not_in_close_physicalproximity" in neuro_obj:
                impact_details = {}
                impact_details["impact_name"]="Women apart not in close physicalproximity"
                impact_details["principle_name"] = "Women apart, not in close physical proximity"
                impact_details["total_count"]= len(neuro_obj.women_apart_not_in_close_physicalproximity["results"])
                impact_details["is_violation"]=self.get_feedback_violation_flag(ref_id,impact_details["impact_name"])
                neuros.append(impact_details)
            if "more_than_two_people_in_close_proximity" in neuro_obj:
                impact_details = {}
                impact_details["impact_name"]="More than two people in close proximity"
                impact_details["principle_name"] = "More than two people in close proximity"
                impact_details["total_count"]= len(neuro_obj.more_than_two_people_in_close_proximity["results"])
                impact_details["is_violation"]=self.get_feedback_violation_flag(ref_id,impact_details["impact_name"])
                neuros.append(impact_details)
            if "more_than_two_consistent_characters" in neuro_obj:
                impact_details = {}
                impact_details["impact_name"]="More than two consistent characters"
                impact_details["principle_name"] = "More than two consistent characters in ad"
                impact_details["total_count"]= len(neuro_obj.more_than_two_consistent_characters["results"])
                impact_details["is_violation"]=self.get_feedback_violation_flag(ref_id,impact_details["impact_name"])
                neuros.append(impact_details)
            if "lack_of_family_interactions" in neuro_obj:
                impact_details = {}
                impact_details["impact_name"]="Lack of Family interactions"
                impact_details["principle_name"] = "Lack of family interactions / baby images"
                impact_details["total_count"]= len(neuro_obj.lack_of_family_interactions["results"])
                impact_details["is_violation"]=self.get_feedback_violation_flag(ref_id,impact_details["impact_name"])
                neuros.append(impact_details)
            if "text_on_face" in neuro_obj:
                impact_details = {}
                impact_details["impact_name"]="Text on face"
                impact_details["principle_name"] = "Overlay of text on face"
                impact_details["total_count"]= len(neuro_obj.text_on_face["results"])
                impact_details["is_violation"]=self.get_feedback_violation_flag(ref_id,impact_details["impact_name"])
                neuros.append(impact_details)
            if "images_on_right_words_to_left" in neuro_obj:
                impact_details = {}
                impact_details["impact_name"]="images on right words to left"
                impact_details["principle_name"] = "Images on right, words to left"
                impact_details["total_count"]= len(neuro_obj.images_on_right_words_to_left["results"])
                impact_details["is_violation"]=self.get_feedback_violation_flag(ref_id,impact_details["impact_name"])
                neuros.append(impact_details)
            if "no_eyes_contact" in neuro_obj:
                impact_details = {}
                impact_details["impact_name"]="no eyes contact"
                impact_details["principle_name"] = "Character does not make eye contact"
                impact_details["total_count"]= len(neuro_obj.no_eyes_contact["results"])
                impact_details["is_violation"]=self.get_feedback_violation_flag(ref_id,impact_details["impact_name"])
                neuros.append(impact_details)
            if "more_than_three_visual_clusters" in neuro_obj:
                impact_details = {}
                impact_details["impact_name"]="More than three visual clusters"
                impact_details["principle_name"] = "More than 3 visual clusters"
                impact_details["total_count"]= len(neuro_obj.more_than_three_visual_clusters["results"])
                impact_details["is_violation"]=self.get_feedback_violation_flag(ref_id,impact_details["impact_name"])
                neuros.append(impact_details)
            if "overlay_text_background" in neuro_obj:
                # print("im neuro1",len(neuro_obj.overlay_text_background["results"]))
                impact_details = {}
                impact_details["impact_name"]="Overlay Text Background"
                impact_details["principle_name"] = "Overlay of text on background / image / illustration"
                impact_details["total_count"]= len(neuro_obj.overlay_text_background["results"])
                impact_details["is_violation"]=self.get_feedback_violation_flag(ref_id,impact_details["impact_name"])
                neuros.append(impact_details)
            if "variation_in_terrain" in neuro_obj:
                # print("im neuro1",len(neuro_obj.variation_in_terrain["results"]))
                impact_details = {}
                impact_details["impact_name"]="Variation in Terrain"
                impact_details["principle_name"] = "Variations in terrain – change of context within which the story unfolds"
                impact_details["total_count"]= len(neuro_obj.variation_in_terrain["results"])
                impact_details["is_violation"]=self.get_feedback_violation_flag(ref_id,impact_details["impact_name"])
                neuros.append(impact_details)
            if "body_part_isolation" in neuro_obj:
                impact_details = {}
                impact_details["impact_name"]="Body part isolation"
                impact_details["principle_name"] = "Chopped faces / body parts or body parts in isolation"
                impact_details["total_count"]= len(neuro_obj.body_part_isolation["results"])
                impact_details["is_violation"]=self.get_feedback_violation_flag(ref_id,impact_details["impact_name"])
                neuros.append(impact_details)

        print("im neuro",neuros)
        # current_date_and_time = datetime.datetime.now()
        # print(current_date_and_time,neuros)
        return sorted(neuros,key=lambda k:k["total_count"],reverse=True)
    
    def get_excel(self):
        # print("",ref_id)
        neuro_obj = self.get_neuro_excel()
        # print("im object",neuro_obj)
        current_date = datetime.datetime.now().date()
        print("curren",current_date)
        export_excelsheet_name = 'export_excel_'+str(current_date)+'.csv'
        print(export_excelsheet_name)
        excel_sheet = BASE_MEDIA_PATH+export_excelsheet_name
        print(excel_sheet)
        neuros = []
        with open(excel_sheet,'w') as f1:
            writer=csv.writer(f1, delimiter='\t',lineterminator='\n',)
            writer.writerow(['Title',
            'Updated_Date',
            'File_Type',
            'Violations Count',
            'P1 Intervening product shots that interrupt the flow of the visual storyline',	
            'P2 More than 3 visual clusters',
            'P3 Variations in terrain change of context within which the story unfolds',	
            'P4 Images on right words to left',
            'P5 Character does not make makes eye contact with viewer',	
            'P6 More than two consistent characters in ad',
            'P7 More than two people in close proximity',	
            'P8 Women apart not in close physical proximity',
            'P9 Overlay of text on face',
            'P10 Lack of family interactions / baby images',	
            'P11 Overlay of text on background / image / illustration',
            'P12 Chopped faces / body parts or body parts in isolation'])
            for i in neuro_obj:
                print(i.violation_status)
                total_violation_count = 0
                if i.violation_status == 'Completed':
                #print(i.interrupt_flow_storyline['results'])            
                    if 'interrupt_flow_storyline' in i:
                        count_interrupt_flow_storyline = len(i.interrupt_flow_storyline['results'])
                        total_violation_count = total_violation_count+count_interrupt_flow_storyline
                    else:
                        count_interrupt_flow_storyline = 0

                    if 'variation_in_terrain' in i:
                        count_variation_in_terrain = len(i.variation_in_terrain['results'])
                        total_violation_count = total_violation_count+count_variation_in_terrain
                    else:
                        count_variation_in_terrain = 0
                    
                    if 'more_than_two_consistent_characters' in i:
                        count_more_than_two_consistent_characters = len(i.more_than_two_consistent_characters['results'])
                        total_violation_count = total_violation_count+count_more_than_two_consistent_characters
                    else:
                        count_more_than_two_consistent_characters = 0
                    
                    if 'lack_of_family_interactions' in i:
                        count_lack_of_family_interactions = len(i.lack_of_family_interactions['results'])
                        total_violation_count = total_violation_count+count_lack_of_family_interactions
                    else:
                        count_lack_of_family_interactions = 0
                    
                    if 'text_on_face' in i:
                        count_text_on_face = len(i.text_on_face['results'])
                        total_violation_count = total_violation_count+count_text_on_face
                    else:
                        count_text_on_face = 0
                    
                    if 'images_on_right_words_to_left' in i:
                        count_images_on_right_words_to_left = len(i.images_on_right_words_to_left['results'])
                        total_violation_count = total_violation_count+count_images_on_right_words_to_left
                    else:
                        count_images_on_right_words_to_left = 0
                    
                    if 'no_eyes_contact' in i:
                        count_no_eyes_contact = len(i.no_eyes_contact['results'])
                        total_violation_count = total_violation_count+count_no_eyes_contact
                    else:
                        count_no_eyes_contact = 0
                    
                    if 'more_than_three_visual_clusters' in i:
                        count_more_than_three_visual_clusters = len(i.more_than_three_visual_clusters['results'])
                        total_violation_count = total_violation_count+count_more_than_three_visual_clusters
                    else:
                        count_more_than_three_visual_clusters = 0
                    
                    if 'more_than_two_people_in_close_proximity' in i:
                        count_more_than_two_people_in_close_proximity = len(i.more_than_two_people_in_close_proximity['results'])
                        total_violation_count = total_violation_count+count_more_than_two_people_in_close_proximity
                    else:
                        count_more_than_two_people_in_close_proximity = 0
                    
                    if 'women_apart_not_in_close_physicalproximity' in i:
                        count_women_apart_not_in_close_physicalproximity = len(i.women_apart_not_in_close_physicalproximity['results'])
                        total_violation_count = total_violation_count+count_women_apart_not_in_close_physicalproximity
                    else:
                        count_women_apart_not_in_close_physicalproximity = 0
                    
                    if 'overlay_text_background' in i:
                        count_overlay_text_background = len(i.overlay_text_background['results'])
                        total_violation_count = total_violation_count+count_overlay_text_background
                    else:
                        count_overlay_text_background = 0
                    
                    if 'body_part_isolation' in i:
                        count_body_part_isolation = len(i.body_part_isolation['results'])
                        total_violation_count = total_violation_count+count_body_part_isolation
                    else:
                        count_body_part_isolation = 0

                    writer.writerow([i.title_name,
                    i.created_at,
                    i.file_type,
                    total_violation_count,
                    count_interrupt_flow_storyline,
                    count_more_than_three_visual_clusters,
                    count_variation_in_terrain,
                    count_images_on_right_words_to_left,
                    count_no_eyes_contact,
                    count_more_than_two_consistent_characters,
                    count_more_than_two_people_in_close_proximity,
                    count_women_apart_not_in_close_physicalproximity,
                    count_interrupt_flow_storyline,
                    count_lack_of_family_interactions,
                    count_overlay_text_background,
                    count_body_part_isolation
                    ])
                    print("total_violation_count",total_violation_count)
        value = upload_to_s3.upload_file(excel_sheet,'machine-vantage-inc-images',export_excelsheet_name+'.xls')
        print(value)
        if value == True:
            return 'https://machine-vantage-inc-images.s3.us-east-2.amazonaws.com/'+export_excelsheet_name+'.xls'

    def covert_keys_to_lowercase(self,boundingboxes):
        s={}
        for key,value in boundingboxes.items():
            s[key.lower()] = value

        return s


    def upload_image_based_on_timestamp(self,time,ref_id):
        neuro=NeuroAnalysis.objects(ref_id=ref_id).first()
        if neuro :
            print(neuro.file_name)
            print("im neruro interain")
            vidcap = cv2.VideoCapture("mv_nalign/media/"+neuro.file_name)   #+neuro.file_name)
                # vidcap = cv2.VideoCapture(video_file)
            url = AMAZON_BASE_URL
            bucket = settings.IMAGE_BUCKET_NAME
            vidcap.set(cv2.CAP_PROP_POS_MSEC,int(time))    # just cut to time msec. position
            # vidcap.set(cv2.CAP_PROP_FPS,int(time)) 
            # cv2.cv2.CAP_PROP_FPS 
            success = True
            success,image = vidcap.read()
            print("im success", success)
            print("im image", image)
            f_obj = ProjectFile.objects().filter(ref_id=ref_id,image_timestamp=time).first()
            print("file exist or not",f_obj)
            if not f_obj:
                print("initialize")
                if success:
                    cv2.imwrite("mv_nalign/media/"+ref_id+"_frame_%s.jpg" % (time),image)
                    upload_to_s3.upload_file("mv_nalign/media/"+ref_id+"_frame_%s.jpg" % (time),bucket,ref_id+"_frame_%s.jpg" % (time))
                    file_obj=ProjectFile()
                    file_obj.db_id = uuid.uuid4().hex
                    file_obj.ref_id = ref_id
                    file_obj.image_url =url+ref_id+"_frame_%s.jpg"%(time)
                    file_obj.image_timestamp=time
                    file_obj.created_at = datetime.datetime.now()
                    file_obj.updated_at = datetime.datetime.now()
                    file_obj.save()
                    return True
        return False

    def upload_image_based_on_timestamp_gcp(self,time,ref_id):
        # print(time)
        # print(ref_id)
        # print("im gcp")
        neuro=NeuroAnalysis.objects(ref_id=ref_id).first()
        if neuro :
            vidcap = cv2.VideoCapture(BASE_MEDIA_PATH+neuro.file_name)
            
            bucket = settings.IMAGE_BUCKET_NAME
                # vidcap = cv2.VideoCapture(video_file)
            url = "https://storage.googleapis.com/%s/%s" % (bucket, neuro.file_name)
            vidcap.set(cv2.CAP_PROP_POS_MSEC,int(time))    # just cut to time msec. position
            success,image = vidcap.read()
            f_obj = ProjectFile.objects().filter(ref_id=ref_id,image_timestamp=time).first()
            # print("file exist or not",f_obj)
            if not f_obj:
                print("initialize")
                if success:
                    cv2.imwrite(BASE_MEDIA_PATH+ref_id+"_frame_%s.jpg" % (time),image)
                    upload_to_gcp.upload_blob(BASE_MEDIA_PATH+ref_id+"_frame_%s.jpg" % (time),'machine-vantage-inc-image',ref_id+"_frame_%s.jpg" % (time))
                    file_obj=ProjectFile()
                    file_obj.db_id = uuid.uuid4().hex
                    file_obj.ref_id = ref_id
                    # print("im here",url+ref_id+"_frame_%s.jpg"%(time))
                    file_obj.image_url =url+ref_id+"_frame_%s.jpg"%(time)
                    file_obj.image_timestamp=str(time)
                    file_obj.created_at = datetime.datetime.now()
                    file_obj.updated_at = datetime.datetime.now()
                    file_obj.save()
                    return True
        return False

    def generate_end_impacts_results_for_video_terrain(self,results,ref_id,file_url,analyzer_type=None,scenario=None):
        bounding = []
        url = AMAZON_BASE_URL
        if results['ViolationFound'] == True:
            for time in results['Results']:
                for timestamp in time:
                    image_url =url+ref_id+"_frame_%s.jpg"%(str(time['Timestamp']))
                    res=self.upload_image_based_on_timestamp(str(time['Timestamp']),ref_id)
                    bounding.append({'image_url':image_url,'Timestamp':str(time['Timestamp']),'bounding_results':[]})
        return bounding

    def generate_end_impacts_results_for_video_logo(self,results,ref_id,file_url,analyzer_type=None,scenario=None):
        bounding = []
        url = AMAZON_BASE_URL
        if results['ViolationFound'] == True:
            for time in results['Results']:
                for timestamp in time:
                    image_url =url+ref_id+"_frame_%s.jpg"%(str(time['Timestamp']))
                    res=self.upload_image_based_on_timestamp(str(time['Timestamp']),ref_id)
                    bounding.append({'image_url':image_url,'Timestamp':str(time['Timestamp']),'bounding_results':[]})
        return bounding
    
    def generate_end_impacts_results_for_video_body(self,results,ref_id,file_url,file_type,analyzer_type=None,scenario=None):
        url = AMAZON_BASE_URL
        impacts=[]
        if file_type == 'image':
            for value in results['Results']:
                if value['ViolationFound'] == True:
                    image_url =url+ref_id+"_frame_%s.jpg"%(str('0'))
                    res=self.upload_image_based_on_timestamp(str('0'),ref_id)
                    impacts.append({'principle':'p11','image_url':image_url,'bounding_results':value['BoundingBox']})
        if file_type == 'video':
            for value in results['Results']:
                if value['ViolationFound'] == True:
                    image_url =url+ref_id+"_frame_%s.jpg"%(str(value['Timestamp']))
                    res=self.upload_image_based_on_timestamp(str(value['Timestamp']),ref_id)
                    impacts.append({'principle':'p11','image_url':image_url,'Timestamp':str(value['Timestamp']),'bounding_results':value['Boxes']})
        return impacts
    
    def generate_end_impacts_results_for_video_background(self,results,ref_id,file_url,file_type,analyzer_type=None,scenario=None):
        url = AMAZON_BASE_URL
        impacts=[]
        if file_type == 'image':
            for value in results['Results']:
                if value['ViolationFound'] == True:
                    image_url =url+ref_id+"_frame_%s.jpg"%(str('0'))
                    res=self.upload_image_based_on_timestamp(str('0'),ref_id)
                    impacts.append({'principle':'p11','image_url':image_url,'bounding_results':value['Boxes']})
        if file_type == 'video':
            for value in results['Results']:
                if value['ViolationFound'] == True:
                    image_url =url+ref_id+"_frame_%s.jpg"%(str(value['Timestamp']))
                    res=self.upload_image_based_on_timestamp(str(value['Timestamp']),ref_id)
                    impacts.append({'principle':'p11','image_url':image_url,'Timestamp':str(value['Timestamp']),'bounding_results':value['Boxes']})
        return impacts

    def generate_end_impacts_results_for_video_eye(self,results,ref_id,file_url,file_type,analyzer_type=None,scenario=None):
        url = AMAZON_BASE_URL
        impacts=[]
        if file_type == 'image':
            for value in results['Results']:             
                if value['ViolationFound'] == True:
                    image_url =url+ref_id+"_frame_%s.jpg"%(str('0'))
                    res=self.upload_image_based_on_timestamp(str('0'),ref_id)
                    impacts.append({'image_url':image_url,'bounding_results':value['Boxes']})
        if file_type == 'video':
            for value in results['Results']:
                if value['ViolationFound'] == True:
                    image_url =url+ref_id+"_frame_%s.jpg"%(str(value['Timestamp']))
                    res=self.upload_image_based_on_timestamp(str(value['Timestamp']),ref_id)
                    print("im res",res)
                    impacts.append({'image_url':image_url,'Timestamp':str(value['Timestamp']),'bounding_results':value['Boxes']})
        return impacts
    
    def generate_end_impacts_results_for_video_women(self,results,ref_id,file_url,file_type,analyzer_type=None,scenario=None):
        url = AMAZON_BASE_URL
        # for value in results['Results']:
        impacts=[]
        if file_type == 'image':
            for value in results['Results']:
                # print("im women",value)
                if value['ViolationFound'] == True:
                    # print("im here women",value['ViolationFound'])
                    image_url =url+ref_id+"_frame_%s.jpg"%(str('0'))
                    res=self.upload_image_based_on_timestamp(str('0'),ref_id)
                    # for boundingbox in value['Boxes']:
                    impacts.append({'image_url':image_url,'bounding_results':value['Boxes']})
        if file_type == 'video':
            for value in results['Results']:
                if value['ViolationFound'] == True:
                    image_url =url+ref_id+"_frame_%s.jpg"%(str(value['Timestamp']))
                    res=self.upload_image_based_on_timestamp(str(value['Timestamp']),ref_id)
                    impacts.append({'image_url':image_url,'Timestamp':str(value['Timestamp']),'bounding_results':value['Boxes']})
        # print("im women", impacts)
        return impacts
        

    def generate_end_impacts_results_for_video_cp(self,results,ref_id,file_url,file_type,analyzer_type=None,scenario=None):
        url = AMAZON_BASE_URL
        impacts=[]
        if file_type == 'image':
            # print("im cp",results)
            for value in results['Results']:
                if value['ViolationFound'] == True:
                    image_url =url+ref_id+"_frame_%s.jpg"%(str('0'))
                    res=self.upload_image_based_on_timestamp(str('0'),ref_id)
                    impacts.append({'principle':'p7','image_url':image_url,'bounding_results':value['Boxes']})
        if file_type == 'video':
            for value in results['Results']:
                if value['ViolationFound'] == True:
                    image_url =url+ref_id+"_frame_%s.jpg"%(str(value['Timestamp']))
                    res=self.upload_image_based_on_timestamp(str(value['Timestamp']),ref_id)
                    impacts.append({'principle':'p7','image_url':image_url,'Timestamp':str(value['Timestamp']),'bounding_results':value['Boxes']})
                # print(impacts)
        print(impacts)
        return impacts
    
    def generate_end_impacts_results_for_video_trp(self,results,ref_id,file_url,file_type,analyzer_type=None,scenario=None):
        url = AMAZON_BASE_URL
        impacts=[]
        if file_type == 'image':
            for value in results['Results']:
                # print("im value trp",results)
                if value['ViolationFound'] == True:
                    # print("im value trp",value['ViolationFound'])
                    image_url =url+ref_id+"_frame_%s.jpg"%(str('0'))
                    res=self.upload_image_based_on_timestamp(str('0'),ref_id)
                    impacts.append({'principle':'p7','image_url':image_url,'bounding_results':value['Boxes']})
                # elif value['ViolationFound'] == False:
                #     impacts = []
        if file_type == 'video':
            for value in results['Results']:
                if value['ViolationFound'] == True:
                    # ;print(value['Boxes']['BoundingBox'])
                    image_url =url+ref_id+"_frame_%s.jpg"%(str(value['Timestamp']))
                    res=self.upload_image_based_on_timestamp(str(value['Timestamp']),ref_id)
                    impacts.append({'principle':'p4','image_url':image_url,'Timestamp':str(value['Timestamp']),'bounding_results':value['Boxes']})
        return impacts
    
    def generate_end_impacts_results(self,results,file_url,file_type,ref_id,analyzer_type=None,scenario=None):
        if file_type == "video" and analyzer_type=="Terrain":
            res = self.generate_end_impacts_results_for_video_terrain(results,ref_id,file_url,scenario=scenario)
        if (file_type == "video" or file_type=='image') and analyzer_type=="Background":
            res = self.generate_end_impacts_results_for_video_background(results,ref_id,file_url,file_type,scenario=scenario)
        if file_type == "video" and analyzer_type=="Logo":
            res = self.generate_end_impacts_results_for_video_logo(results,ref_id,file_url,scenario=scenario)
        if (file_type == "video" or file_type=='image') and analyzer_type=="Body":
            res = self.generate_end_impacts_results_for_video_body(results,ref_id,file_url,file_type,scenario=scenario)
        if (file_type == "video" or file_type=='image') and analyzer_type=="Eye":
            res = self.generate_end_impacts_results_for_video_eye(results,ref_id,file_url,file_type,scenario=scenario)
        if (file_type == "video" or file_type=='image') and analyzer_type=="Women":
            res = self.generate_end_impacts_results_for_video_women(results,ref_id,file_url,file_type,scenario=scenario)
        if (file_type == "video" or file_type=='image') and analyzer_type=="CP":
            res = self.generate_end_impacts_results_for_video_cp(results,ref_id,file_url,file_type,scenario=scenario)
        if (file_type == "video" or file_type=='image') and analyzer_type=="TRP":
            res = self.generate_end_impacts_results_for_video_trp(results,ref_id,file_url,file_type,scenario=scenario)
        return res

    # def get_analysis_detail_by_db_id(self,db_id):
    #     """ Get analysis detail for the particular project """
    #     neuro = NeuroAnalysis.objects().filter(ref_id=db_id).first()
    #     face_analysis = {}
    #     text_analysis = {}
    #     object_analysis = {}
    #     logo_analysis = {}

    #     if neuro:
    #         if "text_on_face" in neuro:
    #             analysis = neuro.text_on_face["analysis_result"]
    #             face_analysis=analysis["face_analysis"]
    #             text_analysis=analysis["text_analysis"]
    #         elif "lack_of_family_interactions" in neuro:
    #             analysis = neuro.lack_of_family_interactions["analysis_result"]
    #             face_analysis={"Faces":analysis["Faces"],"VideoMetadata":analysis["VideoMetadata"]}
    #         elif "lack_of_family_interactions" in neuro:
    #             analysis = neuro.lack_of_family_interactions["analysis_result"]
    #             face_analysis={"Faces":analysis["Faces"],"VideoMetadata":analysis["VideoMetadata"]}
    #         # elif "lack_of_family_interactions" in neuro:
    #         #     analysis = neuro.lack_of_family_interactions["analysis_result"]
    #         #     face_analysis={"Faces":analysis["Faces"],"VideoMetadata":analysis["VideoMetadata"]}

    #     resp ={
    #         "face_analysis":face_analysis,
    #         "text_analysis":text_analysis,
    #         "object_analysis":object_analysis,
    #         "logo_analysis":logo_analysis
    #     }
    #     return resp


    def upsert_feedback(self,data):
        """creating feedback against violations"""
        fdbck_obj=self.update_feedback(data)
        print(fdbck_obj)
        if not fdbck_obj:
            print("crating")
            fdbck_obj,error = FeedbackSchema().load(data)
            fdbck_obj["db_id"] = uuid.uuid4().hex
            fdbck_obj["created_at"] = datetime.datetime.now()
            fdbck_obj["updated_at"] = datetime.datetime.now()
            fdbck_obj.save()
        schema=FeedbackSchema()
        retdata = schema.dump(fdbck_obj)
        return retdata

    def get_feedback(self,data):
        """get feedback against violations and project"""
        ref_id=data["ref_id"]
        violation_name=data["keyword"]
        
        fdback=Feedback.objects(ref_id=ref_id,violation_name=violation_name).first()
        if fdback:
            schema=FeedbackSchema()
            retdata = schema.dump(fdback)
            return retdata


    def get_feedback_by_ref_and_violation_name(self,ref_id,violation_name):
        fdback=Feedback.objects(ref_id=ref_id,violation_name=violation_name).first()
        if fdback:
            return fdback
        return False

    def update_feedback(self,data):
        ref_id=data["ref_id"]
        violation_name = data["violation_name"]
        fdbk = self.get_feedback_by_ref_and_violation_name(ref_id=ref_id,violation_name=violation_name)
        print("violation name",data["violation_name"])
        print("im feedback data",fdbk)
        if fdbk:
            
            
            
            if "violation_name" in data:
                fdbk["violation_name"] = data["violation_name"]
                print(data["violation_name"])
            if "feedbacks" in data:
                print(data["feedbacks"])
                fdbk["feedbacks"]=data["feedbacks"]
            if "is_violation" in data:
                print(data["is_violation"])
                fdbk["is_violation"] = data["is_violation"]

            fdbk["updated_at"]=datetime.datetime.now()

            fdbk.save()
        else:
            print("error - feedback not foound")

        return fdbk


theNAlignSetFactory = NAlignSetFactory()




