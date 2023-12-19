import psycopg2 # db connection
from psycopg2.extras import RealDictCursor, execute_values
import re

def validate_input(input_dict, cursor):
    bad_fields = []
    vehicle = None # only set on Update
    if input_dict['insert_or_update'] == 'Update': 
        sql = "SELECT * FROM vehicleinfo WHERE modelid = %s LIMIT 1"
        cursor.execute(sql, [input_dict['modelid']])
        vehicle = cursor.fetchone()
        if not vehicle:
            bad_fields.append('Model ID: Database does not contain this model id')
    
    if input_dict['laptime']:
        if not re.match("[0-9][:][0-9][0-9][.][0-9][0-9][0-9]$", input_dict['laptime']):
            bad_fields.append('Lap Time: Not formatted correctly. Must look like: 0:59.233')
        # if raceable, it must have a ltbc if it has a lap time
        if not input_dict['laptime_byclass'] and not vehicle['laptime_byclass']:
            if vehicle['class']:
                if "(Not Raceable)" not in vehicle['class']:
                    bad_fields.append('Lap Time: Must have a Lap Time Position In Class filled in to add a Lap Time')
            elif input_dict['race_class']:
                if "(Not Raceable)" not in input_dict['race_class']:
                    bad_fields.append('Lap Time: Must have a Lap Time Position In Class filled in to add a Lap Time')
    
    if input_dict['topspeed']:
        topspeed = input_dict['topspeed'].replace('mph', '')
        if not topspeed.replace('.', '').isnumeric():
            bad_fields.append('Top Speed: Incorrect format, must only be a number. You may optionally include "." or "mph"')
        else:
            input_dict['topspeed'] = topspeed
        # if raceable, it must have a tsbc if it has a top speed
        if not input_dict['topspeed_byclass'] and not vehicle['topspeed_byclass']:
            if vehicle['class']:
                if "(Not Raceable)" not in vehicle['class']:
                    bad_fields.append('Top Speed: Must have a Top Speed Position In Class filled in to add a Top Speed')
            elif input_dict['race_class']:
                if "(Not Raceable)" not in input_dict['race_class']:
                    bad_fields.append(bad_fields.append('Top Speed: Must have a Top Speed Position In Class filled in to add a Top Speed'))
    
    if input_dict['image'] and 'https://' not in input_dict['image']:
        bad_fields.append('Image: Not a valid URL')
    
    if input_dict['flags']:
        if input_dict['flags'] == 'None':
            input_dict['flags'] = ':white_check_mark: None'
        else:
            input_dict['flags'] = ':warning: ' + input_dict['flags']
    
    if input_dict['customization_video'] and 'https://youtu.be/' not in input_dict['customization_video']:
        bad_fields.append('Customization Video: Not a valid YouTube URL. Must be formatted like https://youtu.be/joaePmbBqvk')
    
    if input_dict['laptime_byclass']:
        if ' out of ' not in input_dict['laptime_byclass'] or ' in ' not in input_dict['laptime_byclass']:
            bad_fields.append('Lap Time By Class: Incorrect format. Must be like: 18th out of 42 in Sports Classics')
        if not input_dict['laptime'] and not vehicle['laptime']:
            bad_fields.append('Lap Time By Class: Must have a Lap Time filled in to add a Lap Time By Class')
        if not input_dict['race_class'] and not vehicle['class']:
            bad_fields.append('Lap Time By Class: Must have a Class filled in to add a Lap Time By Class')
        if input_dict['insert_or_update'] == 'Insert':
             bad_fields.append('Cannot add lap time by class data on insert, only update')
    
    if input_dict['topspeed_byclass']:
        if ' out of ' not in input_dict['topspeed_byclass'] or ' in ' not in input_dict['topspeed_byclass']:
            bad_fields.append('Top Speed By Class: Incorrect format. Must be like: 18th out of 42 in Sports Classics')
        if not input_dict['topspeed'] and not vehicle['topspeed']:
            bad_fields.append('Top Speed By Class: Must have a Top Speed filled in to add a Top Speed By Class')
        if not input_dict['race_class'] and not vehicle['class']:
            bad_fields.append('Top Speed By Class: Must have a Class filled in to add a Top Speed By Class')
        if input_dict['insert_or_update'] == 'Insert':
             bad_fields.append('Cannot add top speed by class data on insert, only update')

    if input_dict['numseats'] and not input_dict['numseats'].isnumeric():
        bad_fields.append('Num Seats: You most only enter a number')
    
    if input_dict['price'] and not input_dict['price'].isnumeric():
        bad_fields.append('Price: You most only enter a number')

    if input_dict['dlc'] and ('(' not in input_dict['dlc'] or ')' not in input_dict['dlc']):
        bad_fields.append('DLC: Must have the year of the DLC surrounded by parenthesis')
    
    return bad_fields, vehicle, input_dict

