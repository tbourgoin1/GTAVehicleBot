from email.mime import image
from logging import error
import os
from time import time
from typing import Iterable
from nextcord import Interaction, SlashOption
import nextcord
from nextcord.ext.commands.core import check
from dotenv import load_dotenv
from nextcord.ext import commands
import sheetparser_searchstaffvehicles
import json
import re # regex
import sys # try except error capture
import logging
import logging.handlers
import psycopg2 # db connection
from psycopg2.extras import RealDictCursor, execute_values
from urllib.parse import urlparse
import vehicleinfo_helper
import updatevehicledata_helper
import upsertvehicle_helper
import topvehicles_helper
from keep_db_alive import KeepDBAlive


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
DEV_TOKEN = os.getenv("DEV_DISCORD_TOKEN")
DB_URL = os.getenv("DATABASE_URL")

testserverid = [851239396689707078] # testing only
productionserverids = [715583253289107588, 696800707919085638]

bot = commands.Bot(command_prefix=',', case_insensitive=True)
bot.remove_command('help') # get rid of default help command and use mine instead

# create email logger for errors
smtp_handler = logging.handlers.SMTPHandler(mailhost=("smtp.gmail.com", 587),
                                            fromaddr="GTAVehicleBot@gmail.com", 
                                            toaddrs="mrthankuvrymuch@gmail.com",
                                            subject=u"GTAVehicleBot error!",
                                            credentials=('GTAVehicleBot@gmail.com', 'sjrfllepzooxuonq'),
                                            secure=())
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
logger = logging.getLogger()
logger.addHandler(smtp_handler)

cursor = None # db cursor for executing queries

def db_connect():
    # connect to postgres DB
    dbc = urlparse(DB_URL)
    HOST_NAME = dbc.hostname # change between 'localhost' and dbc.hostname depending on if dev or prod, respectively
    conn = psycopg2.connect(
        dbname=dbc.path.lstrip('/'),
        user=dbc.username,
        password=dbc.password,
        host=HOST_NAME,
        port=dbc.port,
        sslmode='disable',
        cursor_factory=RealDictCursor
    )
    conn.autocommit = True
    global cursor 
    cursor = conn.cursor()

def ping_db():
    print('pinging db...')
    cursor.execute('SELECT 1')
    print(cursor.fetchall())

@bot.event 
async def on_ready():
    db_connect()
    # pings DB every 30 seconds to keep connection alive. this is a fly.io problem, it closes after 60 idle seconds. can be changed to 1500 (25min) for local testing
    KeepDBAlive(30, ping_db)
    print("Bot started!") # prints to the console when the bot starts

@bot.event
async def on_command_error(interaction, error): # provides error embeds when things go wrong
    if(isinstance(error, commands.CommandNotFound)): # general command not found error
        embed = nextcord.Embed(
            title=":x: Please Use Slash Commands!",
            color=0xff2600,
            description="GTAVehicleBot is no longer using legacy commands as a result of Discord's push towards slash commands. Type / to get started."
        )
        embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)")
    elif(isinstance(error, commands.MissingPermissions) or error == "Missing Permissions"):
        embed = nextcord.Embed(
            title=":grey_exclamation: Insufficient Permissions",
            color=0xffdd00,
            description="You don't have permission to run this command."
        )
    elif("http" in str(error) and "429" in str(error)):
        embed = nextcord.Embed(
            title=":x: Too Many Requests!",
            color=0xff2600,
            description="You're submitting too many requests to the bot! Wait a little bit before using it again."
        )
        embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)")
    elif("http" in str(error) and "503" in str(error)):
        embed = nextcord.Embed(
            title=":x: Sheets API Unavailable!",
            color=0xff2600,
            description="This bot uses the Google Sheets API, which seems to be unavailable right now for unknown reasons. Check back later and try again."
        )
        embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)")
    elif 'UniqueViolation' in str(error):
        embed = nextcord.Embed(
            title=":x: Vehicle Already Exists!",
            color=0xff2600,
            description="The vehicle being inserted into the DB already exists."
        )
        embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)")
    elif 'psycopg2.errors' in str(error):
        embed = nextcord.Embed(
            title=":x: Database Error!",
            color=0xff2600,
            description="An unexpected database error occurred. <@339817929577332747> has been notified."
        )
        embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)")
    else:
        logger.exception('Unhandled Exception. Error: ' + str(error))
        embed = nextcord.Embed(
            title=":x: An Error Has Occurred!",
            color=0xff2600,
            description="An unexpected error occurred. <@339817929577332747> has been notified."
        )
        embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)")
    await interaction.send(embed=embed)

@bot.slash_command(name='help', description="General help command. Use me if you're confused!", guild_ids=productionserverids) # general help embed
async def help_func(interaction : Interaction):
    try:
        embed = nextcord.Embed(
            title="Welcome to GTABot!",
            description="Use this bot to look up information on GTA V and GTA Online vehicles.\nThis bot exclusively uses slash commands.\n[] indicates required argument, () is optional.",
            color=0x34ebae
        )
        embed.add_field(name="vehicleinfo [vehicle name]", value="Provides a bunch of information on a GTA Online or GTA V vehicle that you input.", inline=False)
        embed.add_field(name="flags", value="Returns a text guide on handling flags in GTA Online that you'll see the 'vehicleinfo' command mention.", inline=False)
        embed.add_field(name="topvehicles [vehicle class] (number of vehicles) (lap time/top speed)", value="Returns a list of vehicles of a certain class sorted by either lap times or top speeds. If not entered, # of vehicles will default up to 10, and lap time/top speed will default to lap time. \n__Example:__ topvehicles Sports 3 lap time", inline=False)
        embed.add_field(name="staffvehicle [staff member] [vehicle]", value="Displays a vehicle from the chosen staff members' garage.", inline=False)
        embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)")
        await interaction.send(embed=embed)
    except:
        print(sys.exc_info())
        await on_command_error(interaction, sys.exc_info()[0])    

