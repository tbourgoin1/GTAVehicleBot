modelids = open("car_model_ids.txt", "r")
both_read = open("ingame_car_names.txt", "r")
#final = open("final_car_list.txt", "w")

bothlines = both_read.readlines()
modelidlines = modelids.readlines()

to_write = ""
for i in range(0, len(bothlines)):
    combine = modelidlines[i].strip().lower() + "-" + bothlines[i].strip() + "\n"
    to_write += combine

#final.write(to_write)