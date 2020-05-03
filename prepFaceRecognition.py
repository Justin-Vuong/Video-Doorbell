import Oauth
import requests
import UploadVid
import socket
import json
import webbrowser
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def getGPhotoAuth(): 
    gPhoto = Oauth.getAuth("https://www.googleapis.com/auth/photoslibrary.readonly")
    apiData = Oauth.parseApiData()
    credentials = Credentials(token=gPhoto["token"],
                              refresh_token=gPhoto["refresh_token"],
                              id_token=None,
                              token_uri="http://localhost:55555",
                              client_id=apiData["client_id"],
                              client_secret=apiData["client_secret"],
                              scopes="https://www.googleapis.com/auth/photoslibrary.readonly")
    return build("photoslibrary", "v1", credentials = credentials)

def getAlbumPics(authGPhotos):
    print("Searching Album List")
    results = authGPhotos.albums().list(pageSize=10, excludeNonAppCreatedData = False).execute()
    items = results["albums"]
    selectAlbum = []
    numAlbum = 0

    for item in items:
        print(str(numAlbum) + " -> " + item["title"])
        selectAlbum.append(item)
        numAlbum += 1

    num = input()
    print("Looking at Album")
    body = {"albumId":selectAlbum[int(num)]["id"], "pageSize":25}

    allPhotos = []
    allPhotos.append(selectAlbum[int(num)]["title"])
    pics = authGPhotos.mediaItems().search(body=body).execute()
    for a in pics["mediaItems"]:
        allPhotos.append(a["baseUrl"])

    while "nextPageToken" in pics:
        print("Reading Next Page...")
        body = {"albumId":selectAlbum[int(num)]["id"], "pageSize":25, "pageToken":pics["nextPageToken"] }
        pics = authGPhotos.mediaItems().search(body=body).execute()
        for a in pics["mediaItems"]:
            allPhotos.append(a["baseUrl"])

    print("Done reading: " + str(len(allPhotos)))
    return allPhotos