async def vehicleinfo_createvehicleembed(vehicle, was_guess, interaction):
    print('create embed vehicle: ', vehicle, 'guess: ', was_guess)
    # detect closed DB connection and reconnect if closed
    try:
        cursor.execute('SELECT 1')
    except:
        db_connect()
    vehicle_id = vehicle[0]
    vehicle = re.sub(r"[^a-z0-9 ]","", vehicle[1].lower().strip()) # format vehicle again for use searching - if it's a guess it'll be unformatted
    # query for vehicle and return
    sql = "SELECT * FROM vehicleinfo WHERE modelid = %s LIMIT 1"
    cursor.execute(sql, [vehicle_id])
    car = cursor.fetchone()
    if car:
        if not car['name']: # if the name is blank that's the cutoff for not enough info
            embed = nextcord.Embed(
                    title=":grey_exclamation: Vehicle Data Incomplete!",
                    color=0xffdd00,
                    description="This vehicle needs more information filled in before it can be viewed"
            )
            return embed
        embed_title = "" # changes depending on if the vehicle has a manufacturer or not
        if not car['manufacturer']:
                embed_title=car['name']
        else:
            embed_title=car['manufacturer'] + " " + car['name']
        embed = nextcord.Embed( 
            title=embed_title,
            color=0x03fc45
        )
        default_blank_string = "Unknown!"
        if car['custvideo']: # display DCA customization video if it exists/vehicle can be customized
            embed.description = "Customization Video: " + car['custvideo']

        if car['class']:
            class_title = "Class"
            if "Not Raceable" not in car['class'] and "," in car['class']: # multiple race classes
                class_title = "Race Classes"
            elif car['laptime_byclass']: # we know it's a race class if this exists, but only one
                class_title = 'Race Class'
            embed.add_field(name=class_title, value=car['class'], inline=True)
        else:
            embed.add_field(name="Class", value=default_blank_string, inline=True)

        if car['price'] or car['price'] == 0:
            embed.add_field(name="Base Price", value='${:,}'.format(car['price']), inline=True)
        else:
            embed.add_field(name="Base Price", value=default_blank_string, inline=True)

        if car['drivetrain']:
            embed.add_field(name="Drivetrain", value=car['drivetrain'], inline=True)
        else:
            embed.add_field(name="Drivetrain", value=default_blank_string, inline=True)

        if not car['laptime']:
            embed.add_field(name="Lap Time", value='No Lap Time Set', inline=True)
        elif not car['laptime_byclass']:
            embed.add_field(name="Lap Time", value=car['laptime'], inline=True)
        else:
            embed.add_field(name="Lap Time / Lap Time Position in Class", value=car['laptime'] + " / " + car['laptime_byclass'], inline=True)

        if not car["topspeed"]:
            embed.add_field(name="Top Speed", value="No Top Speed Set", inline=True)
        elif not car['topspeed_byclass']:
            embed.add_field(name="Top Speed", value=car['topspeed'] + 'mph', inline=True)
        else:
            embed.add_field(name="Top Speed / Top Speed Position in Class", value=car['topspeed'] + 'mph / ' + car['topspeed_byclass'], inline=True)
        
        if car["numseats"]:
            embed.add_field(name="Number of Seats", value=car['numseats'], inline=True)
        else:
            embed.add_field(name="Number of Seats", value=default_blank_string, inline=True)
        
        if car['flags']:
            embed.add_field(name="Handling Flags", value=car['flags'], inline=True)
        else:
            embed.add_field(name="Handling Flags", value=default_blank_string, inline=True)
        
        if not car['dlc']:
            embed.add_field(name="DLC", value=default_blank_string, inline=True)
        else:
            embed.add_field(name="DLC", value=car['dlc'], inline=True)
        
        embed.add_field(name="Other Notes", value=car['othernotes'], inline=True) # no worries about blanks, None is good
        
        if car['image']:
            embed.set_image(url=car['image'])
        
        if was_guess:
            embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)\nThanks to Broughy1322 for much of the vehicle data!\nBest Guess Match")
        else:
            embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)\nThanks to Broughy1322 for much of the vehicle data!\n")
    
    else:
        print(sys.exc_info())
        await on_command_error(interaction, "psycopg2.errors.DatabaseError")
    return embed

