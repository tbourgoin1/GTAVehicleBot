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
    
    if input_dict['topspeed']:
        topspeed = input_dict['topspeed'].replace('mph', '')
        if not topspeed.replace('.', '').isnumeric():
            bad_fields.append('Top Speed: Incorrect format, must only be a number. You may optionally include "." or "mph"')
        else:
            input_dict['topspeed'] = topspeed
    
    if input_dict['image'] and 'https://' not in input_dict['image']:
        bad_fields.append('Image: Not a valid URL')
    
    if input_dict['flags']:
        if input_dict['flags'] == 'None':
            input_dict['flags'] = ':white_check_mark: None'
        else:
            input_dict['flags'] = ':warning: ' + input_dict['flags']
    
    if input_dict['customization_video'] and 'https://youtu.be/' not in input_dict['customization_video']:
        bad_fields.append('Customization Video: Not a valid YouTube URL. Must be formatted like https://youtu.be/joaePmbBqvk')
    
    if input_dict['laptime_byclass'] and (' out of ' not in input_dict['laptime_byclass'] or ' in ' not in input_dict['laptime_byclass']):
        bad_fields.append('Lap Time By Class: Incorrect format. Must be like: 18th out of 42 in Sports Classics')
    
    if input_dict['topspeed_byclass'] and (' out of ' not in input_dict['topspeed_byclass'] or ' in ' not in input_dict['topspeed_byclass']):
        bad_fields.append('Top Speed By Class: Incorrect format. Must be like: 18th out of 42 in Sports Classics')

    if input_dict['numseats'] and not input_dict['numseats'].isnumeric():
        bad_fields.append('Num Seats: You most only enter a number')
    
    if input_dict['price'] and not input_dict['price'].isnumeric():
        bad_fields.append('Price: You most only enter a number')

    if input_dict['dlc'] and ('(' not in input_dict['dlc'] or ')' not in input_dict['dlc']):
        bad_fields.append('DLC: Must have the year of the DLC surrounded by parenthesis')
    
    return bad_fields, vehicle, input_dict