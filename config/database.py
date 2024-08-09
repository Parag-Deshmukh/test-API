from pymongo import MongoClient

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["course_db"]

# Export the collection
courses_collection = db["courses"]


