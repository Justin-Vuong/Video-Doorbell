import webbrowser
import socket
import sys
import requests
import json
import requests
import gdata.youtube
import gdata.youtube.service
import os

def getAuth():
    HOST = ''   # Symbolic name, meaning all available interfaces
    PORT = 55555 # Arbitrary non-privileged port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #Bind socket to local host and port
    try:
        s.bind((HOST, PORT))
    except socket.error as msg:
        print('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
        sys.exit()
    #Start listening on socket
    s.listen(1)
    
    #Open link in browser
    webbrowser.open_new("https://accounts.google.com/o/oauth2/auth?client_id=223289540342-j8o4l4p6meo9pbnq1ju3dq8jv6o278qa.apps.googleusercontent.com&redirect_uri=http://localhost:55555&response_type=code&scope=https://www.googleapis.com/auth/youtube.upload")

    conn, addr = s.accept()
    print ('Connected with ' + addr[0] + ':' + str(addr[1]))
    data = conn.recv(1024)
    data = data.decode("utf-8")
    data = data.split("&")[0]
    start = data.find("code=")
    data = data[start+5:]

    authDict = parseApiData(data)

    r = requests.post("https://oauth2.googleapis.com/token", authDict)

    conn.close()
    s.close()
    #os.system("pkill -3 chromium")
    
    refreshReq = r.text.split(",")
    authToken = refreshReq[0][21:len(refreshReq[0])-1]
    print("auth-> " + str(authToken))

    refresh_token = refreshReq[2][21:len(refreshReq[2])-1]
    print("refresh->" + str(refresh_token))
    
    tokens = {"token":str(authToken), "refresh_token":str(refresh_token)}
    
    return tokens

def parseApiData(data = None):
    apiAuth = open("/home/pi/Desktop/Video-Doorbell/client_secret.json", "r")
    apiAuth = apiAuth.read()
    apiAuth = json.loads(apiAuth)

    authReqDict = {}
    if data != None:
        authReqDict["code"] = data 
    authReqDict["client_id"] = apiAuth["client_id"]
    authReqDict["client_secret"] = apiAuth["client_secret"]
    authReqDict["redirect_uri"] = "http://localhost:55555"
    authReqDict["grant_type"] = "authorization_code"
    authReqDict["response_type"] = "code"
    return authReqDict