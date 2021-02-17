
import glob
import codecs
import uuid
from pymongo import MongoClient
import datetime


""" database instance """

client = MongoClient("mongodb://CBM_CD_CTN_V3:cbmcdctn123@10.0.20.65:27017/CBM_CD_CTN_V3")
ds_db = client["CBM_CD_CTN_V3"]


client = MongoClient("10.0.10.14",27017)
local_db=client["neuro_align"]


""" Model class """

class MFGGROUP(object):

    db_id = ''
    brand_name=''
    brand_pos =[]


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


def map_mfg_cat_brand(category_list):

    for  mfg in local_db["manufacturer"].find({}):
        local_coll=local_db[mfg["manufacturer_name"].lower()+"_brand_group"]
        for brand_list in sorted(local_db["brand_category_grouped"].distinct('brand')):
            print(brand_list)
            uniq_brand_list = []
            # print(sorted(local_db["brand_category_grouped_demo_13.28"].distinct('category',{ "manufacturer_id" : mfg["db_id"],"brand":brand_list})))
            # break
            for cat in sorted(local_db["brand_category_grouped"].distinct('category',{"brand":brand_list})):
                # print(cat)
                # based on category , get list of brands
                brands = ds_db[cat+'_DS'].aggregate([
                                        {

                                        "$match":{
                                            "Parent Company  [ Parent Company ]":{"$regex":mfg["manufacturer_name"].upper()}
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
    #         #     # print(brands)
    #         #     #from list of brands calculate pos value
                
                
                for brand in brands:
                    uniq_brand_list.append(brand["_id"])
            # print(set(uniq_brand_list))
            
            brands_list =[]  

            for k in sorted(set(uniq_brand_list)):
                single_total_sum=0
                for cat in sorted(local_db["brand_category_grouped_demo_13.28"].distinct('category',{ "manufacturer_id" : mfg["db_id"],"brand":k})):
                    cat_total_sum = 0
                    bask_learn = ds_db[cat+'_DS'].find({"Brand  [ Brand ]":k},{
                                "_id" : 0,
                                "Measures" : 0,
                                "Geography" : 0,
                                "Product" : 0,
                                "Brand  [ Brand ]" :0,
                                "Parent Company  [ Parent Company ]" : 0
            })
                    # print(type(bask_learn))

        # #        
            
        # #                                                                                                                             
                    for  i  in bask_learn:
                        # print(i)
                        cat_total_sum+=sum(i.values())
                    single_total_sum+=cat_total_sum
                    # print("cat %s = %s"%(cat,round(cat_total_sum/1000000,2)))

                    
                # print(brand_list)
                brands_list.append({"brand_name":k,"pos_value":round(single_total_sum/1000000,2)})
                # print(brands_list)

            mfgg = MFGGROUP()
            mfgg.db_id=uuid.uuid4().hex
            mfgg.brand_name=brand_list
            mfgg.brands_pos=brands_list
            local_coll.insert_one(mfgg.__dict__)
                # print(brand_list)






def create_mongo_db():
    print("entered function")
    files = glob.glob('../database/data/Mfg_cat_list.csv')
    # print(files)
    for file_ind in files:
        categorylist=insert_data_from_semrush_file(file_ind)
        # print(categorylist)
        map_mfg_cat_brand(categorylist)

if __name__ == '__main__':
    print("check")
    create_mongo_db()





