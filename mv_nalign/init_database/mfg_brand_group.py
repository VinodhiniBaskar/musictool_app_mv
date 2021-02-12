
import codecs
from pymongo import MongoClient
from bson.objectid import ObjectId
import sys
import glob
from os import path
import ntpath
import sys
import ntpath
import uuid
import bson
# reload(sys)
# sys.setdefaultencoding('utf8')

# TODO: load the db name and es name from settings


#
# test code for mvlib
#

class SemrushCore():
    brand=''
    category=''

client1 = MongoClient("mongodb://CBM_CD_CTN_V3:cbmcdctn123@10.0.20.65:27017/CBM_CD_CTN_V3")
sdb1 = client1["CBM_CD_CTN_V3"]
client2 = MongoClient()
sdb2 = client2["neuro_align"]
db_collection2=sdb2["brand_category_grouped"]
# print(sdb1["ACNE TREATMENTS_LOYALTY_DOWNLOAD_CHILDREN"])

category_list=[]
def insert_data_from_semrush_file(filename):
    category_list =[]
    fp = codecs.open(filename, 'r', 'utf-8')
    lines = fp.readlines()
    # cnt = 0
    # print(lines)
    uni=[]
    nest=[]
    dia=[]
    for line in lines[1:]:
       
        cl = line.replace('\r', '').replace('\n','')
        sr = cl.split(',')
        if sr[0]:
            uni.append(sr[0])
        if sr[1]:
            nest.append(sr[1])
        if sr[2]:    
            dia.append(sr[2])
        # category_list.append(sr[0])
    
    category_list.append(uni)
    category_list.append(nest)
    category_list.append(dia)

    return category_list

def map_mfg_brand(categorylist):
    print("-----------mfg_brand-------------")
    # print(sdb2["manufacturer"].find({}))
    
        # print(mfg_obj["manufacturer_name"])
    for category in categorylist[0]:
        print("working")
        # print(category)
        # break
        # db_collection1=sdb1[category+"_LOYALTY_DOWNLOAD_CHILDREN"]
        
        brands = sdb1[category+'_DS'].aggregate([
                                {

                                "$match":{
                                    "Parent Company  [ Parent Company ]":{"$regex":'UNILEVER'}
                                    }
                                    
                                },
                                {
                                    
                                "$group":{
                                    "_id":{'Brand  [ Brand ]':'$Brand  [ Brand ]'}
                                    }
                                    
                                },
                                
                                
                                { "$unwind": "$_id" },
                                    { "$group": { "_id": "$_id.Brand  [ Brand ]" } }
                                    
                                
                                    
                                    ])

        for brand in brands:
            # print(v)
            # print(brand)
            srr = SemrushCore()
            # srr.manufacturer_id=mfg_obj["db_id"]
            srr.brand=brand["_id"]
            srr.category=category
            db_collection2.insert_one(srr.__dict__)

        #corner_case
    db_collection2.insert_one({"brand" : "DOVE",
"category" : "BEAUTY & PERSONAL CARE"})
        

def create_mongo_db():
    
    print("entered function")
    files = glob.glob('../mv_nalign/init_database/data/Mfg_cat_list.csv')
    print(files)
    for file_ind in files:
        categorylist=insert_data_from_semrush_file(file_ind)
        print(categorylist)
        # break
        map_mfg_brand(categorylist)
if __name__ == '__main__':
    
    create_mongo_db()