def find_input_veh_pos_in_class(class_arr, ltbc, tsbc): # return all classes the input vehicle belongs to w/ its position respectively
    input_veh_positions = {}
    ltbc_arr = []
    tsbc_arr = []
    if ltbc:
        ltbc_arr = ltbc.split(",")
    if tsbc:
        tsbc_arr = tsbc.split(",")
    for c in class_arr:
        for string in ltbc_arr:
            if c in string and not ('Sports Classics' in string and c == 'Sports'):
                key_str = c + "_lt"
                input_veh_positions[key_str] = re.sub("[^0-9]", "", string.split(' out of ',1)[0]) # input [class, input vehicle place in class] tuple
                break
                # total_vehicles_in_class = re.sub("[^0-9]", "", lt.split('out of',1)[1].split('in',1)[0]) DON'T RELY ON INPUT, TAKE FROM DB VAL INSTEAD
        for string in tsbc_arr:
            if c in string and not ('Sports Classics' in string and c == 'Sports'):
                key_str = c + "_ts"
                input_veh_positions[key_str] = re.sub("[^0-9]", "", string.split(' out of ',1)[0]) # input [class, input vehicle place in class] tuple
                break
                # total_vehicles_in_class = re.sub("[^0-9]", "", lt.split('out of',1)[1].split('in',1)[0]) DON'T RELY ON INPUT, TAKE FROM DB VAL INSTEAD
    return input_veh_positions

def make_ordinal(num): # attach an ordinal ("st" "nd", "rd", "th") to the end of a number
    was_special = False # 11th, 12th, or 13th being the last 2 digits
    num_str = str(num)
    res = ""
    if len(num_str) >= 2: # if ends in 11, 12, 13, override to 'th'
        if num_str[-2:] == "11" or num_str[-2:] == "12" or num_str[-2:] == "13":
            res = num_str + "th"
            was_special = True
    if not was_special:
        last_digit = num % 10
        if last_digit == 1:
            res = str(num) + "st"
        elif last_digit == 2:
            res = str(num) + "nd"
        elif last_digit == 3:
            res = str(num) + "rd"
        else:
            res = str(num) + "th"
    return res

def find_cur_veh_pos_update(input_vehicle_exists, db_bc, cur_class, input_pos, cur_pos):
    if input_vehicle_exists:
        for bc_str in db_bc.split(","):
            if cur_class in bc_str and not ('Sports Classics' in bc_str and cur_class == 'Sports'):
                # input vehicle's current database position in class
                db_bc_pos = int(re.sub("[^0-9]", "", bc_str.split('out of',1)[0]))
                # if this is equal it's an edge case that shouldn't happen - don't change anything
                if db_bc_pos < input_pos: # input vehicle moved down the order
                    if db_bc_pos < cur_pos <= input_pos: # if cur pos is between the db and input pos, decrease
                        cur_pos -= 1
                        break
                elif db_bc_pos > input_pos: # moved up the order
                    if input_pos <= cur_pos < db_bc_pos:
                        cur_pos += 1
                        break
    else: # input vehicle doesn't exist in db
        if cur_pos >= input_pos: # increase by 1 if the current vehicle's position is more than input's
            cur_pos += 1
    return cur_pos

