def find_shift(array_1, array_2):
    shift = 0
    while shift < len(array_1):
        start_index = len(array_1) - shift
        modified_array_2 = array_2[start_index:] + array_2[:start_index]
        if array_1 == modified_array_2:
            return shift
        
        shift += 1

    return -1