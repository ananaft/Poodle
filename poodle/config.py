import pymongo
import os
import sys

# MongoDB
CLIENT = pymongo.MongoClient()
DB = eval(f'CLIENT.{sys.argv[-1]}')

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
