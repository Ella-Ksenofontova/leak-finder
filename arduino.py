import serial
import time

def write_signals_in_file(com_port, path, file_name, duration=30000):
    signal = serial.Serial(f"com{com_port}", 9600)
    with open(f"{path}/{file_name}.txt", "w") as file:
        timestamp = time.time()

        while time.time() - timestamp < duration:
            sensor_signal = int(signal.readline())
            file.write(sensor_signal + "\n")
            time.sleep(0.1)