def update_pos_in_class_str(v, input_veh_positions, new_class_totals, lt_ts_index, db_ltbc, db_tsbc, input_vehicle_exists_lt, input_vehicle_exists_ts): # returns new position in class string for existing vehicle. pic = position in class
    #print("new v: " + str(v))
    curveh_pic_arr = v[lt_ts_index] # -> 1 for ltbc, 2 for tsbc
    final_pic_str = "" # new ltbc we will construct
    class_suffix = "_lt"
    if lt_ts_index == 2:
        class_suffix = "_ts"
    for i in range(0, len(curveh_pic_arr)): # array of each position in class for the current vehicle
        cur_pic_str = curveh_pic_arr[i].strip()
        if cur_pic_str == '': # not raceable vehicle, don't modify
            break
        #print("new cur_pic_str: " + str(cur_pic_str))
        cur_class = cur_pic_str.split(' in ',1)[1] # find class
        #print("cur_class: " + str(cur_class))
        cur_pos = None # need later to decide whether to tell if we modified the ltbc string
        if (cur_class + class_suffix) in input_veh_positions.keys(): # cur veh's current class matches one of the input's classes, modify
            input_pos = int(input_veh_positions[cur_class + class_suffix])
            #print("input_pos: " + str(input_pos))
            cur_pos = int(re.sub("[^0-9]", "", cur_pic_str.split('out of',1)[0]))
            #print("cur pos: " + str(cur_pos))
            
            # move existing vehicles' positions depending on several factors
                # if input vehicle already exists, only move vehicles between its new and old positions
                # otherwise, increase all vehicles' positions below the input's by 1
            if class_suffix == "_lt":
                cur_pos = find_cur_veh_pos_update(input_vehicle_exists_lt, db_ltbc, cur_class, input_pos, cur_pos)
            else:
                cur_pos = find_cur_veh_pos_update(input_vehicle_exists_ts, db_tsbc, cur_class, input_pos, cur_pos)
                              
            
            # increase total in class by 1 depending on if the input vehicle already had a ltbc/tsbc or not
            cur_total_in_class = (int(re.sub("[^0-9]", "", cur_pic_str.split('out of',1)[1].split('in',1)[0]))) + 1
            # lap time by class, use ltbc to see if it already exists. if not, increase total
            # if the input vehicle is already in the DB, also don't increase the total
            if class_suffix == "_lt":
                ltbc_arr = db_ltbc.split(",")
                for ltbc_str in ltbc_arr:
                    if (cur_class in ltbc_str and not ('Sports Classics' in ltbc_str and cur_class == 'Sports')) or input_vehicle_exists_lt:
                        cur_total_in_class -= 1
                        break

            elif class_suffix == "_ts":
                tsbc_arr = db_tsbc.split(",")
                for tsbc_str in tsbc_arr:
                    if cur_class in tsbc_str and not ('Sports Classics' in tsbc_str and cur_class == 'Sports') or input_vehicle_exists_ts:
                        cur_total_in_class -= 1
                        break
            
            
            #print("cur_total_in_class: " + str(cur_total_in_class))
            if (cur_class + class_suffix) not in new_class_totals.keys(): # save new total in class if it's not there
                new_class_totals[cur_class + class_suffix] = cur_total_in_class
                # print("new_class_totals: " + str(new_class_totals))
            cur_pos = make_ordinal(cur_pos) # add 'st', 'nd', 'rd' etc to the cur veh's position in class
            if i == len(curveh_pic_arr) - 1: # last in loop = no comma or space afterwards
                final_pic_str += cur_pos + " out of " + str(cur_total_in_class) + " in " + cur_class
            else:
                final_pic_str += cur_pos + " out of " + str(cur_total_in_class) + " in " + cur_class + ", "
        if not cur_pos: # didn't modify string bc class wasn't matching with input - retain original string
            if i == len(curveh_pic_arr) - 1: # last in loop = no comma or space afterwards
                final_pic_str += cur_pic_str
            else:
                final_pic_str += cur_pic_str + ", "
    #print(final_pic_str)
    return final_pic_str

