import serial

import serial.serialutil

def write_signals_in_file(com_port, path, file_name, distance, sound_speed):
    success = 1
    length = round(distance / sound_speed * 9600)
    try:
        signal = serial.Serial(f"com{com_port}", 9600)
        with open(f"{path}/{file_name}.txt", "w") as file:
            k = 0

            while k < length:
                sensor_signal = int(signal.readline())
                file.write(sensor_signal + "\n")
                k += 1
    except serial.serialutil.SerialException:
        success = 0
    finally:
        return success