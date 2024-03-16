import db
from bson.json_util import dumps, loads 
import html
import bcrypt
import uuid
import hashlib
import random
from response import *
from websocket import handshake

def sendRoute(method, path, headers, body, handler):
    status = b'HTTP/1.1 200 OK\r\n'
    # checks if user is already authenticated / still in their session
    if "Cookie" in headers:
        username = isAuthenticated(headers["Cookie"])
    else:
        username = "Guest"
    
    # GET
    if method == "GET":    
        if path == "/":
            content_type = "text/html; charset=utf-8"
            with open('public/index.html', 'r') as html_file:
                html_content = html_file.read()
            
            if username != "Guest":
                file_path = "/public/image/"+  username + ".jpg"
                modified_html = html_content.replace('{{image}}', file_path)
                handler.send(f"{status}\nContent-Type: {content_type}\n\n{modified_html}".encode())
            else:
                handler.send(sendResponse(status, "./public/index.html", content_type))
        
        # establishes websocket connection
        elif path == "/websocket":
            key = headers["Sec-WebSocket-Key"]
            handshake(key, handler, username)

        # serves any image, ensures security so that people can't access any file
        elif "/public/image" in path:
            content_type = "image/jpeg"
            secure = path.split("/public/image/")[1].replace("/", "")
            secure_path = "/public/image/" + secure
            try:
                handler.send(sendResponse(status, "." + secure_path, content_type))
            except:
                handler.send(send404())

        # serves css for homepage
        elif path == "/public/style.css":
            content_type = "text/css; charset=utf-8"
            handler.send(sendResponse(status, "." + path, content_type))
        
        #serves js for homepages
        elif path == "/public/functions.js":
            content_type = "text/javascript; charset=utf-8"
            handler.send(sendResponse(status, "." + path, content_type))
        
        # serves html for homepage
        elif path == "/public/index.html":
            content_type = "text/html; charset=utf-8"
            handler.send(sendResponse(status, "." + path, content_type))
        
        # tracks how many times user has visited
        elif path == "/visit-counter":
            handler.send(cookieResponse(headers))
        
        # loads chat history from database
        elif path == "/chat-history":
            cursor = db.messages.find({})

            data = list(cursor)
            for item in data:
                item['_id'] = str(item['_id'])

            json_data = dumps(data)
            setHeaders("application/json", len(json_data.encode()))
            handler.send(status + headerResponse() + b'\r\n' + json_data.encode())
        else:
            handler.send(send404())

    # POST
    elif method == "POST":
        # sends 200 response
        if path == "/chat-message":
            handler.send(send200())

        # registers new user
        if path == "/register":
            a = body.split("&password_reg=")
            password = html.escape(a[1])
            username = html.escape(a[0].split("username_reg=")[1])

            db.register(username, password) # adds to database
            handler.send(send301())

        # login
        elif path == "/login":
            a = body.split("&password_login=")
            password = html.escape(a[1])
            username = html.escape(a[0].split("username_login=")[1])
            if db.loginSuccessful(username, password):
                token = str(uuid.uuid4())

                # sets new cookie
                cookie = "\r\nSet-Cookie:auth=" + token + ';Max-Age=3600; HttpOnly'

                # salts and hashes auth token
                hashed_token = (hashlib.sha256(token.encode())).hexdigest()

                # stores in database
                db.users.update_one({"username": username}, {"$set":{'token':hashed_token}})
                handler.send(cookie301(cookie))
            else:
                handler.send(send301())
        
        # to update profile pic
        elif path == "/profile-pic":
            # check if logged in
            # save bytes of image as file 
            # store filename in users collection, use username as filename
            # respond with 302 redirect
            if username != "Guest":
                filename = username + ".jpg"
                file_path = 'public/image/' + filename
                with open(file_path, 'wb') as file:
                    file.write(body)
                db.users.update_one({"username": username}, {"$set":{'filename':filename}})
            handler.send(send302())
    
    # for deleting messages
    elif method == "DELETE":
        path = path.split("/")
        message_id = path[2]
        auth_token = db.returnToken(message_id) # retrieve auth token
        value = (headers["Cookie"]).split(";")  # retrieve cookie
        for i in value:
            if "auth" in i:
                cookie = i.split("=")[1]
        hashed_cookie = (hashlib.sha256(cookie.encode())).hexdigest()
        
        # users can only delete their own messages
        if hashed_cookie == auth_token:
            db.messages.delete_one({"id": message_id})
            handler.send(send200())
        else:
            handler.send(send403())
    
       