

import json
import sys
import getopt
import time
import traceback
from mv_nalign.analysis.src.vid_base_impl.scenarios import gaze, humanity_focused, family_interactions, close_w_faces_proximity, close_faces_proximity
from mv_nalign.analysis.src.img_base_impl.principle.text_position import text_relative_position, text_over_face
from mv_nalign.analysis.src.img_base_impl.principle.numerosity import numerosity_principle
from mv_nalign.analysis.src.img_base_impl.principle.background import background_principle
from mv_nalign.analysis.src.img_base_impl.principle.variation import variation_in_terrain
from mv_nalign.analysis.src.img_base_impl.principle.body_parts import body_parts
from mv_nalign.analysis.src.data_preloader import PreLoader
# from dotenv import load_dotenv
# load_dotenv()


# this is the way you can use it
def main(argv):
    print('[%s] Launch\n' % time.time())

    try:
        opts, args = getopt.getopt(sys.argv[1:], "")
        [bucket, file] = args
        if not file:
            print('[%s] Error: arguments bucket and file should be defined.\n'
                  % time.time())
            sys.exit(2)

        # the ARN of an IAM role that gives Amazon Rekognition publishing permissions to the Amazon SNS topic.
        role_arn = 'arn:aws:iam::274822417273:role/AmazonRekognitionServiceRoleCopy'
        p = PreLoader(file, bucket, role_arn)
        p.preload()  # All aws data in this instance after call preload()

        try:
            analyzer = gaze.Gaze(p)
            launch_analyzer('mv_nalign/results/gaze.json', analyzer)

            analyzer = humanity_focused.HumanityFocused(p) #C
            launch_analyzer('mv_nalign/results/humanity.json', analyzer)

            analyzer = family_interactions.FamilyInteractions(p) #C
            launch_analyzer('mv_nalign/results/family.json', analyzer)

            analyzer = text_relative_position.TextObjectsRelative(p)
            print(analyzer)
            launch_analyzer('mv_nalign/results/text_left.json', analyzer)

            analyzer = text_over_face.TextOverFace(p)
            launch_analyzer('mv_nalign/results/text_on_face.json', analyzer)

            analyzer = numerosity_principle.NumerosityPrinciple(p)
            launch_analyzer('mv_nalign/results/clusters.json', analyzer)

            analyzer = close_faces_proximity.CloseProximity(p) #C
            launch_analyzer('mv_nalign/results/close_proximity.json', analyzer)

            analyzer = close_w_faces_proximity.WomenCloseProximity(p) #C
            launch_analyzer('mv_nalign/results/close_proximity_women.json', analyzer)

            analyzer = background_principle.BackgroundPrinciple(p)
            launch_analyzer('mv_nalign/results/text_background.json', analyzer)

            analyzer = variation_in_terrain.VariationInTerrainPrinciple(p)
            launch_analyzer('mv_nalign/results/variation_in_terrain.json', analyzer)

            analyzer = body_parts.BodyParts(p)
            launch_analyzer('mv_nalign/results/body_part.json', analyzer)

            print('[%s] Finished\n' % time.time())
        except IOError as e:
            print('[%s] Error: FS Operation failed: %s' % (time.time(), e.strerror))
    except getopt.GetoptError as e:
        print('[%s] Error: %s\n' % (time.time(), e))
        sys.exit(2)
    except ValueError as e:
        print('[%s] Error: %s\n' % (time.time(), e))
        sys.exit(2)
    except Exception as e:
        print('[%s] Unexpected!\n%s' % (time.time(), traceback.format_exc()))
        sys.exit(2)


def launch_analyzer(res_file, an):
    with open(res_file, 'w') as r:
        print('[%s]: Principle launched\n' % time.time())
        print("im",an.run)
        res = an.run()
        res_json = json.dumps(res)
        json_object = json.loads(res_json)
        res = json.dumps(json_object, indent=4)
        r.write(res)

if __name__ == "__main__":
    main(sys.argv[1:])