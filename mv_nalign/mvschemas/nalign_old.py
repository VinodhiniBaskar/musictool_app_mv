import tracemalloc
import os
import logging
import uuid
import datetime
from functools import wraps
from flask import abort
import marshmallow as ma
from marshmallow import Schema, post_load, validate
from mv_nalign.mvmodels.Brands import BrandCategoryGroup
from mv_nalign.mvmodels.Projects import Project,ProjectFile,TempFileStorage,NeuroAnalysis,Feedback
from mv_nalign.mvexception.exception import MVException, ValidationException,Test
import re
from mongoengine.queryset.visitor import Q
from flask import Flask,jsonify
from flask_pymongo import PyMongo
from flask_restplus import Api, Resource, fields
from bson import ObjectId
import json
import random
import time
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from mv_nalign import settings
from mv_nalign.api import utils
# from pytube import YouTube
from mhyt import yt_download
import cv2
from mv_nalign.utility import upload_to_s3,object_detection,detect_text,upload_to_gcp
from mv_nalign.utility.src.aws_helper_service import AwsHelperService
from mv_nalign.analysis import analysis,analysis_main
from pymongo import MongoClient
import threading
from werkzeug import secure_filename
from mv_nalign.analysis import postprocessing as pp
from PIL import Image
from mv_nalign.analysis.src.scenarios import numerosity_principle as np
from mv_nalign.analysis.src.scenarios import close_w_faces_proximity as close_women_proximity
from mv_nalign.analysis.src.scenarios import close_faces_proximity as morethan_twopeople_close_proximity
from mv_nalign.analysis.src.scenarios import logo_intervention as logo_int
from mv_nalign.analysis.src.scenarios import text_relative_position as trp
import boto3
import asyncio
from google.cloud import storage
from mv_nalign.analysis.src.aws_helper_service import AwsHelperService
import timeit

log = logging.getLogger(__name__)
""" Db initialization """
local=MongoClient()
db=local['test_youtube_db']
coll=db["test_youtube_account"]


WATCH_URL = "https://www.youtube.com/watch?v="
AMAZON_BASE_URL="https://machine-vantage-inc-images.s3.us-east-2.amazonaws.com/"
DEFAULT_CAPTIONS_STRING = "No Captions Available"

ELEVEN_PRINCIPLE = ['','','','','','','','TWO CONSISTENT CHARACTERS','WOMEN TOGETHER','','FAMILY INTERACTIONS','']
DEFAULT_UPLOAD_PATH = settings.MEDIA_PATH+"/"


#TODO handle mv exception
class ProjectSchema(Schema):
    db_id = ma.fields.Str(allow_none=True)
    name = ma.fields.Str(required=False)
    description = ma.fields.Str(required=False, default='')
    file_url = ma.fields.Str(required=False, default='')
    file_duration = ma.fields.Str(required=False, default='')
    deleted = ma.fields.Boolean(required=False, default=False)
    brand = ma.fields.Str(required=False)
    product = ma.fields.Str(required=False)
    file_status = ma.fields.Dict(required=False)
    thumbnail_url = ma.fields.Str(required=False)
    file_type= ma.fields.Str(required=False)
    impacts_count=ma.fields.Int(required=False)
    published_at = ma.fields.DateTime()
    created_at = ma.fields.DateTime()
    updated_at = ma.fields.DateTime()
    impacts_status =ma.fields.Dict(required=False)
    captions = ma.fields.Str(required=False)
    image_width = ma.fields.Int(required=False)
    image_height= ma.fields.Int(required=False)
    # Score = ma.fields.Str(required=False)


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


class NeuroAnalysisSchema(Schema):

    db_id = ma.fields.Str(required=False)
    ref_id = ma.fields.Str(required=False)
    file_name = ma.fields.Str(required=False)
    more_than_two_consistent_characters = ma.fields.Dict(required = False)
    women_together = ma.fields.Dict(required = False)
    lack_of_family_interactions = ma.fields.Dict(required = False)
    text_on_face = ma.fields.Dict(required = False)
    images_on_right_words_to_left = ma.fields.Dict(required = False)
    eyes_contact = ma.fields.Dict(required= False)
    more_than_three_visual_clusters = ma.fields.Dict(required= False)
    interrupt_flow_storyline = ma.fields.Dict(required= False)
    overlay_text_background = ma.fields.Dict(required= False)
    variation_in_terrain = ma.fields.Dict(required= False)
    body_part_isolation = ma.fields.Dict(required= False)
    # text_data = DynamicField(required=False)
    # text_analysis = DynamicField(required=False)
    # video_data = DynamicField(required=False)
    # video_analysis = DynamicField(required=False)
    # face_analysis = DynamicField(required=False)
    # positive_impacts = DynamicField(required=False)
    # negative_impacts = DynamicField(required=False)
    # final_positive_impacts =DynamicField(required=False)
    # final_negative_impacts = DynamicField(required=False)

    @post_load
    def make_neuro_analysis(self, data):
        return NeuroAnalysis(**data)


class FeedbackSchema(Schema):
    db_id = ma.fields.Str(required=False)
    ref_id = ma.fields.Str(required=False)
    violation_name=ma.fields.Str(required=False)
    feedbacks=ma.fields.List(ma.fields.Str(required=False),required=False)
    file_type=ma.fields.Str(required=False,default="image")
    is_violation=ma.fields.Boolean(required=False)
    created_at = ma.fields.DateTime()
    updated_at = ma.fields.DateTime()



    @post_load
    def make_feedback(self, data):
        return Feedback(**data)


'''
    ==============================================
    nalign - Class Factory
    ================================================
'''



class ProcessVideoThread(threading.Thread):
    def __init__(self,ref_id):
        self.ref_id = ref_id

        threading.Thread.__init__(self)

    def run(self):
        # c=theNAlignSetFactory.generate_impact_and_violations(self.ref_id)
        c=theNAlignSetFactory.generate_impacts(self.ref_id)


def process_video(ref_id):
    print("Threading started")
    ProcessVideoThread(ref_id).start()

