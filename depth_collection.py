#!/usr/bin/env python3

import cv2
import depthai as dai
import numpy as np

pipeline = dai.Pipeline()
monoLeft = pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_B)
monoRight = pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_C)
stereo = pipeline.create(dai.node.StereoDepth)

# Linking
monoLeftOut = monoLeft.requestFullResolutionOutput()
monoRightOut = monoRight.requestFullResolutionOutput()
monoLeftOut.link(stereo.left)
monoRightOut.link(stereo.right)

# Aligns points on left and right so the same points have the same y coordinates
stereo.setRectification(True)
# Extends search range for matching pixels from left and right views
stereo.setExtendedDisparity(True)
# Verifies left and right camera feeds by calculating depth twice and removing pixels that are innacurate
stereo.setLeftRightCheck(True)

# Creates a queue of frames for camera to process
disparityQueue = stereo.disparity.createOutputQueue()

# Creates a heatmap from grayscale depth
colorMap = cv2.applyColorMap(np.arange(256, dtype=np.uint8), cv2.COLORMAP_JET)
colorMap[0] = [0, 0, 0]  # to make zero-disparity pixels black

with pipeline:
    pipeline.start()
    maxDisparity = 1
    while pipeline.isRunning():
        # Gets "oldest" frame from queue
        disparity = disparityQueue.get()
        assert isinstance(disparity, dai.ImgFrame)
        # Gets frame from disparity as an array
        npDisparity = disparity.getFrame()
        # Max value of disparity
        maxDisparity = max(maxDisparity, np.max(npDisparity))
        # Applies colormap while adjusting colors to scale to disparity
        colorizedDisparity = cv2.applyColorMap(((npDisparity / maxDisparity) * 255).astype(np.uint8), colorMap)
        cv2.imshow("disparity", colorizedDisparity)
        key = cv2.waitKey(1)
        if key == ord('q'):
            pipeline.stop()
            break
