import smtplib
from email.message import EmailMessage

#python -m smtpd -n -c DebuggingServer localhost:1025

def sendEmail(names):
    msg = EmailMessage()
    msg.set_content(generateEmail(names))
    msg['Subject'] = "Motion Detected at your door!"
    msg['From'] = "3029doorbell@gmail.com"
    msg['To'] = "vuong.justin01@gmail.com"
    s = smtplib.SMTP(host='localhost', port=1025)
    s.send_message(msg)
    s.quit()

def generateEmail(names):
    message = "Motion was detected and a video was uploaded to your Youtube.\n"
    
    if len(names) == 0:
        message += "Did not see anyone in the video."
    else:
        addedName = []
        message += "Here are the people in that video:"
        for person in names:
            if person not in addedName:
                message += "I saw " + person + "\n"
                addedName.append(person)
            
    return message
