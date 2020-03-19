import cv2
import datetime
import time
import imutils
from imutils.video import VideoStream

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
        
        
RefFrameCount = 0

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
            videoIdentifier += 1
            vidClip = cv2.VideoWriter('Footage' + str(videoIdentifier) + '.avi', fourcc, 20.0, (640, 480))  
        isRecording = True
        loopback = ((bufferLength*fps)+(int(saveImg.num)-1)) % (bufferLength*fps)
         
    cv2.putText(frame, "Room Status {}: {}".format(RefFrameCount,text), (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255),2)
    cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0,0,255), 1)
    
    cv2.imshow("Security Feed", frame)
    cv2.imshow("Thresh", thresh)
    cv2.imshow("Frame Delta", frameDelta)
    key = cv2.waitKey(1) & 0xFF
      
    print("On num:" + str(saveImg.num) + " and isRecording is " + str(isRecording) + " Loopback is: " + str(loopback))
    
    if isRecording or loopback != -1:
        if saveImg.num == loopback:
            #Have not detected motion
            if isRecording:
                isRecording = False
            else:
                loopback = -1
        
        #Just detected motion, continue to record
            
        if saveImg.clip is not None:
            vidClip.write(saveImg.clip)
            print("Write")
    
    if cv2.waitKey(1) & 0xFF == ord('r'):
        if loopback == -1:
            videoIdentifier += 1
            vidClip = cv2.VideoWriter('Footage' + str(videoIdentifier) + '.avi', fourcc, 20.0, (640, 480))  
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

