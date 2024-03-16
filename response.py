import db
import hashlib
import datetime

# headers for responses
headers = {"Content-Type": None, "X-Content-Type-Options": "nosniff", "Content-Length": None}
status = b'HTTP/1.1 200 OK\r\n'

# response messages
def send404():
    response = "HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 36\r\n\r\nThe requested content does not exist".encode()
    return response

def send403():
    date = (datetime.datetime.now())
    response = f"HTTP/1.1 403 Forbidden\r\nDate: {date}\r\n\r\n".encode()
    return response

def send301():
    response = "HTTP/1.1 301 Moved Permanently\r\nContent-Length: 0\r\nLocation: /\r\n\r\n".encode()
    return response

# 301 response with cookie
def cookie301(cookie):
    response = ("HTTP/1.1 301 Moved Permanently\r\nContent-Length: 0\r\nLocation: /" + cookie + "\r\n\r\n").encode()
    return response

def send200():
    response = b'HTTP/1.1 200 OK\r\n'
    return response

def send302():
    response = b'HTTP/1.1 302 Found\r\nLocation: /\r\nContent-Type: text/html\r\nContent-Length: 0\r\n\r\n'
    return response

def send101(status, headers):
    return status + buildWSHeaders(headers) + b'\r\n'

# set unique response
def sendResponse(status, filename, content_type):
    with open(filename, 'rb') as file_o:
        file = file_o.read()
    setHeaders(content_type, len(file))
    return status + headerResponse() + b'\r\n' + file

def setHeaders(content_type, length):
    headers["Content-Type"] = content_type
    headers["Content-Length"] = length

# formats header response
def headerResponse():
    response = b''
    for i in headers:
        response += f'{i}: {headers[i]}'.encode()
        response += b'\r\n'
    return response

# checks if user is authenticated
def isAuthenticated(cookie_value):
    guest = "Guest"
    try:# if this fails then user is not authenticated
        value_list = cookie_value.split(";")
        for i in value_list:
            if "auth" in i:
                value = i
        num = value.split("=")[1]
        hashedtoken = (hashlib.sha256(num.encode())).hexdigest()
        db_record = list(db.users.find({"token": hashedtoken}))
        username = db_record[0]['username']
        return username
    except:
        return guest # returns guest if not authenticated

# sets visit counter with cookie
def cookieResponse(reqheaders):
    content_type = "text/plain; charset=utf-8"
    if "Cookie" not in reqheaders:
        message = "Visits = 1"
        value = "visits=1"
    else:
        #if authenticated, updates counter
        if "auth" in reqheaders["Cookie"]:
            value = reqheaders["Cookie"]
            value = value.split(";")
            for i in value:
                if "auth" not in i:
                    value = i
            new_total = str(int(value.split("=")[1]) + 1)
            message = "Visits = " + new_total
            value = "visits=" + new_total
        else:
            new_total = str(int((reqheaders["Cookie"]).split("=")[1]) + 1)
            message = "Visits = " + new_total
            value = "visits=" + new_total
    # creates response
    setHeaders(content_type, len(message.encode()))
    headers["Set-Cookie"] = value
    return buildResponse(message)

def buildResponse(message):
    return status + headerResponse() + b'\r\n' + message.encode()

# headersfor websockets
def buildWSHeaders(headers):
    response = b''
    for i in headers:
        response += f'{i}: {headers[i]}'.encode()
        response += b'\r\n'
    return response
