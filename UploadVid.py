import argparse
import http.client
import httplib2
import os
import random
import time

import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

def youtube_login(yt_auth, settings):
    try:
        initialize_upload(yt_auth, settings)
    except HttpError:
        print ('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))

# Authorize the request and store authorization credentials.
def get_authenticated_service(in_token, in_refresh_token, in_client_id, in_client_secret):
    flow = InstalledAppFlow.from_client_secrets_file('/home/pi/Desktop/Video-Doorbell/client_secret_doorbell.json', "https://www.googleapis.com/auth/youtube.upload")
    credentials = Credentials(token = in_token, refresh_token=in_refresh_token, id_token=None, token_uri="http://localhost:55555", client_id=in_client_id, client_secret=in_client_secret, scopes="https://www.googleapis.com/auth/youtube.upload")
    return build("youtube", "v3", credentials = credentials)

def initialize_upload(youtube, settings):
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
    # The chunksize parameter specifies the size of each chunk of data, in
    # bytes, that will be uploaded at a time. Set a higher value for
    # reliable connections as fewer chunks lead to faster uploads. Set a lower
    # value for better recovery on less reliable connections.
    #
    # Setting 'chunksize' equal to -1 in the code below means that the entire
    # file will be uploaded in a single HTTP request. (If the upload fails,
    # it will still be retried where it left off.) This is usually a best
    # practice, but if you're using Python older than 2.6 or if you're
    # running on App Engine, you should set the chunksize to something like
    # 1024 * 1024 (1 megabyte).
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
    except HttpError:
        if e.resp.status in RETRIABLE_STATUS_CODES:
            error = 'A retriable HTTP error %d occurred:\n%s' % (e.resp.status, e.content)
        else:
            raise
    except RETRIABLE_EXCEPTIONS:
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
