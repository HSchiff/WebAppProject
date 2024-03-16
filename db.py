from pymongo import MongoClient
from util.request import Request
import bcrypt
import html
from bson.json_util import dumps, loads 
import uuid
import random

mongo_client = MongoClient("mongo")
db = mongo_client["cse312"]

messages = db["messages"]
users = db["users"]
# messages.delete_many({}) # comment these out
# users.delete_many({})

# adds new message to messages collection
def post_message(sender, message, id, messageType):
    post = {
        "id": id,
        "username": sender,
        "message": message,
        "messageType": messageType
    }
    messages.insert_one(post)

# adds new user to users collection
def register_user(username, password, salt, num):
    user = {
        "id": num,
        "username": username,
        "password": password,
        "salt": salt
    }
    users.insert_one(user)
    
# checks if username is unique in database
def isUnique(username):
    for i in users.find():
        user = i["username"]
        if username == user:
            return False
    return True

def loginSuccessful(username, password):
    if not isUnique(username):
        # check if password is correct
        db_record = list(users.find({"username": username}))
        db_password = db_record[0]['password']
        db_salt = db_record[0]['salt']
        hashed_input = bcrypt.hashpw(password.encode(), db_salt)
        if db_password == hashed_input: # compare salted and hashed input to pw in database
            return True
        else:
            return False
        
    else:
        return False

# adds encryption to password, registers user
def register(username, password):
    if isUnique(username):
        salt = bcrypt.gensalt()
        pwd = bcrypt.hashpw(password.encode(), salt)
        num = str(random.randint(100000000000, 999999999999))
        register_user(username, pwd, salt, num) # adds to database
        return True
    else:
        # must choose another username
        return False

# returns auth token for current session
def returnToken(message_id):
    username = list(messages.find({"id": message_id}))[0]['username']
    auth_token = list(users.find({"username": username}))[0]['token']
    return auth_token

# opens files, reads data, and sends data
def serve_image(filename):
    try:
        with open(filename, "rb") as image_file:
            image_data = image_file.read()
            return image_data
    except FileNotFoundError:
        # Handle file not found error
        return None
