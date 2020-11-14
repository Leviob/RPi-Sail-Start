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

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.disable(logging.CRITICAL)

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
start_line_point_2 = None
degrees_to_meters_conversion = np.array([111190, 74625]) # Only at lattitudes near Everett.
prev_time = None

def button_callback(channel):
    '''Saves current position for use in drawing starting line.
    
    The two most recent points are used to determine the starting line.'''
    global line_coords, start_line_point_2
    current_position = gps_log[-1]
    if len(line_coords) == 0 or current_position.lattitude != line_coords[-1].lattitude or current_position.longitude != line_coords[-1].longitude: # Ensure new line point is different from previous to prevent dividing by zero in calculations.
        line_coords.append(current_position)
        if len(line_coords) > 1:
            start_line_point_2 = np.array([line_coords[-1].lattitude - line_coords[-2].lattitude, line_coords[-1].longitude - line_coords[-2].longitude]) * degrees_to_meters_conversion 

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

    Units are in meters unless noted, positions are "x, y" (where x is north and y is east, but that's not important)
    location is relative to the origin (second-to-last start_line_point recorded). 
    start_line_point_2 is the most recent start_line_point.'''
    current_coords = gps_log[-1]
    
    # debugging:
    logging.debug(f'current_coords:                  {[current_coords.timestamp, current_coords.lattitude, current_coords.longitude]}')
    logging.debug(f'gps_log[-1] (same as cur coord) :{[gps_log[-1].timestamp, gps_log[-1].lattitude, gps_log[-1].longitude]}')
    logging.debug(f'gps_log[-2] (same as cur coord) :{[gps_log[-2].timestamp, gps_log[-2].lattitude, gps_log[-2].longitude]}')
    logging.debug(f'gps_log[-3] (same as cur coord) :{[gps_log[-3].timestamp, gps_log[-3].lattitude, gps_log[-3].longitude]}')
    
    origin = np.array([line_coords[-2].lattitude, line_coords[-2].longitude]) # degrees lat, lon
    current_location = (np.array([gps_log[-1].lattitude, gps_log[-1].longitude]) - origin) * degrees_to_meters_conversion 
    start_line_direction_vector = start_line_point_2 / np.linalg.norm(start_line_point_2) 
    closest_point_on_line = np.dot(start_line_direction_vector, current_location) * start_line_direction_vector 
    delta_to_closest_point = (current_location - closest_point_on_line) # format: np.array[dx, dy]
    distance_to_line_log.append(DistanceDatapoint(current_coords.timestamp, np.hypot(delta_to_closest_point[0], delta_to_closest_point[1])))
    if len(distance_to_line_log) > 1:
        for i in range(len(distance_to_line_log) - 1):
            velocity_queue.append(distance_to_line_log[i].distance - distance_to_line_log[i+1].distance / (distance_to_line_log[i+1].timestamp - distance_to_line_log[i].timestamp).seconds)
            logging.debug(f'distances to line are {distance_to_line_log[i].distance} and {distance_to_line_log[i+1].distance}')
            logging.debug(f'timestamps are {distance_to_line_log[i+1].timestamp} and {distance_to_line_log[i].timestamp}') 
     
    if len(velocity_queue) != 0:
        velocity_to_line = np.average(velocity_queue) # Computes moving average over length of deque. 
    else: # When the list is empty. 
        velocity_to_line = 0
    return (distance_to_line_log[-1].distance, velocity_to_line)

# Listen on port 2947 (gpsd) of localhost
session = gps.gps("localhost", "2947")
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

# Setup Raspbery Pi GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(25, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.add_event_detect(25, GPIO.RISING, callback = button_callback, bouncetime = 2000)

while True:
    try:
        report = session.next()
        # print(report)
        # Only appends to gps_log if report includes time (and time is different from previous entry), lat, and lon.
        #   This prevents duplicate entries for the same time, and entries where data is missing.  
        if report['class'] == 'TPV':
            if hasattr(report, 'time') and report.time != prev_time:
                timestamp = isoparse(report.time)
                logging.debug(f'report time: {report.time}')
                logging.debug(f'prev time:   {prev_time}')
                if hasattr(report, 'lat'):
                    lat = round(report.lat, 6)
                    if hasattr(report, 'lon'):
                        lon = round(report.lon, 6)
                        prev_time = report.time
                        gps_log.append(GPSDatapoint(timestamp, lat, lon))
                        logging.debug(f'Appended! {[gps_log[-1].timestamp, gps_log[-1].lattitude, gps_log[-1].longitude]}')

                        if len(gps_log) > 1:
                            # Before line is drawn, display GPS coords.
                            if len(line_coords) < 2:
                                display.lcd_display_string(f'lat: {gps_log[-1].lattitude}', 1)
                                display.lcd_display_string(f'lon: {gps_log[-1].longitude}', 2)
                                sleep(1)
                            # After line is drawn, displays distance and velocity relative to the line.
                            else:
                                distance_to_line, velocity_to_line = find_distance_and_velocity()
                                display.lcd_display_string(f'{int(distance_to_line)} m {int(distance_to_line % 1 * 100)} cm        ', 1)
                                display.lcd_display_string(f'{round(velocity_to_line, 3)} m/s        ', 2)
                                sleep(.5)

            else:
                continue
    except KeyError:
        pass