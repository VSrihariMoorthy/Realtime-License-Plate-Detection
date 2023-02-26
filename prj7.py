import cv2
import imutils
import numpy as np
import pytesseract
from PIL import Image
from picamera import PiCamera
import time
import smtplib
import pandas as pd
from time import sleep
import RPi.GPIO as GPIO
import board
import digitalio
import random
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)


import adafruit_character_lcd.character_lcd as characterlcd
lcd_rs = digitalio.DigitalInOut(board.D4)
lcd_en = digitalio.DigitalInOut(board.D15)
lcd_d7 = digitalio.DigitalInOut(board.D22)
lcd_d6 = digitalio.DigitalInOut(board.D9)
lcd_d5 = digitalio.DigitalInOut(board.D10)
lcd_d4 = digitalio.DigitalInOut(board.D27)
lcd_columns=16
lcd_rows=2
lcd = characterlcd.Character_LCD_Mono(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows)

p=PiCamera()

from difflib import SequenceMatcher

def similar(plate_text,word):
    a=SequenceMatcher(None,plate_text,word)
    return a.ratio()

def send_msg(t, plate_text):
    fine = random.randrange(100, 20000,50)
    mailmsg="""
    Name: %s
    License Number: %s
    Fine: Rs. %d"""%(t, plate_text, fine)
    server=smtplib.SMTP('smtp.office365.com',587) #Change the server and the port number corresponding to the sender's_mail_id
    server.starttls()
    server.login("sender's_mail_id", "password")
    server.sendmail("receiver's_mail_id", t, mailmsg)
    server.quit()
    

p.start_preview()
time.sleep(4)
p.capture('4.jpg')
p.stop_preview()

img = cv2.imread('4.jpg',cv2.IMREAD_COLOR)
img = cv2.resize(img, (620,480) )

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) #convert to grey scale
gray = cv2.bilateralFilter(gray, 11, 17, 17) #src dst dia sigmacolor sigmaspace bordertype
edged = cv2.Canny(gray, 30, 200) #Perform Edge detection

# find contours in the edged image, keep only the largest
# ones, and initialize our screen contour
cnts = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)
cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:10]
screenCnt = None
# loop over our contours
for c in cnts:
 # approximate the contour
 peri = cv2.arcLength(c, True)
 approx = cv2.approxPolyDP(c, 0.018 * peri, True)
 # if our approximated contour has four points, then
 # we can assume that we have found our screen
 if len(approx) == 4:
  screenCnt = approx
  break

if screenCnt is None:
 detected = 0
 print("No contour detected")

else:
 detected = 1

if detected == 1:
 cv2.drawContours(img, [screenCnt], -1, (0, 255, 0), 3)


# Masking the part other than the number plate
mask = np.zeros(gray.shape,np.uint8)
new_image = cv2.drawContours(mask,[screenCnt],0,255,-1,)
new_image = cv2.bitwise_and(img,img,mask=mask)

# Now crop
(x, y) = np.where(mask == 255)
(topx, topy) = (np.min(x), np.min(y))
(bottomx, bottomy) = (np.max(x), np.max(y))
Cropped = gray[topx:bottomx+1, topy:bottomy+1]


cv2.imshow('cropped',Cropped)
im1=cv2.imwrite('Cropped.png',Cropped)


#Read the number plate6
#text = pytesseract.image_to_string(Cropped, config='--psm 9')
text=pytesseract.image_to_string(Image.open('Cropped.png'),lang='eng', config='--oem 3 --psm 11 ')

plate_text=[]
for i in text:
    if i.isalnum():
        plate_text.append(i)
plate_text="".join(plate_text)
cv2.imshow('image',img)
print("Detected Number is:",plate_text)
plate_text=str(plate_text)

cv2.waitKey(0)

cv2.destroyAllWindows()

num=""

ob=pd.read_csv('/home/pi/Desktop/data.csv') #Change the address to the location containing data.csv
for i in ob['Number']:
    if similar(plate_text,i)>0.5:
        print("Vehicle Registration Number Detected")
        num=i
        print(i)
        msg = "Reg No:" + str(num)
        t=ob.loc[ob['Number']==i,'emailid'].values[0]
        lcd.message= msg
        send_msg(t, num)
        sleep(30)
        lcd.clear()        
        
if num=="":
    msg="Not Regd"
    lcd.message= msg
    


