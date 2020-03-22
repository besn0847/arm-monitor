import inotify.adapters
import threading
import requests
import imutils
import cv2
import re
from os.path import join
from resettabletimer import ResettableTimer
from skimage.measure import compare_ssim

DEBUG = False
DETECTION_THRESHOLD = 0.4
TARGET_DIR= "/data/pictures"
TIMER_TO = 30
RNN_URL = "http://192.168.1.206:5000/process"
REGEX = "Class: person with confidence: ([0-9.]+)"
SLACK_URL = "https://slack.com/api/files.upload" 
SLACK_API_TOKEN = "__INSERT_YOUR_SLACK_API_TOKEN_HERE__"
SLACK_CHANNEL = "#77570"
SLACK_BOT = "Catson"

running_ti = False
files = []

# Once the final frame is received, start processing
# The last frame is the new reference
def expired():
    global running_ti, files, cre
    running_ti = False
    max_proba = 0.0
    max_file = ""

    reference = files.pop()

    for f in files:
        proba = process(reference,f)
        if DEBUG : print("Proba : (",proba,")")
        if ( float(proba) > max_proba and float(proba) <= 1.0 ) :
            max_proba = float(proba)
            max_file = f
    
    if DEBUG : print("A person is detected with probability",max_proba,"in file",max_file)

    if max_proba > DETECTION_THRESHOLD :
        title = "A person has been detected with probability " + str(max_proba) + " in file " + max_file
        requests.post(SLACK_URL,
                            data={'token': SLACK_API_TOKEN,
                                    'channels': SLACK_CHANNEL,
                                    'username': SLACK_BOT,
                                    'title': title,
                                    'icon_emoji': ":robot_face:"},
                            files={'file': open(join(TARGET_DIR,max_file), 'rb')}
                      )

# extract deltas and trigger RNN
def process(ref, img):
    global cre
    
    _proba = "0.0"

    if DEBUG : print("Processing - ref : {0}, img : {1}".format(ref, img))
    imageR = cv2.imread(join(TARGET_DIR,ref))
    imageD = cv2.imread(join(TARGET_DIR,img))

    subimg = cv2.absdiff(imageD, imageR)
    subimg = cv2.threshold(cv2.cvtColor(subimg, cv2.COLOR_BGR2GRAY), 0, 255, cv2.THRESH_OTSU)[1]

    grayR = cv2.cvtColor(imageR, cv2.COLOR_BGR2GRAY)
    grayD = cv2.cvtColor(imageD, cv2.COLOR_BGR2GRAY)

    (score, diff) = compare_ssim(grayR, grayD, full=True)
    diff = (diff * 255).astype("uint8")

    thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    thresh += subimg

    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)

    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        if (w > 100 and h > 200) :
             if DEBUG : print("Found object : x = {0}, y = {1}, w = {2}, h = {3}".format(x, y, w, h))

             files = { 'image_file' : open(join(TARGET_DIR,img), 'rb') }
             values = {}
             req = requests.put(RNN_URL,files=files,data=values)

             if DEBUG : print(req.text)
             
             result = cre.search(req.text)
             if result : _proba = result.group(1)

             if DEBUG : print("Found a person with a probability of ", _proba)
    return _proba

# Look for files sequence and wait for final frame to received
def _main():
    i = inotify.adapters.Inotify()
    i.add_watch(TARGET_DIR)

    global running_ti, files, cre
    ti = ResettableTimer(TIMER_TO, expired)

    cre = re.compile(REGEX)

    # watch directory for new file creation
    while 1 > 0 :
        for event in i.event_gen(yield_nones=False, timeout_s=1):
            (_, type_names, path, filename) = event
            for type_name in type_names:
                if (type_name == "IN_CREATE") :
                   # start a new timer 
                   if ( running_ti ) :
                       ti.reset()
                       files.append(filename)

                   if ( not running_ti ) :
                       running_ti = True
                       ti = ResettableTimer(TIMER_TO, expired)
                       ti.start()

                       files = []
                       files.append(filename)

if __name__ == '__main__':
    _main()
