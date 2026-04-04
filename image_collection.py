#!/usr/bin/env python3

import cv2
import depthai as dai
import os

device = dai.Device()
with dai.Pipeline(device) as pipeline:
    outputQueues = {}
    sockets = device.getConnectedCameras()
    
    for socket in sockets:
        cam = pipeline.create(dai.node.Camera).build(socket)
        outputQueues[str(socket)] = cam.requestFullResolutionOutput().createOutputQueue(maxSize=1, blocking=False)

    pipeline.start()
    num = 0
    
    print("Commands: 'c' to capture, 'q' to quit")

    while pipeline.isRunning():
        key = cv2.waitKey(1)
        
        for name, queue in outputQueues.items():
            if not os.path.exists(name):
                os.makedirs(name)
            videoIn = queue.get() 
            if isinstance(videoIn, dai.ImgFrame):
                img = videoIn.getCvFrame()
                cv2.imshow(name, img)
                if key == ord("c"):
                    filename = f"{name}/{name}_{num}.jpg"
                    cv2.imwrite(filename, img)

        if key == ord("c"):
            num += 1

        if key == ord("q"):
            break