@bot.slash_command(name='vehicleinfo', description="Returns a bunch of info about a chosen GTA Online vehicle", guild_ids=productionserverids)
async def vehicleinfo_findvehicle(interaction: Interaction, input:str): # main function to get GTA vehicle info from the google sheet. on_command_error handles all errors
    # detect closed DB connection and reconnect if closed
    try:
        cursor.execute('SELECT 1')
    except:
        db_connect()
    try:
        # pull names from DB -> remove everything but spaces and alphanumeric like the helper from whole list, make a list of strings
        cursor.execute("SELECT modelid, name FROM vehicleinfo")
        vehicles_db_list = cursor.fetchall()
        vehicles_list = {} # dict of all vehicles we currently have, from DB
        for veh in vehicles_db_list:
            if veh['name']: # no name from upsert or another method of adding, don't use it for search
                vehicles_list[veh['modelid']] = veh['name']
        
        result_arr = vehicleinfo_helper.find_vehicle(input, vehicles_list)
        vehicle = result_arr[0]
        was_exact = result_arr[1]
        was_guess = result_arr[2]
        
        # if no results, return idk embed
        if vehicle == 'not found':
            embed = nextcord.Embed(
                        title=":grey_exclamation: Vehicle Not Found!",
                        color=0xffdd00,
                        description="Couldn't find that vehicle, please try another search"
                )
            await interaction.send(embed=embed)

        # if single result, need to convert the exact match of the ingame name to the model id for a query and run query
        elif was_guess == True or was_exact == True:
            embed = await vehicleinfo_createvehicleembed(vehicle, was_guess, interaction)
            if embed:
                await interaction.send(embed=embed)

        # if multiple results, return suggestions embed with first 5 array members
        else:
            print('multi suggs')
            vehicle_suggestions = vehicle # for ease of reading
            suggestions_string = ""
            emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
            iterator = 0
            for i in range(0, len(vehicle_suggestions)): # put together the suggestions for the embed
                if(iterator < 5):
                    suggestions_string += emojis[i] + ": " + str(vehicle_suggestions[i][1]) + "\n"
                    iterator += 1
                else:
                    break
            embed = nextcord.Embed( # may need to send as-is depending on how bad the suggestions are. Could end up with 0.
                    title=":grey_exclamation: Vehicle Not Found!",
                    color=0xffdd00,
                    description="I couldn't find the exact vehicle name you submitted. Here's the closest I could come up with."
                    )
            embed.add_field(name="Did You Mean...", value=suggestions_string, inline=False) # add it to the embed and send it
            await interaction.send(embed=embed)
            message = await interaction.original_message() # grab message we just sent to add reactions to it
            for i in range(0, iterator):
                await message.add_reaction(emojis[i])
            
            def check(reaction, user):
                return str(reaction.emoji) in emojis and user == interaction.user
            confirmation = await bot.wait_for("reaction_add", check=check)
            car_to_use = '' # set below, used in call to helper for newfound vehicle
            car_modelid = '' # set below, used in call to helper for newfound vehicle
            if "1️⃣" in str(confirmation):
                car_modelid = vehicle_suggestions[0][0]
                car_to_use = vehicle_suggestions[0][1]
            elif "2️⃣" in str(confirmation):
                car_modelid = vehicle_suggestions[1][0]
                car_to_use = vehicle_suggestions[1][1]
            elif "3️⃣" in str(confirmation):
                car_modelid = vehicle_suggestions[2][0]
                car_to_use = vehicle_suggestions[2][1]
            elif "4️⃣" in str(confirmation):
                car_modelid = vehicle_suggestions[3][0]
                car_to_use = vehicle_suggestions[3][1]
            elif "5️⃣" in str(confirmation):
                car_modelid = vehicle_suggestions[4][0]
                car_to_use = vehicle_suggestions[4][1]
            # send second wait embed, this one gets deleted.
            embed_wait_2 = nextcord.Embed(
            title=":mag: Searching for " + car_to_use + "...",  
            color=0x7d7d7d
            )
            second_wait_message = await interaction.send(embed=embed_wait_2)
            # send message
            embed = await vehicleinfo_createvehicleembed([car_modelid, car_to_use], False, interaction)
            await interaction.send(embed=embed)
            await second_wait_message.delete()
    except:
        print(sys.exc_info())
        await on_command_error(interaction, sys.exc_info()[0])

@bot.slash_command(name='flags', description="Returns a guide on handling flags in GTA Online.", guild_ids=productionserverids)
async def explain_handling_flags(interaction : Interaction):
    try:
        embed = nextcord.Embed( 
                title="Handling Flags Guide",
                color=0x03fc45,
                description="Advanced Handling Flags are certain values Rockstar places on GTA vehicles in the code to make them handle differently. Here's an explanation:"
            )
        embed.add_field(name="Bouncy", value="This gives the vehicle very bouncy suspension, which can lead to it being hard to control. But, it can also make it much faster. In GTA, when any vehicle without the Engine flag goes over a bump, it gains speed. This is called 'curb boosting'. This is made much more significant on vehicles with this flag because of the bouncy suspension, hence why they accelerate faster over roads that aren't perfectly flat. Prime examples of vehicles with this flag are the Itali GTO and Toros.", inline=False)
        embed.add_field(name="Suspension", value="This is very simple - the lower the vehicle's suspension is, the better the grip is and the better lap times you'll get. Prime examples of vehicles with this flag are the Vectre and Sultan RS Classic.", inline=False)
        embed.add_field(name="Engine", value="This was Rockstar's attempt to combat curb boosting. When vehicles with this flag travel over a bump, their engine loses power instead of gaining it. This results in a strange sounding engine note, a slower car, and a worse driving experience overall. All cars that have this flag also have the Bouncy flag and have their mid-drive speed boost (AKA double clutch) disabled. Prime examples of vehicles with this flag are the Entity XXR and Ellie.", inline=False)
        embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)")
        await interaction.send(embed=embed)
    except:
        print(sys.exc_info())
        await on_command_error(interaction, sys.exc_info()[0])

