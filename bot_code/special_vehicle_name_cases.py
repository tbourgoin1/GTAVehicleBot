from fastDamerauLevenshtein import damerauLevenshtein
import re

def main(formatted_vehicle_name, command_name):
    input_had_manufacturer = False
    # IF THE MAKE OF THE CAR IS IN THE QUERY, REMOVE IT TO FIND THE SHEET VALUE ACCURATELY
    car_names = open("txt_files/car_makes.txt", "r")
    for line in car_names:
        line = re.sub("\W","", str(line)).lower()
        if line in formatted_vehicle_name:
            if formatted_vehicle_name != "emperor": # special case bc emperor is car and manufacturer
                formatted_vehicle_name = formatted_vehicle_name.replace(line, "")
                input_had_manufacturer = True
    
    # F1 CARS - makes sure to return mid df without any specification
    f1_cars = ["r88", "pr4", "br8", "dr1"]
    if(any(f1_car in formatted_vehicle_name for f1_car in f1_cars) and command_name == 'vehicleinfo'):
        standalone_f1_car_name = "" # one from the f1_cars list for formatting
        for car in f1_cars: # change formatted name to the exact f1 match, add DF if not key vehicle info sheet (that sheet uses exact names no dfs)
            if(car in formatted_vehicle_name):
                standalone_f1_car_name = car
                break
        if("min" in formatted_vehicle_name):
            formatted_vehicle_name = standalone_f1_car_name + "mindf"
        elif("max" in formatted_vehicle_name):
            formatted_vehicle_name = standalone_f1_car_name + "maxdf"
        else: # if mid is in the name or no downforce specified, provide mid
            formatted_vehicle_name = standalone_f1_car_name + "middf"

    # MISSPELLINGS ON THESE SO BEST GUESS MATCH APPEARS
        # "merryweather mesa" = "mesa (merryweather)"
    if(formatted_vehicle_name == "merryweathermesa"):
       formatted_vehicle_name = "mesamerryweather"
    
    # "merryweather mesa" = "mesa (merryweather)"
    if(formatted_vehicle_name == "armoredkuruma" or formatted_vehicle_name == "armoredkaruma"):
       formatted_vehicle_name = "kurumaarmored"
    
    if(formatted_vehicle_name == "lazer" or formatted_vehicle_name == "laser"):
        formatted_vehicle_name = "p996lazer"
    
    # mk2 cases
    if(formatted_vehicle_name == "mk2"):
        formatted_vehicle_name = "oppressormkii"
    elif(formatted_vehicle_name.endswith("mk2")): # oppressor mk2, retinue mk2 etc common phrases but sheets say "mk ii", so convert to that format
        formatted_vehicle_name = formatted_vehicle_name[:-3] + "mkii"
    
    # youga 4x4 is a common phrase, find youga classic 4x4 instead
    if(formatted_vehicle_name == "youga4x4"):
        formatted_vehicle_name = "yougaclassic4x4"
    
    # fib buffalo means "fib" on sheets
    if(formatted_vehicle_name == "fibbuffalo"):
        formatted_vehicle_name = "fib"

    # arena vehicles
    arena_vehicles = ["dominator", "impaler", "issi", "issi classic", "slamvan", "bruiser", "brutus", "cerberus", "deathbike", "imperator", "sasquatch", "scarab", "zr380"] # all arena war cars
    arena_keywords = ["arena", "future", "future shock", "apocalypse", "nightmare"] # all arena war car types/phrases people use to look up arena war vehicles
    for keyword in arena_keywords: # find and remove the arena keyword the user used if applicable
        if keyword in formatted_vehicle_name:
            formatted_vehicle_name = formatted_vehicle_name.replace(keyword, "") # remove the keyword for more accurate damerauLevenshtein
            max_ratio = 0 # to decide which car they want from arena list
            final_car = "" # car name we choose in the end
            for car in arena_vehicles: # run the algorithm on it, highest similarity is the car they chose
                ratio = damerauLevenshtein(formatted_vehicle_name.lower(), car.lower())
                if ratio > max_ratio:
                    final_car = car
                    max_ratio = ratio
            cars_with_arena_in_name = ["dominator", "impaler", "issi", "slamvan"]
            if(final_car in cars_with_arena_in_name):
                formatted_vehicle_name = final_car + "arena" # append arena to the end of the car name so we find the entry in sheets
            else:
                formatted_vehicle_name = final_car
            break
    return formatted_vehicle_name, input_had_manufacturer

if __name__ == '__main__':
    main()