def handle_new_position_in_class(modelid, race_classes, ltbc, tsbc, cursor, db_ltbc, db_tsbc):
        class_arr = [] # classes the input vehicle is in
        for c in race_classes.split(","):
            class_arr.append(c.strip())
        input_veh_positions = find_input_veh_pos_in_class(class_arr, ltbc, tsbc) # dict of {class, pos in class} tuples for all input vehicle classes

        print("input_veh_positions" + str(input_veh_positions.keys()))
        formatted_class_arr = [] # adding % for query to get all cars in inpout veh class(es) including ones with multiple
        for c in class_arr:
            c = "%" + c + "%"
            formatted_class_arr.append(c)
        sql = "SELECT modelid, laptime_byclass, topspeed_byclass FROM vehicleinfo WHERE class ~~* any(array{classes})".format(classes=list(formatted_class_arr)) # all vehicles in all classes belonging to the input
        cursor.execute(sql)
        queried_vehicles = cursor.fetchall()
        vehicles = [] # every vehicle that shares a class with the input -> [modelid, ltbc, tsbc]
        # add retrieved vehs into an array with their modelid, ltbc and tsbc as comma separated arrays in case of multiple classes
        input_vehicle_exists_lt = False
        input_vehicle_exists_ts = False
        for v in queried_vehicles:
            if v['modelid'] == modelid: # do not append to array of vehicles to update if it has a ltbc/tsbc already
                if v['laptime_byclass']:
                    input_vehicle_exists_lt = True
                if v['topspeed_byclass']:
                    input_vehicle_exists_ts = True
            else:
                if v['laptime_byclass'] == None:
                    v['laptime_byclass'] = ''
                if v['topspeed_byclass'] == None:
                    v['topspeed_byclass'] = ''
                vehicles.append([v['modelid'], v['laptime_byclass'].split(","), v['topspeed_byclass'].split(",")])
        update_arr = [] # array of existing vehicles that need to be updated
        new_class_totals = {} # (class, total # in class) dict - used to update input vehicle totals in class
        
        if ltbc:
            print('ltbc')
            for v in vehicles:
                if v[0] != modelid:
                    final_ltbc_str = update_pos_in_class_str(v, input_veh_positions, new_class_totals, 1, db_ltbc, db_tsbc, input_vehicle_exists_lt, input_vehicle_exists_ts)
                    #print("new ltbc string: " + final_pic_str)
                    tsbc_str = "" 
                    if not tsbc: # no tsbc means no updates to existing vehicles' tsbc, reinstate original tsbc in update_arr. if it exists, blank and handled later
                        for i in range(0, len(v[2])):
                            if i == len(v[2]) - 1:
                                tsbc_str += v[2][i].strip()
                            else:
                                tsbc_str += v[2][i].strip() + ", "
                    update_arr.append([v[0], final_ltbc_str, tsbc_str]) # [modelid, ltbc, tsbc]
            #print("update arr: " + str(update_arr))

        if tsbc:
            print('tsbc')
            for v in vehicles:
                if v[0] != modelid:
                    final_tsbc_str = update_pos_in_class_str(v, input_veh_positions, new_class_totals, 2, db_ltbc, db_tsbc, input_vehicle_exists_lt, input_vehicle_exists_ts)
                    ltbc_str = ""
                    if not ltbc: # create the array with [modelid, ORIGINAL LTBC, new tsbc]
                        for i in range(0, len(v[1])):
                            if i == len(v[1]) - 1:
                                ltbc_str += v[1][i].strip()
                            else:
                                ltbc_str += v[1][i].strip() + ", "
                        update_arr.append([v[0], ltbc_str, final_tsbc_str]) # [modelid, ltbc, tsbc]
                    else: # if ltbc, replace the string to the array where this modelid is, at position [2] to replace its tsbc blank string
                        for i in range(0, len(update_arr)):
                            if update_arr[i][0] == v[0]:
                                update_arr[i][2] = final_tsbc_str
                                break
        print("class totals: " + str(new_class_totals))

        # replace the total vehicle count to what we updated to for the input vehicle's classes - just in case the input total was wrong
        ltbc_arr = []
        tsbc_arr = []
        new_input_ltbc = ""
        new_input_tsbc = ""
        if ltbc:
            ltbc_arr = ltbc.split(",")
        if tsbc:
            tsbc_arr = tsbc.split(",")
        
        for c in class_arr:
            for string in ltbc_arr:
                if c in string and not ('Sports Classics' in string and c == 'Sports'):
                    pos = string.split(' out of ')[0].strip()
                    if not new_class_totals: # no members with ltbc/tsbc in the class - input is first entry
                        new_input_ltbc += '1st out of 1 in ' + c + ", " # input [class, input vehicle place in class] tuple
                    else:
                        new_input_ltbc += pos + ' out of ' + str(new_class_totals[c + "_lt"]) + ' in ' + c + ", " # input [class, input vehicle place in class] tuple
                    break
            for string in tsbc_arr:
                if c in string and not ('Sports Classics' in string and c == 'Sports'):
                    pos = string.split(' out of ')[0].strip()
                    if not new_class_totals: # no members with ltbc/tsbc in the class - input is first entry
                        new_input_tsbc += '1st out of 1 in ' + c + ", " # input [class, input vehicle place in class] tuple
                    else:
                        new_input_tsbc += pos + ' out of ' + str(new_class_totals[c + "_ts"]) + ' in ' + c + ", " # input [class, input vehicle place in class] tuple
                    break
        new_input_ltbc = new_input_ltbc.rstrip(", ")
        new_input_tsbc = new_input_tsbc.rstrip(", ")
        for a in update_arr:
            print(a)
        print(str([modelid, new_input_ltbc, new_input_tsbc]))
        return update_arr, [modelid, new_input_ltbc, new_input_tsbc]