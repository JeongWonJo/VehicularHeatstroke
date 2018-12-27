import RPi.GPIO as GPIO
import time
import sys
import Adafruit_DHT
from math import atan
import buzzer
import gps
import telegram

# buzzer setup
BuzzPin = 37   # raw pin number
buzzer.setup(BuzzPin)


# gps initial info & necessary modules
gpgga_info = "$GPGGA,"
ser = serial.Serial ("/dev/ttyS0")              #Open port with baud rate
GPGGA_buffer = 0
NMEA_buff = 0
lat_in_degrees = 0
long_in_degrees = 0

# set up GPS sensor
GPIO.setmode(GPIO.BCM)

# set up PIR Sensor
GPIO.setup(17, GPIO.IN)

# connect to Telegram
bot = telegram.Bot(token="796092031:AAFDNeSPUpOS0FcaO_dHjPPA-Jp4mX0AUfE")

# set user id
chat_id = int(input("What is your Telegram ID Number?"))


def rec_video():
    # take a real-time video for 5 sec
    camera.start_preview()
    camera.start_recording('/home/pi/video.h264')
    sleep(5)
    camera.stop_recording()
    # convert .h264 format video to .mp4 video
    os.system("avconv -r 30 -i /home/pi/video.h264 -vcodec copy /home/pi/video.mp4")


def start():
    time.sleep(4)
    
    while True:
        # if PIR sensor is True == if motion is detected
        if GPIO.input(17):
            print ("Child is in the car")

            # check environmental condition (humidity and temperature)
            humid, temp = Adafruit_DHT.read_retry(11,27)
            # calculate the wet-bulb temperature
            wetBulb = temp*atan(0.151977* pow((humid+8.313659),0.5))+atan(temp+humid)-atan(humid-1.676331)+0.00391838* \
                      pow(humid,1.5)*atan(0.023101*humid)-4.686035

            # if wet-bulb temperature is above the safe range
            if wetBulb >= 15:
                # wait for 5 min
                time.sleep(600)

                #### telegram to notify parents
                # record video
                rec_video()
                # send a warning message
                bot.sendMessage(chat_id=chat_id, text="Your child is still in a scorching car!")
                # send a real-time video
                bot.sendVideo(chat_id=chat_id, video='/home/pi/video.mp4')

                # wait for 5 min
                time.sleep(300)

                #### buzzer to notify passengers
                # buzzer will be active for 2 min
                buzzer.beep(120)
                buzzer.destroy()

                # wait for 5 min
                time.sleep(300)

                #### telegram to notify 911
                # get GPS location data
                received_data = (str)(ser.readline())
                GPGGA_data_available = received_data.find(gpgga_info)
                if (GPGGA_data_available > 0):
                    GPGGA_buffer = received_data.split("$GPGGA,",1)[1]  #store data coming after "$GPGGA," string 
                    NMEA_buff = (GPGGA_buffer.split(','))               #store comma separated data in buffer
                    gps.GPS_Info()

                # record video
                rec_video()
                # send a warning message
                bot.sendMessage(chat_id=chat_id, text="Possible Child Heat Stroke Death in a Vehicle at Lat: "
                                + lat_in_degrees + "Long: " + long_in_degrees)
                # send a real-time video
                bot.sendVideo(chat_id=chat_id, video='/home/pi/video.mp4')

    # clean up GPIO pins
    GPIO.cleanup()


if __name__ == "__main__":
    start()
