import argparse
import http.client
import httplib2
import os
import random
import time
import threading

import google.oauth2.credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

class UploadQueue:
    def __init__(self, yt):
        self.nextVid = None
        self.lastVid = None
        self.isUploading = False
        self.youtube_login = yt    
            
    def addNewVid(self, vidNode):
        print("Added " + vidNode.vidSettings["title"] + ' ->' + str(self.isUploading))
        if self.nextVid == None:
            self.nextVid = vidNode
            self.lastVid = vidNode
            print("Empty Queue")
        else:
            self.lastVid.next = vidNode
            self.lastVid = vidNode
            print("adding to queue")
        
        if self.isUploading == False:
            print("Starting new thread")
            self.isUploading = True
            vidUploader = CustomThread(self)
            vidUploader.start()

class QueueNode:
    def __init__(self, videoSettings):
        self.vidSettings = videoSettings
        self.next = None

class CustomThread(threading.Thread):
    def __init__(self, queue): 
        threading.Thread.__init__(self) 
        self.queue = queue
    def run(self):
        while self.queue.nextVid:
            currentUpload = self.queue.nextVid
            self.queue.nextVid = currentUpload.next
            print("Starting upload to " + currentUpload.vidSettings["title"] + "...")
            youtube_upload(self.queue.youtube_login, currentUpload.vidSettings)
            print("Done upload to " + currentUpload.vidSettings["title"])
        self.queue.isUploading = False
        print("Closing thread")
        
def youtube_upload(yt_auth, settings):
    try:
        initialize_video(yt_auth, settings)
    except HttpError as e:
        print ('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))

# Authorize the request and store authorization credentials.
def get_authenticated_yt_service(in_token, in_refresh_token, in_client_id, in_client_secret):
    credentials = Credentials(token = in_token, refresh_token=in_refresh_token, id_token=None, token_uri="http://localhost:55555", client_id=in_client_id, client_secret=in_client_secret, scopes="https://www.googleapis.com/auth/youtube.upload")
    return build("youtube", "v3", credentials = credentials)

def initialize_video(youtube, settings):
  tags = None
  
  body=dict(
        snippet=dict(
          title=settings["title"],
          description=settings["description"]
        ),
        status=dict(
          privacyStatus="unlisted"
        )
  )

  # Call the API's videos.insert method to create and upload the video.
  insert_request = youtube.videos().insert(
    part=','.join(body.keys()),
    body=body,
    media_body=MediaFileUpload(settings["file"], chunksize=-1, resumable=True)
  )

  resumable_upload(insert_request)

# This method implements an exponential backoff strategy to resume a
# failed upload.
def resumable_upload(request):
  
  # Explicitly tell the underlying HTTP transport library not to retry, since
  # we are handling retry logic ourselves.
  httplib2.RETRIES = 1

  # Maximum number of times to retry before giving up.
  MAX_RETRIES = 10

  # Always retry when these exceptions are raised.
  RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
  http.client.IncompleteRead, http.client.ImproperConnectionState,
  http.client.CannotSendRequest, http.client.CannotSendHeader,
  http.client.ResponseNotReady, http.client.BadStatusLine)

  # Always retry when an apiclient.errors.HttpError with one of these status
  # codes is raised.
  RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
  
  response = None
  error = None
  retry = 0
  while response is None:
    try:
        print ('Uploading file...')
        status, response = request.next_chunk()
        if response is not None:
            print("response")
            print(response)
            if 'id' in response:
              print ('Video id "%s" was successfully uploaded.' % response['id'])
            else:
              exit('The upload failed with an unexpected response: %s' % response)
    except HttpError as e:
        if e.resp.status in RETRIABLE_STATUS_CODES:
            error = 'A retriable HTTP error %d occurred:\n%s' % (e.resp.status, e.content)
        else:
            raise
    except RETRIABLE_EXCEPTIONS as e:
        error = 'A retriable error occurred: %s' % e

    if error is not None:
        print (error)
        retry += 1
        if retry > MAX_RETRIES:
            exit('No longer attempting to retry.')

        max_sleep = 2 ** retry
        sleep_seconds = random.random() * max_sleep
        print ('Sleeping %f seconds and then retrying...' % sleep_seconds)
        time.sleep(sleep_seconds)
