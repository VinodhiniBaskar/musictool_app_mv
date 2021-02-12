# import sys
# import getopt
# import time
# import re
# import pickle
# import traceback
# import json
# # from mv_nalign.analysis.src.scenarios import logos, logo_intervention
# # from mv_nalign.analysis.src.scenarios import background_principle
# # from mv_nalign.analysis.src.aws_helper_service import AwsHelperService
# # from mv_nalign.analysis.detect_text import DetectText
# # from mv_nalign.analysis.detect_objects import DetectObjects
# # from mv_nalign.analysis.detect_faces import DetectFaces
# # from mv_nalign.analysis.src.data_preloader import PreLoader
# # from mv_nalign.analysis.postprocessing import search_for_overlay_text_background, search_for_logo_intervention,search_for_women_apart_not_in_close_physicalproximity,search_for_more_than_two_people_in_close_proximity,search_for_more_than_two_consistent_characters,search_for_lack_of_family_interactions,search_for_women_together,search_for_eyes_contact
# # from mv_nalign.analysis.src.img_base_impl.principle.variation import variation_in_terrain
# # from mv_nalign.analysis.src.vid_base_impl.scenarios import humanity_focused, close_w_faces_proximity
# # from mv_nalign.analysis.src.scenarios import numerosity_principle,family_interactions,body_parts,gaze,close_faces_proximity
# # from mv_nalign.analysis.src.scenarios.text_position import text_relative_position, text_over_face

# # def preload_instance(self,file,bucket): 
# #     role_arn = 'arn:aws:iam::274822417273:role/AmazonRekognitionServiceRoleCopy'
# #     pickle_path = "var/preloader_models/" + re.sub("[^a-zA-Z0-9\.]", "_", '%s_%s.pickle' % (bucket, file))
# #     try:
# #         with open(pickle_path, 'rb') as handle:
# #             p = pickle.load(handle)
# #     except FileNotFoundError:
# #         p = PreLoader(file, bucket, role_arn)
# #         p.preload()  # All aws data in this instance after call preload()
# #     return p.preload()

# def analyse(file,bucket,scenario):
#     try:
#         scenario_clb=''
#         role_arn = 'arn:aws:iam::274822417273:role/AmazonRekognitionServiceRoleCopy'
#         pickle_path = "var/preloader_models/" + re.sub("[^a-zA-Z0-9\.]", "_", '%s_%s.pickle' % (bucket, file))
#         try:
#             with open(pickle_path, 'rb') as handle:
#                 p = pickle.load(handle)
#         except FileNotFoundError:
#             p = PreLoader(file, bucket, role_arn)
#             p.preload()  # All aws data in this instance after call preload()
#         # p = PreLoader(file, bucket, role_arn)
#         # print(p)
#         # p.preload()
#         # p = p.
#         # print(preload_instance)
        
#         if scenario == 'search_for_text_relative_position':
#             analyzer = text_relative_position.TextObjectsRelative(p) #Completed

#         elif scenario == 'search_for_logo_intervention':
#             analyzer = logo_intervention.LogoIntervention(p) #Completed
        
#         elif scenario == 'search_for_clusters':
#             analyzer = numerosity_principle.NumerosityPrinciple(p) #Completed

#         elif scenario == 'search_for_more_than_two_consistent_characters':
#             analyzer = humanity_focused.HumanityFocused(p) # Completed

#         elif scenario == 'search_for_lack_of_family_interactions':
#             analyzer = family_interactions.FamilyInteractions(p)# Completed
            
#         elif scenario == 'search_for_text_face_overlap':
#             analyzer = text_over_face.TextOverFace(p) #Completed
            
#         elif scenario == 'search_for_eyes_contact':
#             analyzer = gaze.Gaze(p) #Completed

#         elif scenario == 'search_for_more_than_two_people_in_close_proximity':
#             analyzer = close_faces_proximity.CloseProximity(p) #completed

#         elif scenario == 'search_for_women_apart_not_in_close_physicalproximity':
#             analyzer = close_w_faces_proximity.WomenCloseProximity(p) #completed

#         elif scenario == 'search_txt_bkg':
#             analyzer = background_principle.BackgroundPrinciple(p) #COMPLETED
        
#         elif scenario == 'search_for_variation_in_terrain':
#             analyzer = variation_in_terrain.VariationInTerrainPrinciple(p) #completed
        
#         elif scenario == 'search_body_parts':
#             analyzer = body_parts.BodyParts(p) #completed

#         elif scenario:
#             print("[%s] Error: Unknown option type.\n" % time.time())

#         try:
#             print("call run detections")
#             if scenario_clb:
#                 res = analyzer.run_detection(file, bucket, callback=scenario_clb)
#             else:
#                 print(file)
#                 res_1 = analyzer.run()
#                 res_json = json.dumps(res_1)
#                 json_object = json.loads(res_json)
                
#                 # print(res)
                
#                 # results=self.generate_end_impacts_results(json_object,proj_obj.file_url,file_type,ref_id,analyzer_type="Women",scenario='search_for_more_than_two_consistent_characters')
                
#                 # print(generate_impacts_based_on_scenario(file,scenario))
#                 # print(file,bucket)
#                 # res = analyzer
#                 # print(res)
#         except IOError as e:
#             print('[%s] Error: FS Operation failed: %s' % (time.time(), e.strerror))
#     except ValueError as e:
#         print('[%s] Error: %s\n' % (time.time(), e))
        
#     return res
    





