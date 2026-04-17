#!/usr/bin/env python3
import depthai as dai
import time
from pynput import keyboard


def timeDeltaToMilliS(delta) -> float:
    return delta.total_seconds()*1000

x, y, z = 0.0, 0.0, 0.0
last_ts = None
print_flag = False

def on_press(key):
    global print_flag
    try:
        # Press 'p' to print current values
        if key.char == 'p':
            print_flag = True
        # Press 'r' to reset integration
        elif key.char == 'r':
            global x, y, z
            x, y, z = 0.0, 0.0, 0.0
            print("--- Integration Reset ---")
        # Press 'q' to quit
        elif key.char == 'q':
            return False
    except AttributeError:
        pass

listener = keyboard.Listener(on_press=on_press)
listener.start()    

# Create pipeline
with dai.Pipeline() as pipeline:
    # Define sources and outputs
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

    print("System Ready.")
    print("Commands: 'p' = Print, 'r' = Reset, 'q' = Quit")

    imuQueue = imu.out.createOutputQueue(maxSize=50, blocking=False)

    pipeline.start()
    baseTs = None
    while pipeline.isRunning():
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

            if print_flag:
                deg = 180 / 3.14159
                print("\n--- IMU Snapshot ---")
                print(f"Rotation [deg]: x: {x*deg:.2f} y: {y*deg:.2f} z: {z*deg:.2f}")
                print("--------------------")
                print_flag = False # Reset the flag so it only prints once per press

            
