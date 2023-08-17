import psycopg2 # db connection
from psycopg2.extras import RealDictCursor, execute_values
import re

def get_top_vehicles(cursor, vehicle_class, metric, number_of_vehicles):
    sql = "SELECT manufacturer, name, class, laptime, topspeed, laptime_byclass, topspeed_byclass FROM vehicleinfo WHERE class LIKE %s"
    cursor.execute(sql, [vehicle_class])
    vehicles = cursor.fetchall()
    vehicles_to_use = []
    if metric == 'Lap Time':
        metric_str = 'laptime'
        other_metric_str = 'topspeed'
    elif metric == 'Top Speed':
        metric_str = 'topspeed'
        other_metric_str = 'laptime'
    for veh in vehicles:
        if vehicle_class in veh['class'] and veh[metric_str + '_byclass']: # make sure info we need exists on top of it being the right class
            pos_class_arr = veh[metric_str + '_byclass'].split(',') # pos in classes separated by comma in DB
            pos_class_str = None
            for cl in pos_class_arr:
                if vehicle_class in cl:
                    if vehicle_class == 'Sports' and 'Sports Classics' in cl: # potential for the captured class to be sports classics if we're looking for Sports
                        continue
                    else:
                        pos_class_str = cl
                        break
            if pos_class_str: # if it doesn't exist it's a Sports Classics car in a Sports search
                pos_in_class = pos_class_str.split()[0]
                pos_in_class = re.sub("[^0-9]", "", pos_in_class) # only take numbers from pos in class for sorting later
                vehicles_to_use.append([pos_in_class, veh['manufacturer'], veh['name'], veh[metric_str], veh[other_metric_str]])
                
    sorted_vehicles = sorted(vehicles_to_use, key=lambda veh: int(veh[0]))
    position_arr = [] # keeps track of positions in sorted_vehicles to detect dupes
    dupes_arr = [] # remove these after the loop
    for i in range(0, len(sorted_vehicles)): # clear out duplicate lap times/top speeds
        if sorted_vehicles[i][0] not in position_arr:
            position_arr.append(sorted_vehicles[i][0])
        else:
            dupes_arr.append(sorted_vehicles[i])
    sorted_vehicles = [v for v in sorted_vehicles if v not in dupes_arr]
    if len(sorted_vehicles) > number_of_vehicles:
        sorted_vehicles = sorted_vehicles[:number_of_vehicles]
    return sorted_vehicles