# example: str = SlashOption(required=False, default=None)
@bot.slash_command(name='topvehicles', description="Gets a list of vehicles and their stats. Only shows raceable classes", guild_ids=productionserverids)
async def find_top_vehicles(
    interaction: Interaction,
    vehicle_class:str = SlashOption(required=True, choices=['Arena', 'Boats', 'Compacts', 'Coupes', 'Cycles', 'Fighter Jets', 'Go-Kart',
                                                             'Helicopters', 'Motorcycles', 'Muscle', 'Off-Road', 'Open Wheel', 'Planes', 
                                                             'Sedans', 'Special', 'Sports', 'Sports Classics', 'Supers', 'SUVs', 'Tuner', 
                                                             'Utility', 'Vans'
                                                            ]),
    number_of_vehicles:int = SlashOption(required=False, default=10), 
    metric:str = SlashOption(required=False, default='Lap Time', choices=['Lap Time', 'Top Speed'])
):
    # detect closed DB connection and reconnect if closed
    try:
        cursor.execute('SELECT 1')
    except:
        db_connect()
    try:
        print("INPUT TO TOPVEHICLES. Class: " + vehicle_class + ", number: " + str(number_of_vehicles) + ", metric: " + metric)
        # validate input
        error_embed = None
        if not str(number_of_vehicles).isnumeric():
            error_embed = nextcord.Embed(
                    title=":grey_exclamation: Bad input!",
                    color=0xffdd00,
                    description='Number of vehicles must be only a number'
            ) 
        elif number_of_vehicles == 0: # stop here if user inputs 0 vehicles
            error_embed = nextcord.Embed(
                    title=":grey_exclamation: You Cannot Search for Zero Vehicles",
                    color=0xffdd00
            )
        if error_embed:
            await interaction.send(embed=error_embed)
            return 
        # otherwise, look for the data
        number_of_vehicles = abs(number_of_vehicles) # in case of negative input
        result = topvehicles_helper.get_top_vehicles(cursor, vehicle_class, metric, number_of_vehicles) # find what we need in DB, returns 2darray

        vehicle_string = ""
        for vehicle in result:
            if vehicle[0] == '1':
                vehicle_string += ":first_place: **__1st:__** "
            elif vehicle[0] == '2':
                vehicle_string += ":second_place: **__2nd:__** "
            elif vehicle[0] == '3':
                vehicle_string += ":third_place: **__3rd:__** "
            else:
                vehicle_string += "**__#" + vehicle[0] + ":__** "
        
            if vehicle[1] == None: # no manufacturer = don't include
                vehicle_string += "**" + vehicle[2] + ": **"
            else:
                vehicle_string += "**" + vehicle[1] + " " + vehicle[2] + ": **"
            if(metric == "Lap Time"):
                vehicle_string += vehicle[3] + " / " + vehicle[4] + "mph\n"
            else: # top speed
                vehicle_string += vehicle[3] + "mph / " + vehicle[4] + "\n"
        
        if(metric == "Lap Time"):
            title_string = "Top " + str(len(result)) + " " + vehicle_class + " (Lap Time)"
            embed = nextcord.Embed(   
                title=title_string,
                color=0x03fc45
            )
        else: # top speed
            title_string = "Top " + str(len(result)) + " " + vehicle_class + " (Top Speed)"
            embed = nextcord.Embed(
                title=title_string,
                color=0x03fc45
            )
        if len(vehicle_string) > 1024:
            stats_rows = vehicle_string.splitlines()
            embed_strings = [] # strings of max of 1024 in length, one per embed used
            current_embed_string = ""
            non_statistics_strings_length = len(title_string + "Bot created by MrThankUvryMuch#9854. Thanks to Broughy1322 for much of the vehicle data!" + "Performance Statistics" + " Cont.")
            for vehicle in stats_rows:
                if len(current_embed_string + vehicle + "\n") <= (1024 - non_statistics_strings_length): # accomodates title etc in embed aside from actual data
                    current_embed_string += str(vehicle) + "\n"
                else:
                    embed_strings.append(current_embed_string)
                    current_embed_string = str(vehicle) + "\n"
            if len(current_embed_string) > 0: # adds last of vehicles to the embed string
                embed_strings.append(current_embed_string)
            embed.add_field(name="Performance Statistics", value=embed_strings[0], inline=True)
            embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854). Thanks to Broughy1322 for much of the vehicle data!")
            await interaction.send(embed=embed)
            for i in range(1, len(embed_strings)):
                new_embed = nextcord.Embed(
                    title=title_string + " Cont.",
                    color=0x03fc45
                )
                new_embed.add_field(name="Performance Statistics", value=embed_strings[i], inline=True)
                embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854). Thanks to Broughy1322 for much of the vehicle data!")
                await interaction.send(embed=new_embed)

        else:
            embed.add_field(name="Performance Statistics", value=vehicle_string, inline=True)
            embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854). Thanks to Broughy1322 for much of the vehicle data!")
            await interaction.send(embed=embed)
    except:
        print(sys.exc_info())
        await on_command_error(interaction, sys.exc_info()[0])

async def staffvehicle_send_data(car_array): # returns embed for staffvehicle
    # car array has 13 fields in it
    # format tital appropriately, remove manufacturer if needed
    if("VEHICLE DATA INCOMPLETE!" in car_array):
        embed = nextcord.Embed(
            title=":grey_exclamation: Vehicle Data Incomplete!",
            color=0x6911cf,
            description="Some of this vehicle's info hasn't been completed yet. Check back later."
        )
        return embed
    elif("range not set, but it should be" in car_array):
        raise ValueError("Range on 2nd search of staffvehicle wasn't set to a number!")
    embed_title = ""
    if(car_array[0] == "-"): # manufacturer
        embed_title=car_array[12] + "'s " + car_array[1],
    else:
        embed_title=car_array[12] + "'s " + car_array[0] + " " + car_array[1],
    embed_title = re.sub('["(),]',"", str(embed_title)) # title format is messed up for NO reason without this, must be a nextcord bug
    if "Arena" in embed_title:
        embed_title = embed_title.replace("Arena", "(Arena)")
    elif "Racecar" in embed_title:
        embed_title = embed_title.replace("Racecar", "(Racecar)")
    embed = nextcord.Embed( 
        title=embed_title,
        color=0x03fc45
    )
    embed.add_field(name="Class", value=car_array[2], inline=True)
    embed.add_field(name="Garage", value=car_array[3], inline=True)
    embed.add_field(name="Primary Color", value=car_array[4], inline=True)
    embed.add_field(name="Secondary Color", value=car_array[5], inline=True)
    embed.add_field(name="Pearlescent", value=car_array[6], inline=True)
    embed.add_field(name="Wheels", value=car_array[8], inline=True)
    embed.add_field(name="Wheel Color", value=car_array[9], inline=True)
    embed.add_field(name="Plate Text", value=car_array[10], inline=True)
    embed.add_field(name="Other Notes", value=car_array[11], inline=True)
    embed.set_image(url=car_array[7])
    if(car_array[12] == "Not Exact Match"):
        embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)\nBest Guess Match")
    else:
        embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)")
    return embed

