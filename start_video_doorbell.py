import UploadVid
import Oauth
import MotionDetection
import time
from UploadVid import UploadQueue
from UploadVid import QueueNode

#For Emails run command
#python -m smtpd -n -c DebuggingServer localhost:1025

print("START")
yt_tokens = Oauth.getAuth("https://www.googleapis.com/auth/youtube.upload")
apiData = Oauth.parseApiData()

yt = UploadVid.get_authenticated_yt_service(yt_tokens["token"], yt_tokens["refresh_token"], apiData["client_id"], apiData["client_secret"])
newQueue = UploadQueue(yt)
MotionDetection.startCamera(newQueue)

print("good!")
