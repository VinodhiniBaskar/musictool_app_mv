from flask_restplus import reqparse

parser_arguments = reqparse.RequestParser()
parser_arguments.add_argument('db_id', type=str, required=True,  help='unique to the project')