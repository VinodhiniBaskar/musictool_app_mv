import pytest
from mv_musictool import app as mv_app
import sys
from os import path
from mv_musictool import settings
import string
import random
import json
letters=string.ascii_letters
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

#files = {'file_metadata': open('mv_musictool/media/d29347da23e04b5eb35ff3dc7192cdb2_frame_0.jpg','rb')}
upload_payload = {
  "db_id": "",  "name": "check image",  "file_url": "string",  "file_type": "image",  "file_duration": "string"
}
impact_payload_dbid_keyword =      {
  "ref_id": "c165ea319a74439d8687ab7200d7b09d",
  "keyword": "Character does not make eye contact"
}        
    
mv_app.app.config['TESTING'] = False
mv_app.configure_app(mv_app.app)
mv_app.initialize_app(mv_app.app)

base_url = settings.BASE_URL_PREFIX
print("im base",base_url)

@pytest.fixture
def client():
    client = mv_app.app.test_client()
    # print("im client",client)
    yield client

def test_create_nalign(client):
    """create nalignset"""
    url = base_url + 'nalign/impacts'
    #url = 'api/v1/nalign/upload_file'
    resp = client.post(url,json=impact_payload_dbid_keyword)
    print(resp.status)
    print("im json",resp.json)
    assert (resp.status_code == 200) ##Positive Case
  
# def test_image_nalign(client):
#     """create nalignset"""
#     url = base_url + 'nalign/upload_payload'
#     #url = 'api/v1/nalign/upload_file'
#     resp = client.post(url,json=impact_payload_dbid_keyword)
#     print(resp.status)
#     print("im json",resp.json)
#     assert (resp.status_code == 400) ## Negative Case

# def test_create_nalign(client):
#     """create nalignset"""
#     resp = client.post(base_url + 'nalignset/', json=payload)
#     assert (resp.status_code == 201)


# def test_get_nalign_by_id(client):
#     """ get nalign based on id"""
#     cat_id = CustomnalignSet.objects(deleted=False).first().db_id
#     resp = client.get(base_url + 'nalignset/' + cat_id)
#     assert (resp.status_code == 200)



# def test_get_nalign(client):
#     """get list of nalign """
#     resp = client.get(base_url + 'nalignset/')
#     assert (resp.status_code == 200)


# def test_nalign_filter(client):
#     """ filter the nalign based on name and nalign """
    
#     payload_for_filter = []
#     payload_for_filter.append({"partial": "Home", "on_field": "name"})
#     payload_for_filter.append({"partial": "Home", "on_field": "nalign"})
#     for value in payload_for_filter:
#         resp = client.post(base_url + 'nalignset/filters/', json=value)
#         assert (resp.status_code == 200)