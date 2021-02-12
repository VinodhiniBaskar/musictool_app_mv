from mongoengine import *

from mv_nalign import settings

connect('neuro_align', alias='neuro-align-db', host=settings.MONGO_SERVER_NAME)



class BrandCategoryGroup(Document):
    
    brand = StringField(required=False)
    category=StringField(required=False)
    meta = {
        'db_alias': 'neuro-align-db',
        'collection': 'brand_category_grouped',
        'index_options': {},
        'index_background': True,
        'index_drop_dups': True,
        'index_cls': False
    }