async def staffvehicle_multiple_exacts(car_array, staff_member, interaction):
    embed = nextcord.Embed(
        title=":grey_exclamation: Multiple of the Same Vehicle!",
        color=0xffdd00,
        description="Looks like " + str(staff_member) + " has multiple of those."
    )
    exact_matches_string = ""
    final_range = "range not set, but it should be"
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    iterator = 0
    for i in range(0, len(car_array)): # put together the matches for the embed
        if(iterator < 5):
            exact_matches_string += emojis[i] + ": **" + str(car_array[1][i][0]) + "** - " + str(car_array[1][i][1]) + "\n"
            iterator += 1
        else:
            break
    embed.add_field(name="Take Your Pick:", value=exact_matches_string, inline=False)
    await interaction.send(embed=embed)
    async for message in interaction.channel.history(limit=20):
        if not message.embeds:
            continue
        elif message.embeds[0].title == embed.title and message.embeds[0].color == embed.color:
            react_to_me = message
            break
    for i in range(0, iterator):
        await react_to_me.add_reaction(emojis[i])
    
    def check(reaction, user):
        return str(reaction.emoji) in emojis and user == interaction.user
    confirmation = await bot.wait_for("reaction_add", check=check)
    car_to_use = car_array[1][0][0] # guaranteed to be the same car name, so just pick the first one
    if "1️⃣" in str(confirmation):
        final_range = car_array[1][0][2]
    elif "2️⃣" in str(confirmation):
        final_range = car_array[1][1][2]
    elif "3️⃣" in str(confirmation):
        final_range = car_array[1][2][2]
    elif "4️⃣" in str(confirmation):
        final_range = car_array[1][3][2]
    elif "5️⃣" in str(confirmation):
        final_range = car_array[1][4][2]
    # send second wait embed, this one gets deleted.
    embed_wait_2 = nextcord.Embed(
    title=":mag: Searching for " + staff_member + "'s " + car_to_use + "...",  
    color=0x7d7d7d
    )
    second_wait_message = await interaction.send(embed=embed_wait_2)
    # send message
    await interaction.send(embed=await staffvehicle_send_data(sheetparser_searchstaffvehicles.main(staff_member, car_to_use, final_range)))
    await second_wait_message.delete()


@bot.slash_command(name='staffvehicle', description="Returns a vehicle from a staff members' garage", guild_ids=productionserverids)
async def find_staff_vehicle(
    interaction : Interaction, 
    vehicle:str,
    staff_member:str = SlashOption(choices=["Emperor", "Rad", "Alex", "Dornier", "Ritz"], required=True),
    ):
    try:
        print("INPUT TO STAFFVEHICLE. Vehicle: " + vehicle + ", staff_member: " + staff_member)
        car_array = sheetparser_searchstaffvehicles.main(staff_member, vehicle, "N/A") # find the staff members' car, name - pri color
        if("MULTIPLE EXACT MATCHES" in car_array):
            await staffvehicle_multiple_exacts(car_array, staff_member, interaction) # handle multiple exact matches
        elif("VEHICLE DATA INCOMPLETE!" in car_array):
            embed = nextcord.Embed(
                title=":grey_exclamation: Vehicle Data Incomplete!",
                color=0x6911cf,
                description="Some of this vehicle's info hasn't been completed yet. Check back later."
            )
            await interaction.send(embed=embed)
        elif("ERROR: Vehicle not found" in car_array): # if not found and no suggestions, say person doesn't own the vehicle
            embed = nextcord.Embed(
                title=":grey_exclamation: Staff Vehicle Not Found!",
                color=0xffdd00,
                description="Couldn't find that in " + str(staff_member) + "'s garages."
            )
            await interaction.send(embed=embed)
        elif("TRY AGAIN: I have suggestions" in car_array): # didn't find singular vehicle but has multiple suggestions
            embed = nextcord.Embed(
                title=":grey_exclamation: Staff Vehicle Not Found!",
                color=0xffdd00,
                description="Couldn't find that exact vehicle in " + str(staff_member) + "'s garages, but I have some suggestions:"
            )
            vehicle_suggestions = sorted(car_array[1], key=lambda x: x[1], reverse=True) # sorts suggestions, using this from now on
            print("NOT FOUND, SUGGESTIONS SORTED: ", vehicle_suggestions)
            # check, if our highest ratio is decent then send off the suggestion list
            vehicle_suggestions_updated = []
            for i in range(0, len(vehicle_suggestions)): # remove all really bad suggestions
                if not(vehicle_suggestions[i][1] < 0.5 and vehicle_suggestions[i][2] != "EP"):
                    vehicle_suggestions_updated.append(vehicle_suggestions[i])
            if(len(vehicle_suggestions_updated) == 0): # no suggestions left, they were all bad :/ send stock vehicle not found embed
                await interaction.send(embed=embed)
            else: # still at least one good suggestion left, so show it/them
                suggestions_string = ""
                emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
                iterator = 0
                for i in range(0, len(vehicle_suggestions_updated)): # put together the suggestions for the embed
                    if(iterator < 5):
                        suggestions_string += emojis[i] + ": " + str(vehicle_suggestions_updated[i][0]) + "\n"
                        iterator += 1
                    else:
                        break
                embed.add_field(name="Did You Mean...", value=suggestions_string, inline=False) # add it to the embed and send it
                await interaction.send(embed=embed)
                message = await interaction.original_message() # grab message we just sent to add reactions to it
                for i in range(0, iterator):
                    await message.add_reaction(emojis[i])
                
                def check(reaction, user):
                    return str(reaction.emoji) in emojis and user == interaction.user
                confirmation = await bot.wait_for("reaction_add", check=check)
                car_to_use = '' # set below, used in call to sheetparser for newfound vehicle
                if "1️⃣" in str(confirmation):
                    car_to_use = vehicle_suggestions_updated[0][0]
                elif "2️⃣" in str(confirmation):
                    car_to_use = vehicle_suggestions_updated[1][0]
                elif "3️⃣" in str(confirmation):
                    car_to_use = vehicle_suggestions_updated[2][0]
                elif "4️⃣" in str(confirmation):
                    car_to_use = vehicle_suggestions_updated[3][0]
                elif "5️⃣" in str(confirmation):
                    car_to_use = vehicle_suggestions_updated[4][0]
                # send second wait embed, this one gets deleted.
                embed_wait_2 = nextcord.Embed(
                title=":mag: Searching for " + staff_member + "'s " + car_to_use + "...",  
                color=0x7d7d7d
                )
                second_wait_message = await interaction.send(embed=embed_wait_2)
                
                # take precautions with multiple exact matches
                car_array = sheetparser_searchstaffvehicles.main(staff_member, car_to_use, "N/A")
                if "MULTIPLE EXACT MATCHES" not in car_array:
                    await interaction.send(embed=await staffvehicle_send_data(car_array)) # send with good data
                    await second_wait_message.delete()
                else:
                    await second_wait_message.delete()
                    await staffvehicle_multiple_exacts(car_array, staff_member, interaction) # handle multiple exact matches
        elif car_array[len(car_array)-1] == "MAY BE MULTIPLE EXACTS": # none of the above + not a singular exact match = is an inferred misspell. need to check for multiples.
            car_array = sheetparser_searchstaffvehicles.main(staff_member, car_array[1], "N/A")
            if "MULTIPLE EXACT MATCHES" not in car_array:
                await interaction.send(embed=await staffvehicle_send_data(car_array)) # send with good data
            else:
                await staffvehicle_multiple_exacts(car_array, staff_member, interaction) # handle multiple exact matches
        else: # otherwise, it found it normally. So display the data
            await interaction.send(embed=await staffvehicle_send_data(car_array))
    except:
        print(sys.exc_info())
        await on_command_error(interaction, sys.exc_info()[0])


