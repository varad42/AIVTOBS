from pymongo import MongoClient
from config import MONGO_URI

client = MongoClient(MONGO_URI)

db = client["ai_video_blog"]

users_collection = db["users"]
jobs_collection = db["jobs"]
blogs_collection = db["blogs"]

print("MongoDB connected")