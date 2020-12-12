import os
from datetime import timedelta
DEBUG = True

SECRET_KEY = 'from_hd_to_fl,fromhdtofl'
PERMANENT_SESSION_LIFETIME = timedelta(days=7)

# dialect+driver://username:password@host:port/database
DIALECT = 'mysql'
DRIVER = 'pymysql'
USERNAME = 'FailMaster'
PASSWORD = 'fromhdtofl'
HOST = 'comp9900-from-hd-to-fl.cixq9pckihx2.ap-northeast-1.rds.amazonaws.com'
PORT = '3306'
DATABASE = 'from_hd_to_fl'

SQLALCHEMY_DATABASE_URI = "{}+{}://{}:{}@{}:{}/{}?charset=utf8".format(DIALECT,DRIVER,USERNAME,PASSWORD,HOST,PORT,DATABASE)

SQLALCHEMY_TRACK_MODIFICATIONS = False

# aws account and password
# aws: a1215481325@gmail.com
# aws: Ab1215481325
