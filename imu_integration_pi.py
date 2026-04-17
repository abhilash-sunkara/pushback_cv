#!/usr/bin/env python3
import depthai as dai
import time
from curtsies import Input  # Added for SSH input

def timeDeltaToMilliS(delta) -> float:
    return delta.total_seconds()*1000

x, y, z = 0.0, 0.0, 0.0
last_ts = None

# Create pipeline
with dai.Pipeline() as pipeline:
    # Define sources and outputs
    imu = pipeline.create(dai.node.IMU)

    # enable ACCELEROMETER_RAW at 500 hz rate
    imu.enableIMUSensor(dai.IMUSensor.ACCELEROMETER_RAW, 480)
    # enable GYROSCOPE_RAW at 400 hz rate
    imu.enableIMUSensor(dai.IMUSensor.GYROSCOPE_RAW, 400)
    
    imu.setBatchReportThreshold(20)
    imu.setMaxBatchReports(20)

    imuQueue = imu.out.createOutputQueue(maxSize=50, blocking=False)

    pipeline.start()
    baseTs = None

    print("--- System Running ---")
    print("Press 'p' to print, 'r' to reset, 'q' to quit")

    # Wrapped your existing loop with curtsies Input
    with Input(keynames='curtsies') as input_generator:
        while pipeline.isRunning():
            # Check for input without blocking (1ms timeout)
            key = input_generator.send(0.001)

            if key == 'q':
                break
            elif key == 'r':
                x, y, z = 0.0, 0.0, 0.0
                print("\n--- Resetting Integration ---")

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
                
                if last_ts is None:
                    last_ts = current_ts
                    continue
                
                dt = current_ts - last_ts
                last_ts = current_ts

                # Integrate
                x += gyroValues.x * dt
                y += gyroValues.y * dt
                z += gyroValues.z * dt

                # ONLY PRINT when 'p' is pressed
                if key == 'p':
                    imuF = "{:.06f}"
                    print("\n--- IMU Snapshot ---")
                    print(f"Rotation [rad]: x: {imuF.format(x)} y: {imuF.format(y)} z: {imuF.format(z)}")
                    print(f"Rotation [deg]: x: {imuF.format(x * 180 / 3.1415)} y: {imuF.format(y * 180 / 3.1415)} z: {imuF.format(z * 180 / 3.1415)}")
                    print("--------------------\n")
                    key = None # Clear key to prevent repeated prints in the same packet batch