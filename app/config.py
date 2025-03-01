import os
from dotenv import load_dotenv
load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'you-will-never-guess'
    # Connect to local MongoDB by default; override via environment if needed.
    MONGO_URI = os.getenv('MONGO_URI') or 'mongodb://localhost:27017/ai_diary'
