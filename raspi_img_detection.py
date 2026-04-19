#!/usr/bin/env python3
import depthai as dai
import cv2
import time
import math
import serial

# --- 1. Initialize Serial Connection ---
try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    ser.dtr = True
    ser.rts = True
    
    time.sleep(0.5) 
    print("Connected to serial port! Waiting for Brain...")

    while True:
        if ser.in_waiting > 0:
            line = ser.read().decode(errors='ignore').strip()
            if "?" in line:
                print("Signal received! Brain is ready.")
                break

except serial.SerialException as e:
    print(f"Serial Error: {e}")
    exit()


def timeDeltaToMilliS(delta) -> float:
    return delta.total_seconds() * 1000

angle_x, angle_y, angle_z = 0.0, 0.0, 0.0 
last_ts = None

with dai.Pipeline() as pipeline:

    imu = pipeline.create(dai.node.IMU)
    imu.enableIMUSensor(dai.IMUSensor.ACCELEROMETER_RAW, 480)
    imu.enableIMUSensor(dai.IMUSensor.GYROSCOPE_RAW, 400)
    imu.setBatchReportThreshold(20)
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

    last_send_time = 0.0

    try:
        while pipeline.isRunning():
            in_nn = nnDetectionQueue.get() 
            in_pass = nnPassthroughQueue.get()

            frame = in_pass.getCvFrame()
            key = cv2.waitKey(1)

            if key == ord('q'):
                break

            imuData = imuQueue.get()
            assert isinstance(imuData, dai.IMUData)
            imuPackets = imuData.packets
            
            for imuPacket in imuPackets:
                gyroValues = imuPacket.gyroscope
                current_ts = gyroValues.getTimestamp().total_seconds()

                if last_ts is None:
                    last_ts = current_ts
                    continue
                
                dt = current_ts - last_ts
                last_ts = current_ts

                angle_x += gyroValues.x * dt
                angle_y += gyroValues.y * dt
                angle_z += gyroValues.z * dt

            for det in in_nn.detections:
                h, w = frame.shape[:2]
                x1, y1 = int(det.xmin * w), int(det.ymin * h)
                x2, y2 = int(det.xmax * w), int(det.ymax * h)

                pixel_width = x2 - x1
                
                if pixel_width > 0:
                    dist = (real_width * focal_length) / pixel_width
                    
                    target_x = dist * math.sin(angle_y)
                    target_y = dist * math.cos(angle_y)
                    
                    current_time = time.time()
                    if current_time - last_send_time > 0.1:
                        
                        message = f"X:{target_x:.1f}Y:{target_y:.1f}\r\n"
                        ser.write(message.encode('utf-8'))
                        ser.flush()
                        
                        last_send_time = current_time
                        
                        cv2.putText(frame, f"Sent: {message.strip()}", (x1, y1-25), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 100, 0), 2)
                    
                    if key == ord('c'):
                        print(f"Dist: {dist:.2f} | angle_y: {angle_y:.2f} | X: {target_x:.2f} | Y: {target_y:.2f}")

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"Goal: {det.confidence:.2%}", (x1, y1-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            cv2.imshow("Robot Vision", frame)

    except KeyboardInterrupt:
        print("Keyboard interrupt received. Exiting...")
    
    finally:
        if 'ser' in locals() and ser.is_open:
            print("Closing serial port...")
            ser.close()