class NAlignSetFactory(object):

    # db connect in __init__?
    def __init__(self):
        # log.debug ('init')
        pass

    # def get_type(file, bucket):
    # 	s3 = boto3.resource('s3')
    # 	object_data = s3.Object(bucket, file)
    # 	return check(object_data.content_type, file)

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
            raise Test("test working")
            raise MVException("brand doesn't exist")

        return sorted(cat)

    def get_marshalled_schema(self,obj):
        if obj:
            schema=ProjectSchema()
            retdata = schema.dump(obj)
            return retdata

    def create_project(self,data):
        #handling upsert operation here
        link_source = 'INTERNAL'

        proj_obj ={}
        if 'db_id' in data:
            #if db_id has exist , update a project

            if data["db_id"]:
                # log.debug("db id has value,so update operation")
                proj_obj = self.update_project(data)


        if not proj_obj:
            if "link_source"  in data:
                link_source=data["link_source"]
            # if not self.does_check_duplicate_project_name(data["name"]):
            if "file" in data:
                file = data["file"]
            proj_obj, error = ProjectSchema().load(data)
            print(proj_obj,error)
            print(proj_obj["file_type"])
            proj_obj["db_id"] = uuid.uuid4().hex
            proj_obj["created_at"] = datetime.datetime.now()


        # UPDATE STATUS
        # link source External means user uploaded a video in youtube and then get the metadata information
        # link source Internal means user using youtube link to get the metadata information
            if link_source:
                if link_source.upper() == "EXTERNAL":
                    proj_obj["file_status"] = {"status":"Processing"} #video yet to be uploaded
                else:
                    proj_obj["file_status"] = {"status":"Completed"} #video uploaded already
            # proj_obj["file_type"] = "video"
            proj_obj["updated_at"] = datetime.datetime.now()

            proj_obj["impacts_status"] = {"status":"processing"}
            proj_obj["captions"] = ""
            if proj_obj["file_type"] =="image":
                # case 1
                #for only image s3 file url store in main project db
                # case 2
                #for video ,based on timestamp we store s3 url to sub project db
                # data["file"].close()

                # ufile=file
                # data["file"].close()
                t_file=self.generate_thumbnail_image(file,proj_obj["db_id"])
                if t_file:

                    up_load=upload_to_s3.upload_file(t_file, settings.IMAGE_BUCKET_NAME,t_file.split('/')[-1])
                    thumbnail_url = AMAZON_BASE_URL+t_file.split('/')[-1]
                    proj_obj["thumbnail_url"] =thumbnail_url
                print("file!!!!!!!!!",file)#upload_to_s3.upload_file(t_file, settings.IMAGE_BUCKET_NAME,t_file.split('/')[-1])
                # proj_obj["file_url"] = self.upload_image_to_s3_from_input(data["file"],proj_obj["db_id"])
                filename = proj_obj["db_id"]+'.'+thumbnail_url.split('.')[-1]
                org_img_to_s3 = upload_to_s3.upload_file(settings.BASE_MEDIA_PATH+filename,settings.IMAGE_BUCKET_NAME,filename)
                print("org_img uploaded successfully")

                proj_obj["file_url"] =AMAZON_BASE_URL+filename

                # import time
                # time.sleep(5)

                proj_obj["file_status"] = {"status":"Completed"}

            proj_obj.save()

        if proj_obj["impacts_status"]["status"]=="processing":
            print("thread")
            process_video(proj_obj.db_id)
        schema=ProjectSchema()
        print(type(proj_obj.published_at))
        print(type(proj_obj.created_at))
        retdata = schema.dump(proj_obj)
        return retdata

    def generate_thumbnail_image(self,image_file,ref_id):
        # print(image_file)
        from werkzeug.utils import secure_filename
        default_thumbnail_size = (700,400)

        file_extn = image_file.filename.split('.')[-1]
        filename=ref_id+"."+file_extn
        path= os.path.join('mv_nalign/media/')
        print(path)
        # print(type(image_file))
        # image_file.save(dst='media')
        # image_file.close()
        # filename = secure_filename(image_file.filename)
        # file.save('/home/laptop-obs-68/mvsvc/mv_neuroaligner_services/mv_nalign/'+filenamete)
        print(path+filename)
        image_file.save(path+filename)
        # image_file.close()
        path= os.path.join('mv_nalign/media/')
        print("saved")
        # with open()
        im = Image.open(path+filename)
        im.thumbnail(default_thumbnail_size)

        thumbnail_file_name = ref_id+"_thumbnail."+file_extn
        im.save(path+thumbnail_file_name)
        im.close()

        return settings.BASE_MEDIA_PATH+thumbnail_file_name

    def generate_impacts(self,project_id):
        print("generateimapoc")
        scenario = ['search_for_lack_of_family_interactions','search_for_more_than_two_consistent_characters']
        #TODO before calling generate_impacts_based_on_scenario function, detect faces,objects,text for all the scenario(if do like this no need to detect again for all scenario)
        # scenarioList
        
        # scenario = ['search_for_logo_intervention',
        #               'search_for_numerosity_principle',
        #               'search_for_variation_in_terrain',
        #               'search_for_images_on_right_words_to_left',
        #               'search_for_eyes_contact',
        #               'search_for_more_than_two_consistent_characters',
        #               'search_for_more_than_two_people_in_close_proximity',
        #               'search_for_women_apart_not_in_close_physicalproximity',
        #               'search_for_text_on_face',
        #               'search_for_lack_of_family_interactions',
        #               'search_for_overlay_text_background',
        #               'search_for_body_parts'
        #             ]
        for scene in scenario:
            re = self.generate_impacts_based_on_scenario(project_id,scene)

    def upload_image_to_s3_from_input(self,image_file,ref_id):
        # image_file = file
        print("file object",image_file)
        file_extn = image_file.filename.split('.')[-1]
        filename=ref_id+"."+file_extn
        print("file name",filename)

        resp=upload_to_s3.upload_fileobj(image_file,settings.IMAGE_BUCKET_NAME,filename)
        if resp:
            print("image upload success")
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

        # query_result=CustomBrandSet.objects().filter(name__icontains=keywords)

        total_results = Project.objects(deleted=False).count()
        query_ordered_by = self.get_query_order(order,column)
        print(query_ordered_by)
        filtered_results = Project.objects(
            name__icontains=partial, deleted=False).count()
        if limit == -1:
            query_result = Project.objects(
                name__icontains=partial, deleted=False).order_by(query_ordered_by)[:]
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


        return {'data': query_result, 'recordsTotal': total_results, 'recordsFiltered': filtered_results}

    def update_project(self,data):
        print("updateing a porje")
        proj_obj=self.get_by_id(data["db_id"])
        if proj_obj:
            # if not self.does_check_duplicate_project_name(data["name"],data["db_id"]):
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
            # if "published_at" in data:
            #     proj_obj["published_at"]=datetime.datetime.strptime(data["published_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
            if "updated_at" in data:
                proj_obj["updated_at"]=datetime.datetime.now()
            if "link_source" in data:
                link_source=data["link_source"].upper()
                if link_source == "EXTERNAL":
                    proj_obj["file_status"] = {"status":"Processing"} #video yet to be uploaded
                else:
                    proj_obj["file_status"] = {"status":"Completed"} #video uploaded already
            # proj_obj["file_type"] = "video"
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

            # if 'credentials' not in yt_credentials:
            # 	return flask.redirect('authorize')

        # Load credentials from the data store.
        ext = file_data.filename.split('.')[-1]
        file_path=uuid.uuid4().hex+"."+ext
        f=file_data.save(file_path)

        credentials = google.oauth2.credentials.Credentials(
            **credentials)
        youtube = build(
            settings.API_SERVICE_NAME, settings.API_VERSION, credentials=credentials,cache_discovery=False)
        print(youtube)
        # print("req mthd is correct")


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
        # response ={}

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
 

    def download_youtube_video(self,link,project_id,scenario,file_type):
        try:
            print("im download",file_type)
            if file_type=='video':
            # link = "https://www.youtube.com/watch?v=K0Qa9DgVvVM"
                
                file_name = project_id+".mp4"
                    # yt = yt_download(link,file_name)
                    # yt = YouTube(link)
                    # print (yt.title)
                # stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                prefix_folder = settings.BASE_MEDIA_PATH
                print("Im herefh",os.getcwd())
                if not os.path.exists(prefix_folder):
                    print("folder not found")
                    os.mkdir(prefix_folder)
                file_name = project_id
                # file_name = "Unilever - Farewell To The Forest"
                # stream.download(output_path=prefix_folder,filename=file_name)
                # print(prefix_folder+"/"+file_name)
                try:
                    yt = yt_download(link,prefix_folder+file_name+".mp4")
                except:
                    yt = yt_download(link,prefix_folder+file_name+".mp4")
                print("im check the path",os.path.isfile('./'+prefix_folder+file_name+".mp4"))
                bucket = settings.VIDEO_BUCKET_NAME
                file_path=prefix_folder+file_name+".mp4"
                upld_gcp = ''
                if scenario == 'search_for_logo_intervention':
                    upld_gcp = upload_to_gcp.upload_blob(file_path,bucket,file_name+".mp4")
                elif scenario=='search_for_numerosity_principle' or scenario=='search_for_overlay_text_background' or scenario=='search_for_women_apart_not_in_close_physicalproximity' or scenario=='search_for_images_on_right_words_to_left' or scenario=='search_for_text_on_face' or scenario=='search_for_more_than_two_people_in_close_proximity' or scenario=='search_for_more_than_two_consistent_characters' or scenario=='search_for_eyes_contact' or scenario == 'search_for_lack_of_family_interactions' or scenario=='search_for_variation_in_terrain' or scenario=='search_for_body_parts' or scenario=='search_for_text_relative_position': #or scenario == 'search_for_overlay_text_background' or scenario=='search_for_numerosity_principle'
                    print("im scenario for voe",scenario)
                    upld_s3 =  upload_to_s3.upload_file(file_path,bucket,file_name+".mp4")
                    print("im checkingh",file_path,upld_s3)
                    print("im upld",upld_s3)
                else:
                    upld_gcp = False
                    upld_s3 = False
                if upld_gcp == True or upld_s3==True :
                    #TODO does file exist means return True else False
                    if os.path.isfile(file_path) and os.access(file_path, os.R_OK):
                        return file_path
                    else:
                        return False
        except:
                print("im here")

    def upload_image(self,ufile,filename):
        from PIL import Image
        im = Image.fromarray(ufile)
        print(filename)
        im.save(settings.MEDIA_PATH+"/"+filename, filename)
        return settings.MEDIA_PATH+"/"+filename

    def extract_image_from_video(self,video_file,ref_id):
        print("##########","mv_nalign/media/"+ref_id+".mp4")
        # vidcap = cv2.VideoCapture("mv_nalign/media/"+ref_id+".mp4")
        vidcap = cv2.VideoCapture("mv_nalign/media/"+"test_pledge.mp4")
        success,image = vidcap.read()
        print(success,image)
        count = 0
        # path=os.getcwd()+"/mv_nalign/media/"+ref_id+"/"
        # if not os.path.exists(path):
        #     # prefix_folder=main_folder+"output"
        #     # if os.path.exists(prefix_folder):
        #     #      shutil.rmtree(prefix_folder)
        #     print("not found")
        #     os.mkdir(path)
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

        vidcap = cv2.VideoCapture("mv_nalign/media/"+neuro.video_name)

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


                        vidcap = cv2.VideoCapture("mv_nalign/media/"+neuro.video_name)

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
                                    cv2.imwrite("mv_nalign/media/"+ref_id+"_frame_%d.jpg" % (time),image)
                                    upload_to_s3.upload_file("mv_nalign/media/"+ref_id+"_frame_%d.jpg" % (time),bucket,ref_id+"_frame_%d.jpg" % (time))

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

    def get_neuro_by_ref_id(self,ref_id):
        neuro_obj = NeuroAnalysis.objects(ref_id=ref_id).first()
        print("im neruo objec",neuro_obj)
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
            filepath = 'mv_nalign/media/'+ref_id+'.mp4'
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
                    cv2.imwrite('mv_nalign/media/'+ref_id+'_stryframe{:d}.jpg'.format(count), image)
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
            

    def get_impacts_count(self,ref_id):
        # print("",ref_id)
        neuro_obj = self.get_neuro_by_ref_id(ref_id)
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
            if "overlay_text_background" in neuro_obj:
                impact_details = {}
                impact_details["impact_name"]="Body part isolation"
                impact_details["principle_name"] = "Chopped faces / body parts or body parts in isolation"
                impact_details["total_count"]= len(neuro_obj.body_part_isolation["results"])
                impact_details["is_violation"]=self.get_feedback_violation_flag(ref_id,impact_details["impact_name"])
                neuros.append(impact_details)

        print("im neuro",neuros)
        return sorted(neuros,key=lambda k:k["total_count"],reverse=True)

    def covert_keys_to_lowercase(self,boundingboxes):
        s={}
        for key,value in boundingboxes.items():
            s[key.lower()] = value

        return s


    # def search_for_more_than_two_people_in_close_proximity(self):
    # 	print("im here")
    # 	print(self)

    #principle no 7 - POSITIVE IMPACT: Two consistent characters; two people in close proximity(2 only, no more than 2)
    def get_impact_principle_seven(self, ref_id,scenario):
        print("Processing started for analysis")
        proj_obj=self.get_by_id(ref_id)
        print("dfkjdlfkj",proj_obj)
        if proj_obj.file_type=="video":
            if proj_obj:

                yt_download = self.download_youtube_video(proj_obj.file_url,ref_id,scenario,file_type)

            # # yt_download = self.download_youtube_video("dfd",ref_id)
            if yt_download:
                print("video downloaded")
                # print(yt_download)
                file_name_url=yt_download
                file_name_url=file_name_url.split('/')[-1]
            bucket=settings.VIDEO_BUCKET_NAME
        else:
            file_name_url = proj_obj.file_url.split('/')[-1]
            bucket=settings.IMAGE_BUCKET_NAME


        #     pass

        #calculate bounding boxes

        neuro = NeuroAnalysis.objects(ref_id=ref_id).first()
        print("neuro check ",neuro)
        if not neuro:
            print("Not analysis found im video")
            neuro=NeuroAnalysis()
            neuro.db_id=uuid.uuid4().hex
            neuro.ref_id=ref_id
            neuro.video_name=file_name_url
            neuro.video_data={}
            neuro.video_analysis={}
            neuro.text_data={}
            neuro.text_analysis={}
            neuro.face_analysis = {}
            neuro.positive_impacts = {}
            neuro.negative_impacts = {}
            neuro.final_positive_impacts = []
            neuro.final_negative_impacts = []
            neuro.save()



        #save to mongo
        print("Analysis metadata added")
        if not neuro.face_analysis:
            analyse = analysis_main.analyse("face",neuro.video_name,proj_obj.file_type,bucket)
            neuro.face_analysis=json.loads(analyse)
            neuro.save()

        print("ANALYSIS COMPLETED")
        neuro.positive_impacts = []
        if proj_obj.file_type=="image":
            if neuro.face_analysis["FoundScenario"]:
                neuro.positive_impacts.append({"impact_name":"Two consistent characters","impacts_results":{"0":neuro.face_analysis["FaceDetails"]}})
                neuro.save()
            else:
                neuro.positive_impacts.append({"impact_name":"Two consistent characters","impacts_results":{"0":[]}})
                neuro.save()
            impacts = []
            for v in neuro.positive_impacts:
                impacts_obj = {}
                impacts_obj["impact_name"] = v["impact_name"]
                print("impact name is",v["impact_name"])
                bounding = []
                for s in v["impacts_results"]:
                    imp_res = v["impacts_results"][s]
                    inner_impacts = {}

                    inner_impacts["image_url"] =proj_obj.file_url
                    inner_bounding = []
                    for k in imp_res:
                        inner_bounding.append({"bounding_box":self.covert_keys_to_lowercase(k["BoundingBox"])})
                    inner_impacts["bounding_results"] = inner_bounding
                    if len(inner_impacts["bounding_results"])>0:
                        bounding.append(inner_impacts)
                impacts_obj["impact_results"] = bounding
                impacts.append(impacts_obj)

            neuro.final_positive_impacts = impacts
            neuro.save()

            if neuro.final_positive_impacts:
                print("im positie")
                proj_obj = self.get_by_id(ref_id)
                proj_obj.impacts_status = {"status":"completed"}
                proj_obj.impacts_count =  self.get_total_impacts(neuro.final_positive_impacts)
                proj_obj.save()

            print("IMPACTS PROCESS COMPLETED")

        elif proj_obj.file_type=="video":
            if neuro.face_analysis["FoundScenarios"]:
                face_details = {}
                for v in neuro.face_analysis["FoundScenarios"]:
                    for n in neuro.face_analysis["Faces"]:
                        if n["Timestamp"] == v["Timestamp"]:
                            if str(n["Timestamp"]) in face_details:
                                face_details[str(n["Timestamp"])].append(n)
                            else:
                                face_details[str(n["Timestamp"])] = [n]

                neuro.positive_impacts.append({"impact_name":"Two consistent characters","impacts_results":face_details})
                neuro.save()
            else:
                neuro.positive_impacts.append({"impact_name":"Two consistent characters","impacts_results":{"0":[]}})
                neuro.save()

            timestamp = set()
            if neuro:
                for impacts in neuro.positive_impacts:

                    for k in impacts["impacts_results"]:
                        print("key is ",type(k))
                        timestamp.add(k)

                # for d in neuro.negative_impacts:
                #     timestamp.add(d["timestamp"])

            vidcap = cv2.VideoCapture("mv_nalign/media/"+neuro.video_name)

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

            # impacts["positive_impacts"] = []

            print(neuro.positive_impacts)

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
                        inner_bounding = []
                        for k in imp_res:
                            print(k)
                            if "Face" in k:
                                inner_bounding.append({"bounding_box":self.covert_keys_to_lowercase(k["Face"]["BoundingBox"])})
                        inner_impacts["bounding_results"] = inner_bounding
                        if len(inner_impacts["bounding_results"])>0:
                            bounding.append(inner_impacts)


                impacts_obj["impact_results"] = bounding
                impacts.append(impacts_obj)

            neuro.final_positive_impacts = impacts
            neuro.save()

            if neuro.final_positive_impacts:
                proj_obj = self.get_by_id(ref_id)
                proj_obj.impacts_status = {"status":"completed"}
                proj_obj.impacts_count =  self.get_total_impacts(neuro.final_positive_impacts)
                proj_obj.save()

            print("IMPACTS PROCESS COMPLETED")
        return "success"

    def upload_image_based_on_timestamp(self,time,ref_id):
        neuro=NeuroAnalysis.objects(ref_id=ref_id).first()
        if neuro :
            print("im neruro interain")
            vidcap = cv2.VideoCapture("mv_nalign/media/"+neuro.file_name)
                # vidcap = cv2.VideoCapture(video_file)
            url = AMAZON_BASE_URL
            bucket = settings.IMAGE_BUCKET_NAME
            vidcap.set(cv2.CAP_PROP_POS_MSEC,int(time))    # just cut to time msec. position
            success,image = vidcap.read()
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
        print(time)
        print(ref_id)
        print("im gcp")
        neuro=NeuroAnalysis.objects(ref_id=ref_id).first()
        if neuro :
            vidcap = cv2.VideoCapture("mv_nalign/media/"+neuro.file_name)
            bucket = settings.IMAGE_BUCKET_NAME
                # vidcap = cv2.VideoCapture(video_file)
            url = "https://storage.googleapis.com/%s/%s" % (bucket, neuro.file_name)
            vidcap.set(cv2.CAP_PROP_POS_MSEC,int(time))    # just cut to time msec. position
            success,image = vidcap.read()
            f_obj = ProjectFile.objects().filter(ref_id=ref_id,image_timestamp=time).first()
            print("file exist or not",f_obj)
            if not f_obj:
                print("initialize")
                if success:
                    cv2.imwrite("mv_nalign/media/"+ref_id+"_frame_%s.jpg" % (time),image)
                    upload_to_gcp.upload_blob("mv_nalign/media/"+ref_id+"_frame_%s.jpg" % (time),'machine-vantage-inc-image',ref_id+"_frame_%s.jpg" % (time))
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
        print("im heree terrain")
        bounding = []
        url = AMAZON_BASE_URL
        bucket = settings.IMAGE_BUCKET_NAME
        if results['ViolationFound'] == True:
            inner_impacts = {}
            for time in results['Results']:
                image_url =url+ref_id+"_frame_%s.jpg"%(str(time))
                res=self.upload_image_based_on_timestamp(str(time),ref_id)
                print(res,"res")
                bounding.append({'image_url':image_url,'Timestamp':str(time),'bounding_results':[]})
                print(bounding)
        return bounding

    def generate_end_impacts_results_for_video_logo(self,results,ref_id,file_url,analyzer_type=None,scenario=None):
        print(results)
        # check_gender_female=False
        # print(ref_id)
        # print(file_url)
        url = "https://storage.googleapis.com/machine-vantage-inc-image/"
        if "FoundScenario" in results:
            scenario_found=results['FoundScenario']
            if scenario_found != False:
                resp={}
                for v in results["FoundScenario"]:
                    impacts=[]
                    if len(v['Segments']) != 0:
                        inner_timestamp = []
                        for values in v['Segments']:    
                            for n in values:
                                # print(n['Timestamp'])
                                timestamp = url+ref_id+"_frame_%s.jpg"%(int(n['Timestamp']))
                                # inner_impacts["image_url"] = url+ref_id+"_frame_%s.jpg"%(n['Timestamp'])
                                resp['bounding_box']=self.covert_keys_to_lowercase(n["BoundingBox"])
                                res=self.upload_image_based_on_timestamp_gcp(int(n['Timestamp']),ref_id)
                                # print(inner_timestamp)
                                impacts.append({'principle':'p1','image_url':timestamp,'bounding_results':[{'BoundingBox':resp['bounding_box']}]})
                    else:
                        impacts=[]
                                # impacts.append(inner_impacts)
                                # print("logo", impacts)
            else:
                impacts=[]

        return impacts
    
    def generate_end_impacts_results_for_video_body(self,results,ref_id,file_url,analyzer_type=None,scenario=None):
        url = AMAZON_BASE_URL
        impacts=[]
        for value in results['Results']:
            # impacts=[]
            if value['ViolationFound'] == True:
                # print(value['Timestamp'])
                # print(value['Boxes'])
                image_url =url+ref_id+"_frame_%s.jpg"%(str(value['Timestamp']))
                res=self.upload_image_based_on_timestamp(str(value['Timestamp']),ref_id)
                impacts.append({'principle':'p11','image_url':image_url,'Timestamp':str(value['Timestamp']),'bounding_results':value['Boxes']})
        return impacts
    
    def generate_end_impacts_results_for_video_background(self,results,ref_id,file_url,analyzer_type=None,scenario=None):
        url = AMAZON_BASE_URL
        impacts=[]
        for value in results['Results']:
            # impacts=[]
            if value['ViolationFound'] == True:
                # print(value['Timestamp'])
                # print(value['Boxes'])
                image_url =url+ref_id+"_frame_%s.jpg"%(str(value['Timestamp']))
                res=self.upload_image_based_on_timestamp(str(value['Timestamp']),ref_id)
                print(value['Boxes'])
                impacts.append({'principle':'p11','image_url':image_url,'Timestamp':str(value['Timestamp']),'bounding_results':value['Boxes']})
        return impacts

    def generate_end_impacts_results_for_video_eye(self,results,ref_id,file_url,file_type,analyzer_type=None,scenario=None):
        url = AMAZON_BASE_URL
        impacts=[]
        # print("im file type",file_type)
        # if file_type == 'video':
        for value in results['Results']:
            if value['ViolationFound'] == True:
                image_url =url+ref_id+"_frame_%s.jpg"%(str(value['Timestamp']))
                res=self.upload_image_based_on_timestamp(str(value['Timestamp']),ref_id)
                impacts.append({'principle':'p5','image_url':image_url,'Timestamp':str(value['Timestamp']),'bounding_results':value['Boxes']})
        # else:
        #     for value in results['Results']:
        return impacts
    
    def generate_end_impacts_results_for_video_women(self,results,ref_id,file_url,analyzer_type=None,scenario=None):
        url = AMAZON_BASE_URL
        impacts=[]
        print("im women",results)
        for value in results['Results']:
            if value['ViolationFound'] == True:
                image_url =url+ref_id+"_frame_%s.jpg"%(str(value['Timestamp']))
                res=self.upload_image_based_on_timestamp(str(value['Timestamp']),ref_id)
                impacts.append({'principle':'p6','image_url':image_url,'Timestamp':str(value['Timestamp']),'bounding_results':value['Boxes']})
        return impacts

    def generate_end_impacts_results_for_video_cp(self,results,ref_id,file_url,analyzer_type=None,scenario=None):
        url = AMAZON_BASE_URL
        impacts=[]
        for value in results['Results']:
            if value['ViolationFound'] == True:
                image_url =url+ref_id+"_frame_%s.jpg"%(str(value['Timestamp']))
                res=self.upload_image_based_on_timestamp(str(value['Timestamp']),ref_id)
                impacts.append({'principle':'p7','image_url':image_url,'Timestamp':str(value['Timestamp']),'bounding_results':value['Boxes']})
        return impacts
    
    def generate_end_impacts_results_for_video_trp(self,results,ref_id,file_url,analyzer_type=None,scenario=None):
        url = AMAZON_BASE_URL
        impacts=[]
        for value in results['Results']:
            if value['ViolationFound'] == True:
                # ;print(value['Boxes']['BoundingBox'])
                image_url =url+ref_id+"_frame_%s.jpg"%(str(value['Timestamp']))
                res=self.upload_image_based_on_timestamp(str(value['Timestamp']),ref_id)
                impacts.append({'principle':'p4','image_url':image_url,'Timestamp':str(value['Timestamp']),'bounding_results':value['Boxes']})
        return impacts
    
    def generate_end_impacts_results(self,results,file_url,file_type,ref_id,analyzer_type=None,scenario=None):
        if file_type == "image" and analyzer_type=="Face":
            res =  self.generate_end_impacts_results_for_image_face(results,file_url,scenario=scenario)
        if file_type == "video" and analyzer_type=="Face":
            # print("im gafdce abd not teria")
            res = self.generate_end_impacts_results_for_video_face(results,ref_id)
        if file_type == "video" and analyzer_type=="Terrain":
            res = self.generate_end_impacts_results_for_video_terrain(results,ref_id,file_url,scenario=scenario)
        if (file_type == "video" or file_type=='image') and analyzer_type=="Background":
            res = self.generate_end_impacts_results_for_video_background(results,ref_id,file_url,scenario=scenario)
        if file_type == "video" and analyzer_type=="Logo":
            res = self.generate_end_impacts_results_for_video_logo(results,ref_id,file_url,scenario=scenario)
        if (file_type == "video" or file_type=='image') and analyzer_type=="Body":
            res = self.generate_end_impacts_results_for_video_body(results,ref_id,file_url,scenario=scenario)
        if (file_type == "video" or file_type=='image') and analyzer_type=="Eye":
            res = self.generate_end_impacts_results_for_video_eye(results,ref_id,file_url,file_type,scenario=scenario)
        if (file_type == "video" or file_type=='image') and analyzer_type=="Women":
            res = self.generate_end_impacts_results_for_video_women(results,ref_id,file_url,scenario=scenario)
        if (file_type == "video" or file_type=='image') and analyzer_type=="CP":
            res = self.generate_end_impacts_results_for_video_cp(results,ref_id,file_url,scenario=scenario)
        if (file_type == "video" or file_type=='image') and analyzer_type=="TRP":
            res = self.generate_end_impacts_results_for_video_trp(results,ref_id,file_url,scenario=scenario)
        if file_type == "video" and analyzer_type=="Text":
            res = self.generate_end_impacts_results_for_video_text(results,ref_id,file_url,scenario=scenario)
        if file_type == "image" and analyzer_type=="Text":
            res =  self.generate_end_impacts_results_for_image_text(results,file_url,scenario=scenario)
        elif file_type =="image" and analyzer_type=="Face_Object_Text": #Face_Object_Text_Cluster
            res = self.generate_end_impacts_results_for_image_face_obj_text(results,file_url,scenario=scenario)
        elif file_type =="image" and analyzer_type=="Face_Object_Text_Cluster": #Face_Object_Text_Cluster
            res = self.generate_end_impacts_results_for_image_face_obj_text_cluster(results,file_url,scenario=scenario)
        # elif file_type =="video" and analyzer_type=="Text":
        #     res=self.generate_end_impacts_results_for_video_text(results,ref_id)

        return res

    def generate_impacts_based_on_scenario(self,ref_id,scenario):
        print("Processing started for analysis",scenario)
        proj_obj=self.get_by_id(ref_id)
        print("project exist or not ",proj_obj)
        file_type = proj_obj.file_type
        # bucket=settings.VIDEO_BUCKET_NAME
        yt_downloads = ''
        if file_type=="video": 
            yt_downloads = self.download_youtube_video(proj_obj.file_url,ref_id,scenario,file_type)
            if  not proj_obj.is_uploaded:
                print("im here",yt_downloads)
                if yt_downloads:
                    print("video downloaded")
                    proj_obj.is_uploaded=True
                    proj_obj.save()
                    file_name_url=yt_downloads
                    file_name_url=file_name_url.split('/')[-1]
            elif proj_obj.is_uploaded:
                print("video downloaded")
                proj_obj.is_uploaded=True
                proj_obj.save()
                file_name_url=yt_downloads
                file_name_url=file_name_url.split('/')[-1]
            bucket=settings.VIDEO_BUCKET_NAME
        else:
            print("im here payload")
            file_name_url = proj_obj.file_url.split('/')[-1]
            bucket=settings.IMAGE_BUCKET_NAME

        neuro = NeuroAnalysis.objects(ref_id=ref_id).first()
        print("neuro check ",neuro)
        if not neuro:
            payload = {}
            payload["db_id"] = uuid.uuid4().hex
            payload["ref_id"] = ref_id
            payload["file_name"]=file_name_url
            neuro,error = NeuroAnalysisSchema().load(payload)
            # print(payload,"im payload value")
            neuro.save()
            print("Not analysis found")

        if scenario == "search_for_lack_of_family_interactions" and (file_type=='image' or file_type=='video'):
            try:
                start = timeit.default_timer()
                result_search_for_lack_of_family_interactions = analysis_main.analyse(neuro.file_name,bucket,"search_for_lack_of_family_interactions")
                res_1 = result_search_for_lack_of_family_interactions.run()
                res_json = json.dumps(res_1)
                json_object = json.loads(res_json)
                stop = timeit.default_timer()
                time_capture = stop - start 
                # print(res)
                if result_search_for_lack_of_family_interactions != '':
                    results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,ref_id,analyzer_type="Women",scenario='search_for_more_than_two_consistent_characters')
                    neuro.lack_of_family_interactions={"analysis_result":json_object,"results":results,'timeduration':time_capture}
                    neuro.save()
                else:
                    neuro.lack_of_family_interactions={"analysis_result":result_search_for_lack_of_family_interactions,"results":[],'timeduration':time_capture}
                    neuro.save()
            except KeyError as e:
                neuro.lack_of_family_interactions={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()
            except IndexError as e:
                neuro.lack_of_family_interactions={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()
            
        elif scenario == "search_for_more_than_two_consistent_characters" and (file_type=='image' or file_type=='video'): ##15-10-2020 Committed
            try:
                start = timeit.default_timer()
                result_search_for_women_together = analysis_main.analyse(neuro.file_name,bucket,"search_for_more_than_two_consistent_characters")
                res_1 = result_search_for_women_together.run()
                res_json = json.dumps(res_1)
                json_object = json.loads(res_json)
                stop = timeit.default_timer()
                time_capture = stop - start 
                if result_search_for_women_together != '':
                        results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,ref_id,analyzer_type="Women",scenario='search_for_more_than_two_consistent_characters')
                        neuro.more_than_two_consistent_characters={"analysis_result":json_object,"results":results,'timeduration':time_capture}
                        neuro.save()
                else:
                    neuro.more_than_two_consistent_characters={"analysis_result":json_object,"results":[],'timeduration':time_capture}
                    neuro.save()
            except KeyError as e:
                neuro.more_than_two_consistent_characters={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()
            except IndexError as e:
                neuro.more_than_two_consistent_characters={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()
                
        elif scenario == "search_for_text_on_face" and (file_type=="image" or file_type=='video'):
            try:
                start = timeit.default_timer()
                result_search_for_text_face_overlap = analysis_main.analyse(neuro.file_name,bucket,"search_for_text_face_overlap")
                res_1 = result_search_for_text_face_overlap.run()
                res_json = json.dumps(res_1)
                json_object = json.loads(res_json)
                stop = timeit.default_timer()
                time_capture = stop - start 
                if result_search_for_text_face_overlap != '':
                    results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,ref_id,analyzer_type="TRP",scenario='search_for_images_on_right_words_to_left')
                    neuro.text_on_face={"analysis_result":json_object,"results":results,'timeduration':time_capture}
                    neuro.save()
                else:
                    neuro.text_on_face={"analysis_result":json_object,"results":[],'timeduration':time_capture}
                    neuro.save()
            except KeyError as e:
                neuro.text_on_face={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()
            except IndexError as e:
                neuro.text_on_face={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()
            
        elif scenario == "search_for_images_on_right_words_to_left" and  (file_type=='image' or file_type=='video'):
            try:
                start = timeit.default_timer()
                result_search_for_text_relative_position = analysis_main.analyse(neuro.file_name,bucket,"search_for_text_relative_position")
                res_1 = result_search_for_text_relative_position.run()
                res_json = json.dumps(res_1)
                json_object = json.loads(res_json)
                stop = timeit.default_timer()
                time_capture = stop - start 
                if result_search_for_text_relative_position != '':
                    results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,ref_id,analyzer_type="TRP",scenario='search_for_images_on_right_words_to_left')
                    neuro.images_on_right_words_to_left={"analysis_result":json_object,"results":results,'timeduration':time_capture}
                    neuro.save()
                else:
                    neuro.images_on_right_words_to_left={"analysis_result":json_object,"results":[],'timeduration':time_capture}
                    neuro.save()
            except KeyError as e:
                neuro.images_on_right_words_to_left={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()
            except IndexError as e:
                neuro.images_on_right_words_to_left={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()
           
        elif scenario == "search_for_eyes_contact" and (file_type=='image' or file_type=='video'):
            try:
                start = timeit.default_timer()
                result_search_for_eyes_contact = analysis_main.analyse(neuro.file_name,bucket,"search_for_eyes_contact")
                # res_1 = result_search_for_eyes_contact.run()
                res_json = json.dumps(res_1)
                json_object = json.loads(res_json)
                stop = timeit.default_timer()
                time_capture = stop - start 
                if result_search_for_eyes_contact != '':
                    results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,ref_id,analyzer_type="Eye",scenario='search_for_eyes_contact')
                    neuro.no_eyes_contact={"analysis_result":json_object,"results":results,'timeduration':time_capture}
                    neuro.save()
                else:
                    neuro.no_eyes_contact={"analysis_result":json_object,"results":[],'timeduration':time_capture}
                    neuro.save()
            except KeyError as e:
                neuro.no_eyes_contact={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()
            except IndexError as e:
                neuro.no_eyes_contact={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()
           
        elif scenario =="search_for_numerosity_principle" and (file_type=='image' or file_type=='video'): #or file_type=='video'
            try:
                start = timeit.default_timer()
                result_search_for_clusters = analysis_main.analyse(neuro.file_name,bucket,"search_for_clusters")
                res_1 = result_search_for_clusters.run()
                res_json = json.dumps(res_1)
                json_object = json.loads(res_json)
                stop = timeit.default_timer()
                time_capture = stop - start 
                if result_search_for_clusters != '':
                    results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,ref_id,analyzer_type="Eye",scenario='search_for_numerosity_principle')
                    neuro.more_than_three_visual_clusters={"analysis_result":json_object,"results":results,'timeduration':time_capture}
                    neuro.save()
                else:
                    neuro.more_than_three_visual_clusters={"analysis_result":json_object,"results":[],'timeduration':time_capture}
                    neuro.save()
            except KeyError as e:
                neuro.more_than_three_visual_clusters={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()
            except IndexError as e:
                neuro.more_than_three_visual_clusters={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()
            
        elif scenario == 'search_for_more_than_two_people_in_close_proximity' and (file_type=='image' or file_type=='video'):
            try:
                start = timeit.default_timer()
                result_more_than_two_people_in_close_proximity = analysis_main.analyse(neuro.file_name,bucket,"search_for_more_than_two_people_in_close_proximity")
                res_1 = result_more_than_two_people_in_close_proximity.run()
                res_json = json.dumps(res_1)
                json_object = json.loads(res_json)
                stop = timeit.default_timer()
                time_capture = stop - start 
                if result_more_than_two_people_in_close_proximity != '':
                    results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,ref_id,analyzer_type="CP",scenario='search_for_more_than_two_people_in_close_proximity')
                    neuro.more_than_two_people_in_close_proximity={"analysis_result":json_object,"results":results,'timeduration':time_capture}
                    neuro.save()
                else:
                    neuro.more_than_two_people_in_close_proximity={"analysis_result":json_object,"results":[],'timeduration':time_capture}
                    neuro.save()
            except KeyError as e:
                neuro.more_than_two_people_in_close_proximity={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()
            except IndexError as e:
                neuro.more_than_two_people_in_close_proximity={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()

        elif scenario == 'search_for_women_apart_not_in_close_physicalproximity' and (file_type=='image' or file_type=='video'):
            try:
                start = timeit.default_timer()
                result_women_apart_not_in_close_physicalproximity = analysis_main.analyse(neuro.file_name,bucket,"search_for_more_than_two_people_in_close_proximity")
                res_1 = result_women_apart_not_in_close_physicalproximity.run()
                res_json = json.dumps(res_1)
                json_object = json.loads(res_json)
                stop = timeit.default_timer()
                time_capture = stop - start
                if result_women_apart_not_in_close_physicalproximity != '':
                    results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,ref_id,analyzer_type="CP",scenario='search_for_more_than_two_people_in_close_proximity')
                    neuro.women_apart_not_in_close_physicalproximity={"analysis_result":json_object,"results":results,'timeduration':time_capture}
                    neuro.save()
                else:
                    neuro.women_apart_not_in_close_physicalproximity={"analysis_result":json_object,"results":[],'timeduration':time_capture}
                    neuro.save()
            except KeyError as e:
                neuro.women_apart_not_in_close_physicalproximity={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()
            except IndexError as e:
                neuro.women_apart_not_in_close_physicalproximity={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()

        elif scenario == 'search_for_logo_intervention' and file_type=='video':
            try:
                start = timeit.default_timer()
                logo_intervention_analyse = analysis_main.analyse(neuro.file_name,bucket,"search_for_logo_intervention")
                res_1 = logo_intervention_analyse.run()
                res_json = json.dumps(res_1)
                json_object = json.loads(res_json)
                stop = timeit.default_timer()
                time_capture = stop - start
                if logo_intervention_analyse != '':
                    results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,ref_id,analyzer_type="Logo")
                    neuro.interrupt_flow_storyline={"analysis_result":json_object,"results":results,'timeduration':time_capture}
                    neuro.save()
                else:
                    neuro.interrupt_flow_storyline={"analysis_result":json_object,"results":[],'timeduration':time_capture}
                    neuro.save()
            except KeyError as e:
                neuro.interrupt_flow_storyline={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()
            except IndexError as e:
                neuro.interrupt_flow_storyline={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()
        
        elif scenario == 'search_for_overlay_text_background' and (file_type=='image' or file_type=='video'): #or file_type=='video'
            try:
                start = timeit.default_timer()
                search_txt_bkg_analyze = analysis_main.analyse(neuro.file_name,bucket,"search_txt_bkg")
                res_1 = search_txt_bkg_analyze.run()
                res_json = json.dumps(res_1)
                json_object = json.loads(res_json)
                stop = timeit.default_timer()
                time_capture = stop - start
                if search_txt_bkg_analyze != '':
                    results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,ref_id,analyzer_type="Background",scenario='search_txt_bkg')
                    neuro.overlay_text_background={"analysis_result":json_object,"results":results,'timeduration':time_capture}
                    neuro.save()
                else:
                    neuro.overlay_text_background={"analysis_result":json_object,"results":[],'timeduration':time_capture}
                    neuro.save()
            except KeyError as e:
                neuro.overlay_text_background={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()
            except IndexError as e:
                neuro.overlay_text_background={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()

        elif scenario == 'search_for_variation_in_terrain' and file_type=='video':
            try:
                start = timeit.default_timer()
                search_variation_in_terrain = analysis_main.analyse(neuro.file_name,bucket,"search_for_variation_in_terrain")
                res_1 = search_variation_in_terrain.run()
                res_json = json.dumps(res_1)
                json_object = json.loads(res_json)
                stop = timeit.default_timer()
                time_capture = stop - start
                if json_object['ViolationFound'] == True:
                    print(search_variation_in_terrain)
                    results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,ref_id,analyzer_type="Terrain",scenario='search_txt_bkg')
                    neuro.variation_in_terrain={"analysis_result":json_object,"results":results,'timeduration':time_capture}
                    neuro.save()
                else:
                    neuro.variation_in_terrain={"analysis_result":json_object,"results":[],'timeduration':time_capture}
                    neuro.save()
            except KeyError as e:
                neuro.variation_in_terrain={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()
            except IndexError as e:
                neuro.variation_in_terrain={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()
        
        elif scenario == 'search_for_body_parts' and (file_type=='video' or file_type=='image'):
            try:
                start = timeit.default_timer()
                search_for_bp = analysis_main.analyse(neuro.file_name,bucket,"search_body_parts")
                res_1 = search_for_bp.run()
                res_json = json.dumps(res_1)
                json_object = json.loads(res_json)
                stop = timeit.default_timer()
                time_capture = stop - start
                if search_for_bp != '':
                    results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,ref_id,analyzer_type="Body",scenario='search_body_parts')
                    neuro.body_part_isolation={"analysis_result":json_object,"results":results,'timeduration':time_capture}
                    neuro.save()
                else:
                    neuro.body_part_isolation={"analysis_result":json_object,"results":[],'timeduration':time_capture}
                    neuro.save()
            except KeyError as e:
                neuro.body_part_isolation={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()
            except IndexError as e:
                neuro.body_part_isolation={"analysis_result":[],"results":[],'timeduration':''}
                neuro.save()
                    
        print("%s IMPACT CALCULATIONS COMPLETED"%(scenario))
        # impacts_count = []

        if file_type=="image":
            attrs = vars(neuro)
            print(', '.join("%s: %s" % item for item in attrs.items()))
            print("im neuro inside",vars(neuro))
            # if 'more_than_two_consistent_characters' in neuro and 'lack_of_family_interactions' in neuro and 'women_together' in neuro and 'text_on_face' in neuro and 'images_on_right_words_to_left' in neuro and 'eyes_contact' in neuro:
            if 'more_than_two_people_in_close_proximity' in neuro and 'women_apart_not_in_close_physicalproximity' in neuro and 'lack_of_family_interactions' in neuro and 'images_on_right_words_to_left' in neuro and \
                'more_than_three_visual_clusters' in neuro and 'more_than_two_consistent_characters' in neuro and 'text_on_face' in neuro and 'no_eyes_contact' in neuro and 'overlay_text_background' in neuro:
                print("im scenario list")
                proj_obj.impacts_status={"status":"completed"}
                proj_obj.impacts_count=self.get_total_impacts(self.get_impacts_count(ref_id))
                proj_obj.updated_at=datetime.datetime.now()
                proj_obj.save()
                print("IMPACT CALCULATIONS COMPLETED")
        else:
            if 'text_on_face' in neuro and 'more_than_three_visual_clusters' in neuro and 'overlay_text_background' in neuro and 'more_than_two_people_in_close_proximity' in neuro and 'women_apart_not_in_close_physicalproximity' in neuro and 'images_on_right_words_to_left' in neuro and 'interrupt_flow_storyline' in neuro and 'lack_of_family_interactions' in neuro and 'variation_in_terrain' in neuro and 'body_part_isolation' in neuro and 'more_than_two_consistent_characters' in neuro and 'no_eyes_contact' in neuro:
                proj_obj.impacts_status={"status":"completed"}
                proj_obj.impacts_count=self.get_total_impacts(self.get_impacts_count(ref_id))
                proj_obj.updated_at=datetime.datetime.now()
                proj_obj.save()
                print("IMPACT CALCULATIONS COMPLETED")
        return None


    def get_analysis_detail_by_db_id(self,db_id):
        """ Get analysis detail for the particular project """
        neuro = NeuroAnalysis.objects().filter(ref_id=db_id).first()
        face_analysis = {}
        text_analysis = {}
        object_analysis = {}
        logo_analysis = {}

        if neuro:
            if "text_on_face" in neuro:
                analysis = neuro.text_on_face["analysis_result"]
                face_analysis=analysis["face_analysis"]
                text_analysis=analysis["text_analysis"]
            elif "lack_of_family_interactions" in neuro:
                analysis = neuro.lack_of_family_interactions["analysis_result"]
                face_analysis={"Faces":analysis["Faces"],"VideoMetadata":analysis["VideoMetadata"]}
            elif "lack_of_family_interactions" in neuro:
                analysis = neuro.lack_of_family_interactions["analysis_result"]
                face_analysis={"Faces":analysis["Faces"],"VideoMetadata":analysis["VideoMetadata"]}
            # elif "lack_of_family_interactions" in neuro:
            #     analysis = neuro.lack_of_family_interactions["analysis_result"]
            #     face_analysis={"Faces":analysis["Faces"],"VideoMetadata":analysis["VideoMetadata"]}

        resp ={
            "face_analysis":face_analysis,
            "text_analysis":text_analysis,
            "object_analysis":object_analysis,
            "logo_analysis":logo_analysis
        }
        return resp


    def upsert_feedback(self,data):
        """creating feedback against violations"""
        fdbck_obj=self.update_feedback(data)
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

        if fdbk:
            if "violation_name" in data:
                fdbk["violation_name"] = data["violation_name"]

            if "feedbacks" in data:
                fdbk["feedbacks"]=data["feedbacks"]

            if "is_violation" in data:
                fdbk["is_violation"] = data["is_violation"]

            fdbk["updated_at"]=datetime.datetime.now()

            fdbk.save()
        else:
            print("error - feedback not foound")

        return fdbk


theNAlignSetFactory = NAlignSetFactory()