@bot.slash_command(name='updatevehicledata', description="Scrapes gtacars.net and puts all updated info in the bot DB", guild_ids=productionserverids)
async def update_data(interaction : Interaction):
    # detect closed DB connection and reconnect if closed
    try:
        cursor.execute('SELECT 1')
    except:
        db_connect()
    try:
        if(not interaction.user.guild_permissions.ban_members):
            await on_command_error(interaction, "Missing Permissions")
        else:
            in_progress_embed = nextcord.Embed(
            title=":jigsaw: Updating data...",
            color=0x7d7d7d,
            description="Sit back, relax. This will take a few minutes."
            )
            await interaction.send(embed=in_progress_embed)

            updated_vehicle_info_arr = []
            to_insert_vehicle_info_arr = []
            cursor.execute("SELECT * FROM vehicleinfo;")
            old_vehicleinfo = cursor.fetchall()

            # create vehicleinfo backup table
            cursor.execute('''SELECT EXISTS (
                        SELECT FROM pg_tables
                        WHERE tablename = 'vehicleinfo_bak'
            );''')
            if cursor.fetchone()['exists']:
                cursor.execute("DROP TABLE vehicleinfo_bak;")
            print('creating backup table...')
            cursor.execute('''CREATE TABLE vehicleinfo_bak (
                            modelid varchar(50),
                            manufacturer varchar(50),
                            name varchar(75),
                            class varchar(50),
                            laptime varchar(25),
                            topspeed varchar(25),
                            image varchar(150),
                            flags varchar(50),
                            custvideo varchar(50),
                            laptime_byclass VARCHAR(150),
                            topspeed_byclass VARCHAR(150),
                            drivetrain varchar(5),
                            numseats varchar(10),
                            price INT,
                            dlc varchar(100),
                            othernotes varchar(500)
                            );''')
                
            # arrange columns and values for insert to backup table
            columns = []
            first_vehicle = old_vehicleinfo[0]
            for column in first_vehicle:
                columns.append(column)

            query = "INSERT INTO vehicleinfo_bak ({}) VALUES %s".format(','.join(columns))

            # puts dict values (car info) for each car into a list for insertion into another list, which is a list of lists
            values = []
            for tuple in old_vehicleinfo:
                vehicle_arr = []
                for column in tuple:
                    vehicle_arr.append(tuple[column])
                values.append(vehicle_arr)
            
            print('inserting into backup table...')
            execute_values(cursor, query, values)
            
            print("collecting vehicles to insert/modify...")
            cursor.execute("SELECT modelid FROM vehicleinfo")
            modelids_db_list = cursor.fetchall()

            for veh in modelids_db_list:
                modelid = veh['modelid']
                url = "https://gtacars.net/gta5/" + modelid
                new_vehicleinfo = updatevehicledata_helper.get_new_vehicle_data(url, modelid)
                if new_vehicleinfo:
                    # find the member of old_vehicleinfo with a modelid that matches the modelid of the current new vehicle
                    old_vehicle_to_compare = []
                    vehicle_found = False
                    for old_vehicle in old_vehicleinfo:
                        if old_vehicle['modelid'] == new_vehicleinfo['modelid']:
                            old_vehicle_to_compare = old_vehicle
                            vehicle_found = True
                            break
                    if vehicle_found: # vehicle exists to inspect to potentially update
                        # loop through every field in the new vehicle, if one differs compared to the old one, add the new vehicle to the updated arr
                        for new_field in new_vehicleinfo:
                            if str(new_vehicleinfo[new_field]).strip() != str(old_vehicle_to_compare[new_field]).strip():
                                updated_vehicle_info_arr.append(new_vehicleinfo)
                                break
                    else: # vehicle model id not found, must be new. add to insert array
                        to_insert_vehicle_info_arr.append(new_vehicleinfo)
            
            if len(updated_vehicle_info_arr) > 0:
                # check for update temp table in case, delete if so
                cursor.execute('''SELECT EXISTS (
                            SELECT FROM pg_tables
                            WHERE tablename = 'vehicleinfo_tempupdate'
                );''')
                var = cursor.fetchone()['exists']
                if var:
                    cursor.execute("DROP TABLE vehicleinfo_tempupdate;")

                print("creating temp update table...")
                temptable_update = '''CREATE TABLE vehicleinfo_tempupdate (
                                    modelid varchar(50),
                                    manufacturer varchar(50),
                                    name varchar(75),
                                    class varchar(50),
                                    laptime varchar(25),
                                    topspeed varchar(25),
                                    image varchar(150),
                                    flags varchar(50),
                                    laptime_byclass VARCHAR(150),
                                    topspeed_byclass VARCHAR(150),
                                    drivetrain varchar(5),
                                    numseats varchar(10),
                                    price INT);'''
                print("creating temp update table")
                cursor.execute(temptable_update)

                # put updated vehicles into temp update table
                columns = updated_vehicle_info_arr[0].keys()
                query = "INSERT INTO vehicleinfo_tempupdate ({}) VALUES %s".format(','.join(columns))
                # puts dict values (car info) into a list of lists as a list
                values = [[value for value in veh.values()] for veh in updated_vehicle_info_arr]
                print("inserting into update table...")
                execute_values(cursor, query, values)

                print("inserting updated values into update table...")
                cursor.execute('''UPDATE vehicleinfo v
                                    SET manufacturer = vtempu.manufacturer,
                                        name = vtempu.name,
                                        class = vtempu.class,
                                        laptime = vtempu.laptime,
                                        topspeed = vtempu.topspeed,
                                        image = vtempu.image,
                                        flags = vtempu.flags,
                                        laptime_byclass = vtempu.laptime_byclass,
                                        topspeed_byclass = vtempu.topspeed_byclass,
                                        drivetrain = vtempu.drivetrain,
                                        numseats = vtempu.numseats,
                                        price = vtempu.price
                                    FROM vehicleinfo_tempupdate vtempu
                                    WHERE v.modelid = vtempu.modelid;''')

                # delete update temp table now that we're finished
                print("dropping tempupdate table...")
                cursor.execute("DROP TABLE vehicleinfo_tempupdate;")

            
            if len(to_insert_vehicle_info_arr) > 0:
                # check for insert temp table in case, delete if so
                cursor.execute('''SELECT EXISTS (
                            SELECT FROM pg_tables
                            WHERE tablename = 'vehicleinfo_tempinsert'
                );''')
                if cursor.fetchone()['exists']:
                    cursor.execute("DROP TABLE vehicleinfo_tempinsert;")
                
                print("creating temp insert table...")
                temptable_insert = '''CREATE TABLE vehicleinfo_tempinsert (
                                    modelid varchar(50),
                                    manufacturer varchar(50),
                                    name varchar(75),
                                    class varchar(50),
                                    laptime varchar(25),
                                    topspeed varchar(25),
                                    image varchar(150),
                                    flags varchar(50),
                                    laptime_byclass VARCHAR(150),
                                    topspeed_byclass VARCHAR(150),
                                    drivetrain varchar(5),
                                    numseats varchar(10),
                                    price INT);'''
                cursor.execute(temptable_insert)

                # put new vehicles into temp insert table
                columns = to_insert_vehicle_info_arr[0].keys()
                query = "INSERT INTO vehicleinfo_tempinsert ({}) VALUES %s".format(','.join(columns))
                # puts dict values (car info) into a list of lists as a list
                values = [[value for value in veh.values()] for veh in to_insert_vehicle_info_arr]
                print("inserting new vehicles into temp insert table")
                execute_values(cursor, query, values)

                print("inserting new vehicles into vehicleinfo...")
                cursor.execute('''INSERT INTO vehicleinfo 
                            (modelid, manufacturer, name, class, laptime, topspeed, image, flags, laptime_byclass, topspeed_byclass, drivetrain, numseats, price)
                                SELECT modelid, manufacturer, name, class, laptime, topspeed, image, flags, laptime_byclass, topspeed_byclass, drivetrain, numseats, price
                                FROM vehicleinfo_tempinsert;''')

                # delete insert temp table now that we're finished
                print("dropping temp insert table...")
                cursor.execute("DROP TABLE vehicleinfo_tempinsert;")
            
            finished_embed = nextcord.Embed(
            title=":white_check_mark: Data Update Complete",  
            color=0x03fc45
            )
            finished_embed.add_field(name="Existing Vehicles Updated", value=len(updated_vehicle_info_arr), inline=False)
            finished_embed.add_field(name="New Vehicles Inserted", value=len(to_insert_vehicle_info_arr), inline=False)
            await interaction.send(embed=finished_embed)
    except:
        print(sys.exc_info())
        await on_command_error(interaction, sys.exc_info()[0])
    

