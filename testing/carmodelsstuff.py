def model_combine():
    disabled = ''' modelids = open("car_model_ids.txt", "r")
    both_read = open("ingame_car_names.txt", "r")
    final = open("final_car_list.txt", "w")

    bothlines = both_read.readlines()
    modelidlines = modelids.readlines()

    to_write = ""
    for i in range(0, len(bothlines)):
        combine = modelidlines[i].strip().lower() + "$" + bothlines[i].strip() + "\n"
        to_write += combine

    final.write(to_write)'''
    print('disabled. too much customization to lose.')

def detect_dupes():
    f = open("final_car_list.txt", "r")
    lines = f.readlines()
    name_list = []
    dupes = []
    for line in lines:
        line_arr = line.strip().split('$')
        if line_arr[1] in name_list:
            dupes.append(line)
        else:
            name_list.append(line_arr[1].strip())
    for dupe in dupes:
        print(dupe)

def copy_ingame_names():
    f = open("final_car_list.txt", "r")
    f2 = open("ingame_car_names.txt", "w")
    lines = f.readlines()
    write_str = ""
    for line in lines:
        line_arr = line.split('$')
        write_str += line_arr[1].strip() + "\n"
    f2.write(write_str)

def dedupe():
    f = open('nodupes_modelid_to_carnames.txt', 'r')
    lines = f.readlines()
    ids_arr = []
    for line in lines:
        line = line.split('$')
        if line[0] in ids_arr:
            print(line)
        else:
            ids_arr.append(line[0])

if __name__ == "__main__":
    inp = input("enter method:\n")
    if inp == 'modelscript':
        model_combine()
    elif inp == 'detectdupes':
        detect_dupes()
    elif inp == "copynames":
        copy_ingame_names()
    elif inp == 'dedupe':
        dedupe()
