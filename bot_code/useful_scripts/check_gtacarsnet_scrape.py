# useful for checking if the gtacars.net scrape still works properly if any changes were made to the site

import sys
sys.path.insert(0, r'C:\Users\Trent\Desktop\gtabot git\GTAVehicleBot\bot_code')
import updatevehicledata_helper

new_vehicleinfo = updatevehicledata_helper.get_new_vehicle_data('https://gtacars.net/gta5/feltzer3', 'feltzer3')
for field in new_vehicleinfo:
    print(new_vehicleinfo[field])