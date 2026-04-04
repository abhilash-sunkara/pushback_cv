#!/usr/bin/env python3
import depthai as dai
import cv2
import time
import math

def timeDeltaToMilliS(delta) -> float:
    return delta.total_seconds()*1000

x, y, z = 0.0, 0.0, 0.0
last_ts = None


with dai.Pipeline() as pipeline:

    imu = pipeline.create(dai.node.IMU)

    # enable ACCELEROMETER_RAW at 500 hz rate
    imu.enableIMUSensor(dai.IMUSensor.ACCELEROMETER_RAW, 480)
    # enable GYROSCOPE_RAW at 400 hz rate
    imu.enableIMUSensor(dai.IMUSensor.GYROSCOPE_RAW, 400)
    # it's recommended to set both setBatchReportThreshold and setMaxBatchReports to 20 when integrating in a pipeline with a lot of input/output connections
    # above this threshold packets will be sent in batch of X, if the host is not blocked and USB bandwidth is available
    imu.setBatchReportThreshold(20)
    # maximum number of IMU packets in a batch, if it's reached device will block sending until host can receive it
    # if lower or equal to batchReportThreshold then the sending is always blocking on device
    # useful to reduce device's CPU load  and number of lost packets, if CPU load is high on device side due to multiple nodes
    imu.setMaxBatchReports(20)

    imuQueue = imu.out.createOutputQueue(maxSize=50, blocking=False)
    cam = pipeline.create(dai.node.Camera).build()
    
    nn_input = cam.requestOutput(size=(640, 640), type=dai.ImgFrame.Type.BGR888p)

    archive = dai.NNArchive("best_robot_model2.rvc2.tar.xz")

    neuralNetwork = pipeline.create(dai.node.DetectionNetwork).build(nn_input, archive)
    
    nnDetectionQueue = neuralNetwork.out.createOutputQueue()
    nnPassthroughQueue = neuralNetwork.passthrough.createOutputQueue()

    real_width = 152.4
    focal_length = 770


    pipeline.start()
    print("Pipeline started! Press 'q' to quit.")

    baseTs = None

    while pipeline.isRunning():
        in_nn = nnDetectionQueue.get() 
        in_pass = nnPassthroughQueue.get()

        frame = in_pass.getCvFrame()
        key = cv2.waitKey(1)

        time.sleep(0.001)
        try:
            imuData = imuQueue.get()
        except KeyboardInterrupt:
            break
        assert isinstance(imuData, dai.IMUData)
        imuPackets = imuData.packets
        for imuPacket in imuPackets:
            acceleroValues = imuPacket.acceleroMeter
            gyroValues = imuPacket.gyroscope

            current_ts = gyroValues.getTimestamp().total_seconds()
            acceleroTs = acceleroValues.getTimestamp()
            gyroTs = gyroValues.getTimestamp()

            if last_ts is None:
                last_ts = current_ts
                continue
            
            dt = current_ts - last_ts
            last_ts = current_ts

            # Integrate
            x += gyroValues.x * dt
            y += gyroValues.y * dt
            z += gyroValues.z * dt

            imuF = "{:.06f}"
            tsF  = "{:.03f}"

        for det in in_nn.detections:
            h, w = frame.shape[:2]
            x1, y1 = int(det.xmin * w), int(det.ymin * h)
            x2, y2 = int(det.xmax * w), int(det.ymax * h)

            if key == ord('c'):
                print("Height:", y2-y1)
                print("Width:",  x2-x1)
                pixel_width = x2 - x1
                dist = (real_width * focal_length) / pixel_width
                print("Distance:", dist)
                print("y angle:", y)
                print("x:", dist * math.sin(y))
                print("y:", dist * math.cos(y))
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"Goal: {det.confidence:.2%}", (x1, y1-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            

        cv2.imshow("Robot Vision", frame)
        if key == ord('q'):
            break