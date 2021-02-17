from mongoengine import *

from mv_musictool import settings

# connect('neuro_align', alias='neuro-align-db', host=settings.MONGO_SERVER_NAME)
connect('mv_musictool', alias='mv-musictool-db', host=settings.MONGO_SERVER_NAME)

### Adding this to new_development env
class Project(Document):
    db_id = StringField(required=False)
    name = StringField(required=False)
    description = StringField(required=False)
    brand = StringField(required=False)
    product = StringField(required=False)
    file_url = StringField(required=False)
    file_duration = StringField(required=False)
    file_youtube = StringField(required=False)
    file_status= DynamicField(required=False)  
    multiple_video_upload_status= DynamicField(required=False)  
    multiple_image_upload_status = DynamicField(required=False)  
    thumbnail_url = StringField(required=False)
    file_type = StringField(required=False)
    # violations_count = StringField(required=False,default='1')
    published_at=DateTimeField(required=False)
    created_at = DateTimeField(required=False)  
    updated_at = DateTimeField(required=False)
    impacts_status = DynamicField(required=False)
    impacts_count = IntField(required=False)
    captions = StringField(required=False)
    is_uploaded = BooleanField(required=False,default=False)
    deleted=BooleanField(default=False)
    image_width = IntField(required=False)
    image_height = IntField(required=False)
    # Score = StringField(required=False)
    mono_link = StringField(required=False)


    meta = {
        'db_alias': 'mv-musictool-db',
        'collection': 'projects',
        'index_options': {},
        'index_background': True,
        'index_drop_dups': True,
        'index_cls': False
    }


class ProjectFile(Document):
    db_id = StringField(required=False)
    ref_id = StringField(required=False)
    image_url=StringField(required=False)
    image_timestamp = StringField(required=False)
    created_at = DateTimeField(required=False)
    updated_at = DateTimeField(required=False)
    # violations= ListField(required=False,default = [])
    # video_data=
    #impact
    #violation


    meta = {
        'db_alias': 'mv-musictool-db',
        'collection': 'projects_file',
        'index_options': {},
        'index_background': True,
        'index_drop_dups': True,
        'index_cls': False
    }



class TempFileStorage(Document):
    db_id = StringField(required=False)
    image = StringField(required=False)
    created_at = DateTimeField(required=False)
    updated_at = DateTimeField(required=False)


    meta = {
        'db_alias': 'mv-musictool-db',
        'collection': 'temp_file_storage',
        'index_options': {},
        'index_background': True,
        'index_drop_dups': True,
        'index_cls': False
    }



class NeuroAnalysis(Document):
    db_id = StringField(required=False)
    ref_id = StringField(required=False)
    file_name =StringField(required=False)
    file_type = StringField(required=False)
    created_at = DateTimeField(required=False)
    title_name = StringField(required=False)
    violation_status = StringField(required=False)
    more_than_two_consistent_characters = DynamicField(required = False)
    women_together = DynamicField(required = False)
    lack_of_family_interactions = DynamicField(required = False)
    text_on_face =DynamicField(required = False)
    images_on_right_words_to_left = DynamicField(required= False)
    no_eyes_contact = DynamicField(required= False)
    more_than_three_visual_clusters = DynamicField(required= False)
    more_than_two_people_in_close_proximity = DynamicField(required= False)
    women_apart_not_in_close_physicalproximity = DynamicField(required= False)
    interrupt_flow_storyline = DynamicField(required= False)
    overlay_text_background = DynamicField(required= False)
    variation_in_terrain = DynamicField(required= False)
    body_part_isolation = DynamicField(required= False)

    meta = {

        'db_alias': 'mv-musictool-db',
        'collection': 'neuro_analysis',
        'index_options': {},
        'index_background': True,
        'index_drop_dups': True,
        'index_cls': False
    }



class Feedback(Document):
    db_id = StringField(required=False)
    ref_id = StringField(required=False)
    violation_name=StringField(required=False)
    feedbacks=ListField(StringField(required=False),required=False)
    file_type=StringField(required=False,default="image")
    is_violation = BooleanField(required=False,default=False)
    created_at = DateTimeField(required=False)
    updated_at = DateTimeField(required=False)


    meta = {
        'db_alias': 'mv-musictool-db',
        'collection': 'neuro_feedback',
        'index_options': {},
        'index_background': True,
        'index_drop_dups': True,
        'index_cls': False
    }


