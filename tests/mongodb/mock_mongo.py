import mongomock
import json

collection = mongomock.MongoClient().db.collection
with open("test_numerical.json", "r") as f:
    docs = json.load(f)
collection.insert_many(docs)