@bot.slash_command(name='upsertvehicle', description="Update or insert a single vehicle. Only modelid is required", guild_ids=productionserverids)
async def upsert_vehicle(
    interaction: Interaction,
    insert_or_update:str = SlashOption(description="Updating an existing vehicle or inserting a new vehicle?", choices=["Update", "Insert"], required=True),
    modelid:str = SlashOption(description="Vehicle model ID - Something like 'formula' for the PR4, for example", required=True),
    manufacturer:str = SlashOption(description="Vehicle manufacturer - Truffade, for example", required=False),
    name:str = SlashOption(description="Vehicle name - Ardent, for example", required=False),
    race_class:str = SlashOption(description="Vehicle race class(es). Enter in a comma separated list like: SUVs, Sports", required=False),
    laptime:str = SlashOption(description="Vehicle lap time around Broughy's track. 0:59.293 for example.", required=False),
    topspeed:str = SlashOption(description="Vehicle top speed under Broughy's testing. 160.25 for example", required=False),
    image:str = SlashOption(description="Image link to the vehicle (must be a DIRECT link)", required=False),
    flags:str = SlashOption(description="Vehicle handling flags", choices=["None", "Engine", "Bouncy", "Suspension", "Engine, Bouncy", "Bouncy, Suspension", "Engine, Suspension", "Engine, Bouncy, Suspension"], required=False),
    customization_video:str = SlashOption(description="DCA customization video for the vehicle in question", required=False),
    laptime_byclass:str = SlashOption(description="Lap time position in class(es). Enter in list like: 4th out of 9 in SUVs, 2nd out of 9 in Sports", required=False),
    topspeed_byclass:str = SlashOption(description="Top speed position in class(es). Enter in list like: 4th out of 9 in SUVs, 2nd out of 9 in Sports", required=False),
    drivetrain:str = SlashOption(description="Vehicle drivetrain, if applicable", choices=["N/A", "RWD", "FWD", "AWD"], required=False),
    numseats:str = SlashOption(description="Number of seats in the vehicle. Enter only the number", required=False),
    price:str = SlashOption(description="Base price of the vehicle. Enter only the number", required=False),
    dlc:str = SlashOption(description="DLC the vehicle was released in. DLC name + year in parenthesis, like Base Game (2013)", required=False),
    othernotes:str = SlashOption(description="Other notes section. This will overwrite them, so add the existing ones you want to keep as well", required=False)
):
    # detect closed DB connection and reconnect if closed
    try:
        cursor.execute('SELECT 1')
    except:
        db_connect()
    try:
        if(not interaction.user.guild_permissions.ban_members):
            await on_command_error(interaction, "Missing Permissions")
        else:
            # put input values into dictionary for use later
            input_dict = locals()
            input_dict.pop('interaction')
            # input validation
            bad_fields, vehicle, input_dict = upsertvehicle_helper.validate_input(input_dict, cursor)
            if len(bad_fields) > 0:
                bad_fields_str = ""
                for field in bad_fields:
                    bad_fields_str += field + "\n\n"
                bad_fields_str.strip()
                bad_input_embed = nextcord.Embed(
                    title=":x: Bad Input!", 
                    description="**The input had the following issues:**\n\n" + bad_fields_str,
                    color=0xff2600
                    )
                await interaction.send(embed=bad_input_embed)
            else: # data is good
                # make keys of input match DB
                input_dict.pop('insert_or_update')
                input_dict['class'] = input_dict['race_class']
                input_dict['custvideo'] = input_dict['customization_video']
                input_dict.pop('race_class')
                input_dict.pop('customization_video')
                columns = list(input_dict.keys())

                if insert_or_update == 'Update':
                    in_progress_embed = nextcord.Embed(
                        title=":jigsaw: Updating vehicle...",
                        color=0x7d7d7d,
                        )
                    await interaction.send(embed=in_progress_embed)

                    query_str = "UPDATE vehicleinfo SET "
                    are_changes = False
                    for col in columns: # set which fields to update and construct query
                        if input_dict[col] and input_dict[col] != vehicle[col]:
                            input_dict[col] = input_dict[col].replace("'", "''") # escape single quotes to avoid errors
                            query_str += col + " = '" + input_dict[col] + "',"
                            are_changes = True
                    if are_changes:
                        query_str = query_str.rstrip(',') + " WHERE modelid = '" + vehicle['modelid'] + "'"
                        print('upsertvehicle update query: ', query_str)
                        cursor.execute(query_str)
                        complete_embed = nextcord.Embed(
                            title=":white_check_mark: Vehicle Updated!",
                            color=0x03fc45,
                            )
                        await interaction.send(embed=complete_embed)
                    else:
                        embed = nextcord.Embed(
                            title=":grey_exclamation: No Changes!",
                            color=0xffdd00,
                            description="Your input did not differ from the DB data, update not executed."
                        )
                        await interaction.send(embed=embed)
                
                elif insert_or_update == "Insert":
                    in_progress_embed = nextcord.Embed(
                        title=":jigsaw: Inserting vehicle...",
                        color=0x7d7d7d,
                        )
                    await interaction.send(embed=in_progress_embed)

                    query = "INSERT INTO vehicleinfo ({}) VALUES %s".format(','.join(columns))
                    # puts dict values (car info) into a list of lists as a list
                    values = tuple(value for value in input_dict.values())
                    print('upsertvehicle insert query: ', query)
                    cursor.execute(query, [values])
                    complete_embed = nextcord.Embed(
                        title=":white_check_mark: Vehicle Added!",
                        color=0x03fc45,
                    )
                    await interaction.send(embed=complete_embed)
    except:
        print(sys.exc_info())
        await on_command_error(interaction, sys.exc_info()[0])


# INVITE BOT BACK TO TEST SERVER USING
# MAIN BOT: https://discord.com/api/oauth2/authorize?client_id=800779921814323290&permissions=0&scope=bot%20applications.commands
# DEV: https://discord.com/oauth2/authorize?client_id=1136704389780873359&permissions=0&scope=bot%20applications.commands

bot.run(TOKEN)