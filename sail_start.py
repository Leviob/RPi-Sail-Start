# Use: Pushing button defines two points of a line
# LCD will display distance and velocity relative to the line 

import numpy as np
import RPi.GPIO as GPIO
from time import sleep
import lcddriver, threading, gps
import pprint

display = lcddriver.lcd()

line_coords = []
gps_log = [[0,0,0]]
degrees_to_meters_conversion = np.array([111190, 74625]) #only at lattitudes near everett.

# Listen on port 2947 (gpsd) of localhost
session = gps.gps("localhost", "2947")
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(25, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.add_event_detect(25, GPIO.RISING, callback = button_callback)

# Logs coords
def log_coords():
    global gps_log
    while True:
        try:
            report = session.next()
            # print(report)
            if report['class'] == 'TPV':
                if hasattr(report, 'time'):
                    timestamp = report.time
                if hasattr(report, 'lat'):
                    lat = round(report.lat, 6)
                if hasattr(report, 'lon'):
                    lon = round(report.lon, 6)
                    gps_log.append([timestamp, lat, lon])
        except KeyError:
            pass

# On button press, appends current location to list of line coords. format: np.array([lat, lon])
def button_callback(channel):
    global line_coords
    line_coords.append(np.array([gps_log[-1][1], gps_log[-1][2]]))
    display.lcd_clear()
    display.lcd_display_string('Point set.', 1)
    sleep(1)
    display.lcd_clear()

thread_object = threading.Thread(target=log_coords)
thread_object.start()
print('GPS log thread started.')

try:
    while True:
        # Before line is drawn, display GPS coords.
        if len(line_coords) < 2:
            display.lcd_display_string(f'lat: {gps_log[-1][1]}', 1)
            display.lcd_display_string(f'lon: {gps_log[-1][2]}', 2)
            sleep(1)
        # After line is drawn, displays distance and... 
        # TODO:velocity relative to the line.
        else:
            start_point_1 = np.array([0,0]) # Origin (line_coords[-2] - line_coords[-2])
            start_point_2 = np.array(line_coords[-1] - line_coords[-2]) * degrees_to_meters_conversion # relative to origin, converts degrees to meters
            current_location = (np.array([gps_log[-1][1], gps_log[-1][2]]) - line_coords[-2]) * degrees_to_meters_conversion # relative to origin, in meters
            line_direction_vector = start_point_2 / np.linalg.norm(start_point_2) # This breaks when both line points are equal (divides by zero)
            closest_point_on_line = np.dot(line_direction_vector, current_location) * line_direction_vector # relative to origin, in meters
            difference_to_line = (current_location - closest_point_on_line) # format: [meters, meters]
            distance_to_line = np.hypot(difference_to_line[0], difference_to_line[1]) # units: meters
            # Maybe save timestamps with GPS data to reference in generating position log?
            display.lcd_display_string(f'{int(distance_to_line)} m {int(distance_to_line % 1 * 100)} cm        ', 1)
            sleep(.5)
except KeyboardInterrupt:
    print('Stopped.')
    display.lcd_clear()
    GPIO.cleanup()