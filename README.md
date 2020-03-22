# arm-monitor
A monitor to manage your Motion captures directory and request human detection from arm-tiny-yolow (must be running somewhere). 

To start, you need to mount the pictures directory from Motion on /data and configure global variables in /conf/monitor.py :
```bash
docker run -d --name arm-monitor -v <conf_directory>:/conf/ -v <data_directory>:/data arm-monitor
```

Based on Raspbian Linux Stretch, Python 3.5, and OpenCV 3.4.4

#### Logic

 1. Monitor listens for new files in the Motion pictures/ directory
 2. When new files are added, it stores each new file name and waits until the detection is over + 15 seconds
 3. The last frame captured is an empty one as there is a 5 to 10 seconds with no motion detected configured in Motion
 4. This frame is used as the reference one to extract deltas with the others
 5. Each other frame is analyzed against the reference one and the extracted deltas greather than 100x200 (aka contours) are sent to the Tiny Yolo RNN which performs human detection
 6. Tiny Yolo returns the presence of a person with the associated probability 
 7. For each frame processed, Monitor only keeps the name and probability with the highest probability
 8. At the end of frame processing, if this probability is above 40%, then Monitor notifies Slack that a human has come in the lanscape

#### References
1. https://www.pyimagesearch.com/2017/09/04/raspbian-stretch-install-opencv-3-python-on-your-raspberry-pi/
2. https://github.com/besn0847/arm-tiny-yolo 
3. https://github.com/besn0847/arm-tfcv2/
