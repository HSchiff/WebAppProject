
import hashlib
import base64
from response import *
from json import loads, dumps
import html
from routes import *
import random
import db

# sets headers
rheaders = {"X-Content-Type-Options": "nosniff", "Connection": "Upgrade", "Upgrade": "websocket"}

# websocket handshake
def handshake(key, handler, username):
    status = b"HTTP/1.1 101 Switching Protocols\r\n"
    key = key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    accept_key = base64.b64encode((hashlib.sha1(key.encode())).digest())
    rheaders["Sec-WebSocket-Accept"] = accept_key.strip().decode("ascii")
    handler.switchProtocols(status, rheaders)
    parse_frames(handler, username)

def parse_frames(handler, username):
    from server import MyTCPHandler
    MyTCPHandler.websocket_connections.append(handler)
    leftover_frame = b''
    while True:
        if leftover_frame == b'':
            frame = handler.request.recv(2048).strip()
        else:
            frame = leftover_frame
        
        # gets opcode
        opcode = getOp(frame)
        if opcode == 8:
            break
        fin = getFIN(frame) #fin bit
        mask_bit = getMask(frame) # mask bit
        payload_length = getPayloadLength(frame) # payload length
        masking_key = getMaskKey(frame) # masking_key
        current = getStart(frame, masking_key) # starting bit
        payload = b''
        payload += frame[current:]

        # keep receiving bytes for larger messages
        while len(payload) < payload_length:
            new_frame = handler.request.recv(2048).strip()
            payload += new_frame
        
        if len(payload) == payload_length:
            leftover_frame = b''
            
        # if there are remaining bytes, add to payload
        elif len(payload) > payload_length:
            remaining_bytes = payload[payload_length:]
            payload = payload[:payload_length]
            leftover_frame += remaining_bytes

        payload = getPayload(payload, mask_bit, payload_length, masking_key)
  
        # sends the message
        send_frame = createFrame(payload, username, frame)
        for socket in MyTCPHandler.websocket_connections:
            try:
                socket.request.sendall(send_frame)
                print("success")
            except:
                pass


def getPayload(frame, mask_bit, payload_length, masking_key):
    # after buffering
    current = 0
    payload = b''
    if mask_bit == 1: # if 1 then we must demask the payload
        i = 0
        while i < payload_length:
            currentBytes = frame[current: current + 4]
            payload += getMessage(currentBytes, masking_key) # demasks the payload
            # if payload not divisible by 4, get the end
            if i + 4 > payload_length and i < payload_length: 
                remainingBytes = payload_length - i
                currentBytes = currentBytes[current:current + remainingBytes]
                masking_key = masking_key[:remainingBytes]
                payload += getMessage(currentBytes, masking_key)
            current += 4
            i += 4

    if mask_bit == 0: # we do not need to mask
        current = 0
        # payload begins
        i = 0
        while i < payload_length:
            currentBytes = frame[current]
            payload += currentBytes.decode()
            current += 1
            i += 1
    return payload.decode()

# retrieves first bit
def getFIN(frame):
    fin = frame[0] >> 7
    return fin

# gets opcode to determine operation
def getOp(frame):
    opcode = frame[0] & 0b00001111
    return opcode

#if we need to demask payload
def getMask(frame):
    mask_bit = frame[1] >> 7
    return mask_bit

# retrieve masking key
def getMaskKey(frame):
    if getLength(frame) == 126:
        return frame[4:8]
    elif getLength(frame) == 127:
        return frame[10:14]
    else:
        return frame[2:6]

# get payload length
def getPayloadLength(frame):
    length = frame[1] & 0b01111111
    current = 2
    # assumes mask is 1
    if length == 126:
        payload_length = lengthBytes(frame, current, current + 2)
        # read next 2 bytes
    elif length == 127:
        payload_length = lengthBytes(frame, current, current + 8)
        # read next 8 bytes
    else:
        payload_length = length
    return payload_length

def getLength(frame):
    return frame[1] & 0b01111111

# determines starting bit based off of length
def getStart(frame, mask):
    current = 0
    #if mask == 1:
    if getLength(frame) == 126:
        current = 8
    elif getLength(frame) == 127:
        current = 14 # changed this
    else:
        current = 6
    return current

# this creates the frame to be sent over websockets
def createFrame(payload, username, frame):
    if payload[-1] != "}":
        if payload[-1] != "\"":
            payload = payload + "\""
        payload = payload + "}"
    payload = payloadBody(payload, username)
    #payload = payload.replace(" ", "")
    payload_length = len(payload)
    
    # creates payload
    first_byte = 0b10000001 # sets first bytes
    mask = 0
    # sets the masking bit and payload length
    if payload_length < 126:
        second_byte = (mask << 7) | payload_length
    else:
        second_byte = (mask << 7) | getLength(frame)
    header = bytes([first_byte, second_byte])
    integer_value = payload_length
    # converts message to bytes
    if getLength(frame) == 126:
        bytes_integer = integer_value.to_bytes(2, byteorder='big')
        frame = header + bytes_integer + payload.encode()
    elif getLength(frame) == 127:
        bytes_integer = integer_value.to_bytes(8, byteorder='big')
        frame = header + bytes_integer + payload.encode()
    else:
        bytes_integer = b''
        frame = header + payload.encode()
    return frame

def lengthBytes(frame, current, end):
    result = 0
    for b in frame[current:end]:
        result = result * 256 + int(b)
    return result

# converts bytes to message using masking key
def getMessage(currentBytes, mkey):
    return bytearray(b1 ^ b2 for b1, b2 in zip(currentBytes, mkey))

# loads message into json
def getMessageType(payload):
    json_data = loads(payload)
    return payload["messageType"]

# creates message with new id
def payloadBody(payload, username):
    json_data = loads(payload)
    message_id = str(random.randint(100000000000, 999999999999))
    json_data["username"] = username
    json_data["id"] = message_id
    for i in json_data:
        json_data[i] = html.escape(json_data[i])

    # saves message in database
    db.post_message(username, json_data["message"], message_id, json_data["messageType"])
    
        
    body = dumps(json_data)
    return body
