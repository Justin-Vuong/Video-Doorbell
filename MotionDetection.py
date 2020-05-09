import cv2
import datetime
import time
import datetime
import imutils
from imutils.video import VideoStream
import UploadVid
import threading
from UploadVid import QueueNode
import face_recognition
import FaceProcessing
import GenerateEmail

class FrameBuffer:
    def __init__(self):
        self.clip = None
        self.next = None
        self.num = None
    
class VidBuffer:
    #Head is the oldest frame in the shot
    #Last points to the most recent frame
    
    def __init__(self, inFPS, inBufferLength):
        self.fps = inFPS
        self.bufferLength = inBufferLength
        
        #Initializing buffer structure
        self.head = FrameBuffer()
        self.head.num = 0
        currentLoop = FrameBuffer()
        currentLoop.num = 1
        self.head.next = currentLoop
        for index in range(2, int(self.fps) * int(self.bufferLength)):
            print("initializing " + str(index))
            nextLoop = FrameBuffer()
            nextLoop.num = index
            currentLoop.next = nextLoop
            currentLoop = nextLoop
        currentLoop.next = self.head

def startCamera(queue):        
    RefFrameCount = 0
    detector = cv2.CascadeClassifier("pi-face-recognition/haarcascade_frontalface_default.xml")
    names = []
            
    vs = VideoStream(src=0).start()
    fourcc = cv2.VideoWriter_fourcc(*'XVID')

    #For Recording
    bufferLength = 5
    fps = 20
    vidLoop = VidBuffer(bufferLength,fps)
    saveImg = vidLoop.head
    videoIdentifier = 0
    loopback = -1
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    isRecording = False
    time.sleep(2)

    while True:
        frame = vs.read()
        text = "Nobody"
        if frame is None:
            print("Can't read form camera")
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21,21), 0)
        
        if RefFrameCount % 250 == 0:
            firstFrame = gray
        RefFrameCount+= 1   
        
        frameDelta = cv2.absdiff(firstFrame,gray)
        thresh = cv2.threshold(frameDelta, 25,255,cv2.THRESH_BINARY)[1]
        
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        
        for c in cnts:
            if cv2.contourArea(c) < 250:
                continue
            (x,y,w,h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)
            text = "Motion!"
       
        if len(cnts) > 0:
            if loopback == -1:
                name_time = datetime.datetime.now().strftime("%H:%M_%A_%B_%d_%Y")
                vidClip = cv2.VideoWriter("SavedClips/" + name_time + ".avi", fourcc, 20.0, (640, 480))
            isRecording = True
            loopback = ((bufferLength*fps)+(int(saveImg.num)-1)) % (bufferLength*fps)
        
        #Prepare for facial recognition
        grayFR = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rgbFR = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # detect faces in the grayscale frame
        rects = detector.detectMultiScale(grayFR, scaleFactor=1.1, 
        minNeighbors=5, minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE)
        boxesFaces = [(y, x + w, y + h, x) for (x, y, w, h) in rects]
        encodings = face_recognition.face_encodings(rgbFR, boxesFaces)

        #Run facial recognition
        FaceProcessing.runFacialRecognition(frame, encodings, boxesFaces, names)
        
        cv2.putText(frame, "Room Status {}: {}".format(RefFrameCount,text), (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255),2)
        cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0,0,255), 1)
        
        cv2.imshow("Security Feed", frame)
        #cv2.imshow("Thresh", thresh)
        #cv2.imshow("Frame Delta", frameDelta)
        key = cv2.waitKey(1) & 0xFF
          
        #print("On num:" + str(saveImg.num) + " and isRecording is " + str(isRecording) + " Loopback is: " + str(loopback))
        
        if isRecording or loopback != -1:
            if saveImg.num == loopback:
                #Have not detected motion
                if isRecording:
                    isRecording = False
                else:
                    loopback = -1
                    
                    #Upload Video
                    settings = {}
                    settings["file"] = "/home/pi/Desktop/Video-Doorbell/SavedClips/" + name_time + ".avi"
                    settings["title"] = name_time
                    settings["description"] = "Video Capture from " + name_time + "\n"

                    for person in names:
                        settings["description"] += "Found " + person + " at your door."
                                               
                    UploadVid.youtube_upload(queue.youtube_login, settings)
                    video = QueueNode(settings)
                    queue.addNewVid(video)
                    
                    #Send email
                    GenerateEmail.sendEmail(names)
                    names = []
            
            #Just detected motion, continue to record
                
            if saveImg.clip is not None:
                vidClip.write(saveImg.clip)
                print("Write")
        
        if cv2.waitKey(1) & 0xFF == ord('r'):
            if loopback == -1:
                name_time = datetime.datetime.now().strftime("%H:%M_%A_%B_%d_%Y")
                vidClip = cv2.VideoWriter("SavedClips/" + name_time + ".avi", fourcc, 20.0, (640, 480))
            isRecording = True
            loopback = ((bufferLength*fps)+(int(saveImg.num)-1)) % (bufferLength*fps)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
        saveImg.clip = frame
        saveImg = saveImg.next
        
        if key == ord("q"):
            break

    vs.stop()
    cv2.destroyAllWindows()