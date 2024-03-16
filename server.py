import socketserver
import sys
from util.request import Request
import db
from bson.json_util import dumps, loads 
import html
import bcrypt
import uuid
import hashlib
import datetime
import random
from routes import sendRoute
from response import buildWSHeaders

class MyTCPHandler(socketserver.BaseRequestHandler):

    websocket_connections = []

    def send(self, response):
        self.request.sendall(response)

    def switchProtocols(self, status, headers):
        response = status + buildWSHeaders(headers) + b'\r\n'
        self.send(response)

    def handle(self):
        received_data = self.request.recv(2048) # reads up to 2048 bytes
        print(self.client_address, "sent", len(received_data), "bytes")

        request = Request(received_data)  # Create the Request object

        if "multipart/form-data" in request.headers["Content-Type"]:
            request.parse_multipart(received_data, request.headers, self)

        sendRoute(request.method, request.path, request.headers, request.body, self)  # Call sendRoute after handling the request

def main():
    host = "0.0.0.0"
    port = 8080

    # allows you to reuse port
    socketserver.TCPServer.allow_reuse_address = True

    #starts tcp server
    server = socketserver.ThreadingTCPServer((host, port), MyTCPHandler)

    print("Listening on port " + str(port))
    sys.stdout.flush()
    sys.stderr.flush()

    # starts server
    server.serve_forever()

if __name__ == "__main__":
    main()
