# Basic settings
from envparse import env
DB_HOST = env('DB_HOST', default='localhost')
DB_PORT = env('DB_PORT', cast=int, default=27017)
DB_NAME = env('DB_NAME', default='neuroslav')
VERSION = env('VERSION', default='0.0.1')
MAX_ATTEMPTS = 2
WELCOME_IMAGE = '965417/253f8b23ad1182b886c8'
