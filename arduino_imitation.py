from random import randint

def make_arrays(distance, sound_speed, shift=500):
    array1 = []
    array2 = []
    h = round(distance / sound_speed * 9600)

    for i in range(round(h * 3.5)):
        array1.append(0)
        array2.append(0)

    for i in range(round(h * 3.5)):
        j = i
        while j >= h:
            j = j - h
            array1[i] = array1[j]
        else:
            array1[i] = randint(1, 1024)

    for i in range(round(h * 3.5)):
        j = i + shift
        if j >= len(array2):
            j = j - len(array2)

        array2[i] = array1[j]
    
    return (array1, array2)

def write_signals_in_file(distance, sound_speed, first_dir_path, second_dir_path, first_file_name, second_file_name):
    array_1, array_2 = make_arrays(distance, sound_speed)

    with open(first_dir_path + "/" + first_file_name, "w") as first_file:
        for i in array_1:
            first_file.write(str(i // 100) + "\n")

    with open(second_dir_path + "/" + second_file_name, "w") as second_file:
        for i in array_2:
            second_file.write(str(i // 100) + "\n")

    return 1

