#!/usr/bin/env python3
import depthai as dai
import cv2


with dai.Pipeline() as pipeline:
    cam = pipeline.create(dai.node.Camera).build()
    
    nn_input = cam.requestOutput(size=(640, 640), type=dai.ImgFrame.Type.BGR888p)

    archive = dai.NNArchive("best_robot_model2.rvc2.tar.xz")

    neuralNetwork = pipeline.create(dai.node.DetectionNetwork).build(nn_input, archive)
    
    nnDetectionQueue = neuralNetwork.out.createOutputQueue()
    nnPassthroughQueue = neuralNetwork.passthrough.createOutputQueue()

    real_width = 152.4
    dist = 609.6/2


    pipeline.start()
    print("Pipeline started! Press 'q' to quit.")

    while pipeline.isRunning():
        in_nn = nnDetectionQueue.get() 
        in_pass = nnPassthroughQueue.get()

        frame = in_pass.getCvFrame()


        for det in in_nn.detections:
            h, w = frame.shape[:2]
            x1, y1 = int(det.xmin * w), int(det.ymin * h)
            x2, y2 = int(det.xmax * w), int(det.ymax * h)

            if cv2.waitKey(1) == ord('c'):
                print("Height:", y2-y1)
                print("Width:",  x2-x1)
                pixel_width = x2 - x1
                focal_length = (dist * pixel_width) / real_width
                print("Focal length:", focal_length)
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"Goal: {det.confidence:.2%}", (x1, y1-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            

        cv2.imshow("Robot Vision", frame)
        if cv2.waitKey(1) == ord('q'):
            break