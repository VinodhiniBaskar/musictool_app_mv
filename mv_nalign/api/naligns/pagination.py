from flask_restplus import reqparse

pagination_arguments = reqparse.RequestParser()
pagination_arguments.add_argument('page', type=int, required=False, default=1, help='Page number')
pagination_arguments.add_argument('bool', type=bool, required=False, default=1, help='Page number')
pagination_arguments.add_argument('per_page', type=int, required=False, choices=[-1,2,3,4,5,6,10,15, 20,25, 30, 40, 50],
                                  default=50, help='Results per page {error_msg}')
pagination_arguments.add_argument('sort_field', type=str, required=False, help='String')
pagination_arguments.add_argument('order', type=str, required=False  , help='String')
pagination_arguments.add_argument('search_key', type=str, required=False  , help='String',default='')