import serial
import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
print("All available serial ports: ")
port_name = None

for port, desc, hwid in sorted(ports):
    print(f"{port}: {desc} [{hwid}]")

for port in sorted(ports):
    if "User Port" in port.description:
        print(f"Found Vex V5 User Port on port {port.device}")
        print("Connecting...")
        port_name = port.device
        break

ser = serial.Serial(port_name, 115200)
print("Connected")