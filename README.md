# RPi-Sail-Start
### Measures distance and velocity relative to a starting line for optimal sailboat racing starts using a Raspberry Pi and GPS. 

I created a proof of concept of a system that will allow easier, more consistent, and faster starting performance in sailboat races. The system uses GPS to draw an imaginary line between two points. An LCD screen then displays distance and velocity information relative to that line. 

In the context of sailboat racing, the starting line is typically represented by a buoy and an officiating boat as it's endpoints. An ideal racing start is crossing the starting line at precisely the designated start time, without incurring a penalty for crossing it too early. It can be difficult to visualize how far the boat is from the starting line, especially near the midpoint of the line when there is not a nearby reference of either endpoint. Especially in these scenarios, knowledge of how close the boat is to the starting line and how quickly it is approaching the starting line is incredibly valuable information. 

My Sail Start system can be used to plot the endpoints of the starting line before the race begins. The provided information can then be used to inform speed or course adjustments such that the boat crosses the start line optimally. 


## Demo - Click Pictures To Play Videos
The components of the system include a Raspberry Pi, GPS unit, LCD display, battery power supply, and breadboard components. A button is used to set endpoints. After two endpoints have been set, the display shows distance and velocity relative to the line created by the two endpoints.

### 1 - Drawing The Line
First, I'm initializing one endpoint, walking a bit, and initializing the second endpoint.

[![Video of drawing line](https://user-images.githubusercontent.com/59812528/108651946-b87c0d80-7477-11eb-985e-1fc88f77ebd9.png)](https://user-images.githubusercontent.com/59812528/108650400-58d03300-7474-11eb-895b-ff33ddaa6226.mp4 "Drawing Line Video")


### 2 - Walking Perpendicular To The Line
Once the line in plotted, walking perpendicular to the line will give my actual velocity (negative, because I'm walking away from the line) and distance.

[![Video of walking away](https://user-images.githubusercontent.com/59812528/108652216-72737980-7478-11eb-8138-c21c4104a9e6.png)](https://user-images.githubusercontent.com/59812528/108652202-6ab3d500-7478-11eb-91da-7c31f6e96e4c.mp4 "Walking Away Video")


### 3 - Walking Parallel To The Line
Walking Parallel to the line, my velocity and distance remain close to zero. 

[![Video of walking parallel](https://user-images.githubusercontent.com/59812528/108652132-40faae00-7478-11eb-89f1-bcdaa31b38d1.png)](https://user-images.githubusercontent.com/59812528/108651765-591dfd80-7477-11eb-8a70-ac3d395446c2.mp4 "Walking Parallel Video")

The velocity is calculated relative to the line. Therefore, moving 30° relative to the line, the displayed velocity will be half of the actual velocity. 

## Potential Improvements

Right now, the GPS coordinates update much too slow to be useful in an actual race. Perhaps a higher quality GPS or antenna will mitigate this. I also have an idea to use accelerometers to measure short distances while awaiting GPS feedback. I plan on adding a timer to measure time until the race starts, and combining this with the velocity data to directly inform whether speed adjustments are necessary. 
