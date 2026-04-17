import serial
import time

try:
    ser = serial.Serial('COM22', 115200, timeout=1)
    
    ser.dtr = True
    ser.rts = True
    
    time.sleep(0.5) 
    print("Connected to Brain!")

    while True:
        if ser.in_waiting > 0:
            # Read the line and clean it up
            line = ser.read().decode()
            if line == "?":
                print("Signal received! Brain is ready.")
                break
 
    while True:
        user_val = input("Enter value to send (or 'q' to quit): ")
        
        if user_val.lower() == 'q':
            break
            
        message = f"{user_val}\r\n"
        ser.write(message.encode('utf-8'))
        ser.flush() 
        
        print(f"Sent: {message.strip()}")
        
except serial.SerialException as e:
    print(f"Serial Error: {e}")
except KeyboardInterrupt:
    print("Exiting...")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()