#!/usr/bin/env python3

# Use: Pushing button defines two points of a line
# LCD will display distance and velocity relative to the line 

import numpy as np
import RPi.GPIO as GPIO
from time import sleep
import lcddriver, threading, gps
import pprint
from collections import deque
from dateutil.parser import isoparse
import logging

logging.basicConfig(filename='MissingCalvinDataLog.txt', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class GPSDatapoint:
    '''A class for storing timestamps and GPS coordinates.'''
    def __init__(self, timestamp, lattitude, longitude):
        self.timestamp = timestamp
        self.lattitude = lattitude
        self.longitude = longitude

class DistanceDatapoint:
    '''A class for storing distances to calculate velocity.'''
    def __init__(self, timestamp, distance):
        self.timestamp = timestamp
        self.distance = distance

display = lcddriver.lcd()
line_coords = []
gps_log = [] # list of all GPS positions
distance_to_line_log = deque([], maxlen = 2)
velocity_queue = deque([], maxlen = 3) # Three most recent distances to line; for calculating velocity
start_point_2 = None
degrees_to_meters_conversion = np.array([111190, 74625]) # Only at lattitudes near Everett.

# TODO: Test and verify that same time/coords are not being logged twice - this would break my velocity calcs. 
# Logs coords
def log_coords():
    global gps_log
    while True:
        try:
            report = session.next()
            # print(report)
            if report['class'] == 'TPV':
                if hasattr(report, 'time'):
                    timestamp = isoparse(report.time)
                if hasattr(report, 'lat'):
                    lat = round(report.lat, 6)
                if hasattr(report, 'lon'):
                    lon = round(report.lon, 6)
                if hasattr(report, 'time') and hasattr(report, 'lat') and hasattr(report, 'lon'):
                    gps_log.append(GPSDatapoint(timestamp, lat, lon))
        except KeyError:
            pass

 
def button_callback(channel):
    '''Saves current position for use in drawing starting line.
    
    The two most recent points are used to determine the starting line.'''
    global line_coords, start_point_2
    current_position = gps_log[-1]
    if len(line_coords) == 0 or current_position.lattitude != line_coords[-1].lattitude or current_position.longitude != line_coords[-1].longitude: # Ensure new line point is different from previous to prevent dividing by zero in calculations.
        line_coords.append(current_position)
        if len(line_coords) > 1:
            start_point_2 = np.array([line_coords[-1].lattitude - line_coords[-2].lattitude, line_coords[-1].longitude - line_coords[-2].longitude]) * degrees_to_meters_conversion 

        display.lcd_clear()
        display.lcd_display_string('Point set.', 1)
        sleep(1)
        display.lcd_clear()            
    else:
        display.lcd_clear()
        display.lcd_display_string('Point already', 1)
        display.lcd_display_string('has been set.', 2)
        sleep(1)

def find_distance_and_velocity():
    '''Calculates distance and velocity relative to the starting line. 

    Units are in meters, positions are relative to the origin (line_coords[-2]) "x, y" (where x is north and y is east, but that's not important)'''
    logging.debug('find_distance_and_velocity function called')
    current_position = gps_log[-1]
    current_location = (np.array([current_position.lattitude, current_position.longitude]) - line_coords[-2]) * degrees_to_meters_conversion 
    start_line_direction_vector = start_point_2 / np.linalg.norm(start_point_2) 
    closest_point_on_line = np.dot(start_line_direction_vector, current_location) * start_line_direction_vector 
    delta_to_closest_point = (current_location - closest_point_on_line) # format: np.array[dx, dy]
    distance_to_line_log.append(DistanceDatapoint(current_position.timestamp, np.hypot(delta_to_closest_point[0], delta_to_closest_point[1])))
    if len(distance_to_line_log) > 1:
        for i in len(distance_to_line_log) - 1:
            velocity_queue.append(distance_to_line_log[i].distance - distance_to_line_log[i+1].distance / (distance_to_line_log[i+1].timestamp - distance_to_line_log[i].timestamp).seconds)

    #TODO: Verify log update does not cause errors because each position is tied to a timestamp. an update will push everything, 
        # If time_2 - time_1 = 0 skip, otherwise velocity devides by zero (Can this even occur?)
    
    try:
        velocity_to_line = np.average(velocity_queue) # Computes moving average over length of deque. 
    except RuntimeWarning: # When the list is empty. 
        velocity_to_line = 0
    return (distance_to_line_log[-1], velocity_to_line)

# Listen on port 2947 (gpsd) of localhost
session = gps.gps("localhost", "2947")
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

# Setup Raspbery Pi GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(25, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.add_event_detect(25, GPIO.RISING, callback = button_callback, bouncetime = 1000)

thread_object = threading.Thread(target=log_coords)
thread_object.start()
print('GPS log thread started.')

try:
    while len(gps_log) > 1:
        # Before line is drawn, display GPS coords.
        if len(line_coords) < 2:
            logging.debug('Less than 2 line_coords')
            display.lcd_display_string(f'lat: {gps_log[-1].lattitude}', 1)
            display.lcd_display_string(f'lon: {gps_log[-1].longitude}', 2)


            sleep(1)
        # After line is drawn, displays distance and... 
        # TODO:velocity relative to the line.
        else:
            logging.debug('2 or more line_coords')
            distance_to_line, velocity_to_line = find_distance_and_velocity()
            display.lcd_display_string(f'{int(distance_to_line)} m {int(distance_to_line % 1 * 100)} cm        ', 1)
            display.lcd_display_string(f'{round(velocity_to_line, 3)} m/s        ', 2)
            sleep(.5)
except KeyboardInterrupt:
    display.lcd_clear()
    GPIO.cleanup()
    print('Stopped.')