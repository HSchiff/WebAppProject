import json

crlf2 = b"\r\n\r\n"

class Request:

    def __init__(self, request: bytes):
        if request == b'':
            return
        

        data = request
        crlf2_split = data.split(crlf2, 1)          # splits body and headers
        first = crlf2_split[0].split(b"\r\n")       # splits the first part
        first_line = first[0].split(b' ')           # splits first line
        self.method = first_line[0].decode()
        self.path = first_line[1].decode()
        self.http_version = first_line[2].decode()
        self.headers = Request.parse_headers(first)
        req_body = crlf2_split[1]

        if "multipart/form-data" in self.headers["Content-Type"]:
            return

        # if self.method == "POST":
        #     try:
        #         post = json.loads(req_body)
        #         message = post.get("message")
        #         self.body = message
        #     except:
        #         self.body = req_body.decode()
        # else:
        self.body = req_body.decode()

    
    def parse_headers(h_list):
        headers = {}
        h_list.pop(0)
        for i in h_list:
            i = i.split(b":", 1)
            i[1] = i[1].strip()
            headers[i[0].decode()] = i[1].decode()

        if 'Content-Type' not in headers:
            headers['Content-Type'] = '' 
        
        return headers
    
    def parse_multipart(self, data, headers, handler):
        length = int(headers["Content-Length"])
        boundary = headers["Content-Type"].split("boundary=", 1)[1].encode()
        body = data.split(b"\r\n\r\n", 1)[1]
        image = bytearray(body)
        while len(image) < length:
            received_data = handler.request.recv(2048)
            if not received_data:
                break

            image += received_data
        image = image.split(b'\r\n\r\n')[1]
        image = image.split(b"\r\n--" + boundary + b"--")[0]
        self.body = bytes(image)