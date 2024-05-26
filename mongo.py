from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient


connection = AsyncIOMotorClient('mongodb://localhost:27017')
