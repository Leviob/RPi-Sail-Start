# RPi-Sail-Start
### Measures distance and velocity relative to a starting line for optimal sailboat racing starts using a Raspberry Pi and GPS. 

I created a proof of concept of a system that will allow easier, more consistent, and faster starting performance in sailboat races. The system uses GPS to draw an imaginary line between two points. An LCD screen then displays distance and velocity information relative to that line. 

In the context of sailboat racing, the starting line is typically represented by a buoy and an officiating boat as it's endpoints. An ideal racing start looks like the crossing the starting line at precisely the designated start time, without incurring a penalty for crossing it too early. It can be difficult to visualize how far your boat is from the starting line, especially near the midpoint of the line when you don't have a nearby reference of either endpoint. This makes knowledge of how close you are to the starting line and how quickly you are approaching it incredibly valuable information. 

My Sail Start system can be used to plot the endpoints of the starting line before the race begins. The provided information can then be used to inform speed or course adjustments such that the boat crosses the start line optimally. 


## Demo
The components of the system include a Raspberry Pi, GPS unit, LCD display, battery power supply, and breadboard components. A button is used to set endpoints. After two endpoints have been set, the display shows distance and velocity relative to the line created by the two endpoints.

### 1 - Drawing The Line
First, I'm initializing one endpoint, walking a bit, and initializing the second endpoint.

[![Video of drawing line](https://user-images.githubusercontent.com/59812528/108651946-b87c0d80-7477-11eb-985e-1fc88f77ebd9.png)](https://user-images.githubusercontent.com/59812528/108650400-58d03300-7474-11eb-895b-ff33ddaa6226.mp4 "Drawing Line Video")

### 2 - Walking Perpendicular To The Line
Once the line in plotted, walking perpendicular to the line will give my actual velocity (negative, because I'm walking away from the line) and distance.


### 3 - Walking Parallel To The Line
Walking Parallel to the line, my velocity and distance remain close to zero. 


The velocity is calculated relative to the line. Therefore, moving 30° relative to the line, the displayed velocity will be half of your actual velocity. 

Additional features I plan on adding include a timer to measure time until the race starts, and combining this with the velocity data to directly inform whether speed adjustments are necessary. 
