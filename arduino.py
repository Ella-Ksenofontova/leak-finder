import serial
import time

import serial.serialutil

def write_signals_in_file(com_port, path, file_name, duration=30000):
    success = 1
    try:
        signal = serial.Serial(f"com{com_port}", 9600)
        with open(f"{path}/{file_name}.txt", "w") as file:
            timestamp = time.time()

            while time.time() - timestamp < duration:
                sensor_signal = int(signal.readline())
                file.write(sensor_signal + "\n")
                time.sleep(0.1)
    except serial.serialutil.SerialException:
        success = 0
    finally:
        return success