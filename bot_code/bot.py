from email.mime import image
from logging import error
import os
from time import time
from typing import Iterable
from nextcord import ApplicationSubcommand, Interaction, SlashOption
import nextcord
from nextcord.ext.commands.core import check
from dotenv import load_dotenv
from nextcord.ext import commands
import sheetparser
import sheetparser_topvehicles
import sheetparser_searchstaffvehicles
import sheetparser_podium
import sheetparser_prizeride
import json
import re # regex
import sys # try except error capture
import logging
import logging.handlers


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

testserverid = [851239396689707078] # testing only
productionserverids = [715583253289107588, 696800707919085638]

bot = commands.Bot(command_prefix=',', case_insensitive=True)
bot.remove_command('help') # get rid of default help command and use mine instead

# create email logger to send to me on error
smtp_handler = logging.handlers.SMTPHandler(mailhost=("smtp.gmail.com", 587),
                                            fromaddr="GTAVehicleBot@gmail.com", 
                                            toaddrs="mrthankuvrymuch@gmail.com",
                                            subject=u"GTAVehicleBot error!",
                                            credentials=('GTAVehicleBot@gmail.com', 'sjrfllepzooxuonq'),
                                            secure=())
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
logger = logging.getLogger()
logger.addHandler(smtp_handler)

@bot.event 
async def on_ready():
    print("Bot started!") # prints to the console when the bot starts

@bot.event
async def on_command_error(interaction, error): # provides error embeds when things go wrong
    if(isinstance(error, commands.CommandNotFound)): # general command not found error
        print(error)
        embed = nextcord.Embed(
            title=":x: Please Use Slash Commands!",
            color=0xff2600,
            description="GTAVehicleBot is no longer using legacy commands as a result of Discord's push towards slash commands. Type / to get started."
        )
        embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)")
        await interaction.send(embed=embed)
    elif(isinstance(error, commands.MissingPermissions) or error == "Missing Permissions"):
        embed = nextcord.Embed(
            title=":grey_exclamation: Insufficient Permissions",
            color=0xffdd00,
            description="You don't have permission to run this command."
        )
        await interaction.send(embed=embed)
    elif("http" in str(error) and "429" in str(error)):
        embed = nextcord.Embed(
            title=":x: Too Many Requests!",
            color=0xff2600,
            description="You're submitting too many requests to the bot! Wait a little bit before using it again."
        )
        embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)")
        await interaction.send(embed=embed)
    elif("http" in str(error) and "503" in str(error)):
        embed = nextcord.Embed(
            title=":x: Sheets API Unavailable!",
            color=0xff2600,
            description="This bot uses the Google Sheets API, which seems to be unavailable right now for unknown reasons. Check back later and try again."
        )
        embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)")
        await interaction.send(embed=embed)
    else:
        print(error)
        logger.exception('Unhandled Exception. Error: ' + str(error))
        embed = nextcord.Embed(
            title=":x: An Error Has Occurred!",
            color=0xff2600,
            description="An unexpected error occurred. <@339817929577332747> has been notified."
        )
        embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)")
        await interaction.send(embed=embed)

@bot.slash_command(name='help', description="General help command. Use me if you're confused!", guild_ids=testserverid) # general help embed
async def help_func(interaction : Interaction):
    try:
        embed = nextcord.Embed(
            title="Welcome to GTABot!",
            description="Use this bot to look up information on GTA V and GTA Online vehicles.\nThis bot exclusively uses slash commands.\n[] indicates required argument, () is optional.",
            color=0x34ebae
        )
        embed.add_field(name="vehicleinfo [vehicle name]", value="Provides a bunch of information on a GTA Online or GTA V vehicle that you input.", inline=False)
        embed.add_field(name="podium", value="Displays current podium vehicle and future podium vehicle list.", inline=False)
        embed.add_field(name="flags", value="Returns a text guide on handling flags in GTA Online that you'll see the 'vehicleinfo' command mention.", inline=False)
        embed.add_field(name="topvehicles [vehicle class] (number of vehicles) (lap time/top speed)", value="Returns a list of vehicles of a certain class sorted by either lap times or top speeds. If not entered, # of vehicles will default up to 10, and lap time/top speed will default to lap time. \n__Example:__ topvehicles Sports 3 lap time", inline=False)
        embed.add_field(name="staffvehicle [staff member] [vehicle]", value="Displays a vehicle from the chosen staff members' garage.", inline=False)
        embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)")
        await interaction.send(embed=embed)
        # saving these for the future
        #if ctx.author.guild_permissions.administrator:
            # embed.add_field(name="Admin Only Commands", value="**prefix [new prefix]:** Sets new prefix to use with this bot.\n**podiumupdate [future/current] [add/remove] [vehicle_name/vehiclename img_link]:** Updates the future or current podium vehicle on the podium vehicle list found with the podium command.\n\nMore commands coming soon!", inline=False)
    except:
        await on_command_error(interaction, sys.exc_info()[0])

async def vehicleinfo_helper(car_array): # on successful vehicle find, this organizes the embed
    # emojis for 1st, 2nd, 3rd in lap time/top speed position
    times_in_class = [car_array[8], car_array[9]]
    for i in range(0, len(times_in_class)):
        if(times_in_class[i] == "#1"):
            times_in_class[i] = ":first_place: 1st"
        elif("#1 in" in times_in_class[i]):
            times_in_class[i] = times_in_class[i].replace("#1 in", ":first_place: 1st in")
        elif(times_in_class[i] == "#2"):
            times_in_class[i] = ":second_place: 2nd"
        elif("#2 in" in times_in_class[i]):
            times_in_class[i] = times_in_class[i].replace("#2 in", ":second_place: 2nd in")
        elif(times_in_class[i] == "#3"):
            times_in_class[i] = ":third_place: 3rd"
        elif("#3 in" in times_in_class[i]):
            times_in_class[i] = times_in_class[i].replace("#3 in", ":third_place: 3rd in")
    car_array[8] = times_in_class[0]
    car_array[9] = times_in_class[1]

    no_drivetrain = ["Boats", "Cycles", "Helicopters", "Anti-Aircraft Trailer", "Thruster", "Oppressor Mk II", "Planes"]
    if(car_array[0] in no_drivetrain or car_array[1] in no_drivetrain):
        car_array[10] = "N/A"

    embed_title = "" # changes depending on if the vehicle has a manufacturer or not
    if(car_array[12] == "-"):
            embed_title=car_array[0]
    else:
        embed_title=car_array[12] + " " + car_array[0]
    
    embed = nextcord.Embed( 
        title=embed_title,
        color=0x03fc45
    )
    if car_array[7] != "N/A": # display DCA customization video if it exists/vehicle can be customized
        embed.description = "Customization Video: " + car_array[7]
    embed.add_field(name="Class", value=car_array[1], inline=True)
    embed.add_field(name="Base Price", value=car_array[13], inline=True)
    embed.add_field(name="Drivetrain", value=car_array[10], inline=True)
    embed.add_field(name="Lap Time / Lap Time Position in Class", value=car_array[2] + " / " + car_array[8], inline=True)
    embed.add_field(name="Top Speed / Top Speed Position in Class", value=car_array[3] + 'mph / ' + car_array[9], inline=True)
    embed.add_field(name="Number of Seats", value=car_array[11], inline=True)
    embed.add_field(name="Handling Flags?", value=car_array[5], inline=True)
    embed.add_field(name="DLC", value=car_array[14], inline=True)
    embed.add_field(name="Other Notes", value=car_array[15], inline=True)
    embed.set_image(url=car_array[4])
    if(car_array[6] == "Not Exact Match"):
        embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)\nThanks to Broughy1322 for much of the vehicle data!\nBest Guess Match")
    else:
        embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)\nThanks to Broughy1322 for much of the vehicle data!\n")
    return embed

@bot.slash_command(name='vehicleinfo', description="Returns a bunch of info about a chosen GTA Online vehicles", guild_ids=testserverid)
async def give_car(interaction: Interaction, vehicle:str): # main function to get GTA vehicle info from the google sheet. on_command_error handles all errors
    try:
        print("INPUT TO VEHICLEINFO: " + vehicle)
        car_array = sheetparser.main(vehicle)
        if("ERROR: Vehicle not found" in car_array): # didn't find anything
            embed = nextcord.Embed(
                    title=":grey_exclamation: Vehicle Not Found!",
                    color=0xffdd00,
                    description="I couldn't find the exact vehicle name you submitted and I have no suggestions."
            )
            await interaction.send(embed=embed)
        elif("TRY AGAIN: I have suggestions" in car_array): # didn't find singular vehicle but has multiple suggestions
            embed = nextcord.Embed( # may need to send as-is depending on how bad the suggestions are. Could end up with 0.
                    title=":grey_exclamation: Vehicle Not Found!",
                    color=0xffdd00,
                    description="I couldn't find the exact vehicle name you submitted. Here's the closest I could come up with."
            )
            vehicle_suggestions = sorted(car_array[1], key=lambda x: x[1], reverse=True) # sorts suggestions, using this from now on
            print("NOT FOUND, SUGGESTIONS SORTED: ", vehicle_suggestions)
            # check, if our highest ratio is decent then send off the suggestion list
            final_veh_suggs = []
            for i in range(0, len(vehicle_suggestions)): # remove all really bad suggestions
                if not(vehicle_suggestions[i][1] < 0.5 and vehicle_suggestions[i][2] != "EP"):
                    final_veh_suggs.append(vehicle_suggestions[i])
            if(len(final_veh_suggs) == 0): # all suggestions were bad :/ send stock vehicle not found embed
                await interaction.send(embed=embed)
            elif(len(final_veh_suggs) == 1): # 1 decent suggestion, run with it
                embed = await vehicleinfo_helper(sheetparser.main(final_veh_suggs[0][0]))
                await interaction.send(embed=embed)
            else: # still at least two good suggestions left, so show them
                not_found_suggestions_string = ""
                emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
                iterator = 0
                for i in range(0, len(final_veh_suggs)): # put together the suggestions for the embed
                    if(iterator < 5):
                        not_found_suggestions_string += emojis[i] + ": " + str(final_veh_suggs[i][0]) + "\n"
                        iterator += 1
                    else:
                        break
                embed.add_field(name="Did You Mean...", value=not_found_suggestions_string, inline=False) # add it to the embed and send it
                await interaction.send(embed=embed)
                message = await interaction.original_message() # grab message we just sent to add reactions to it
                for i in range(0, iterator):
                    await message.add_reaction(emojis[i])
                
                def check(reaction, user):
                    return str(reaction.emoji) in emojis and user == interaction.user
                confirmation = await bot.wait_for("reaction_add", check=check)
                car_to_use = '' # set below, used in call to sheetparser for newfound vehicle
                if "1️⃣" in str(confirmation):
                    car_to_use = final_veh_suggs[0][0]
                elif "2️⃣" in str(confirmation):
                    car_to_use = final_veh_suggs[1][0]
                elif "3️⃣" in str(confirmation):
                    car_to_use = final_veh_suggs[2][0]
                elif "4️⃣" in str(confirmation):
                    car_to_use = final_veh_suggs[3][0]
                elif "5️⃣" in str(confirmation):
                    car_to_use = final_veh_suggs[4][0]
                # send second wait embed, this one gets deleted.
                embed_wait_2 = nextcord.Embed(
                title=":mag: Searching for " + car_to_use + "...",  
                color=0x7d7d7d
                )
                second_wait_message = await interaction.send(embed=embed_wait_2)
                # send message
                embed = await vehicleinfo_helper(sheetparser.main(car_to_use))
                await interaction.send(embed=embed)
                await second_wait_message.delete()

        elif("VEHICLE DATA INCOMPLETE!" in car_array):
            embed = nextcord.Embed(
                title=":grey_exclamation: Vehicle Data Incomplete!",
                color=0x6911cf,
                description="Some of this vehicle's info hasn't been completed yet. Check back later."
            )
            await interaction.send(embed=embed)
        else: # successfully found vehicle off the bat
            embed = await vehicleinfo_helper(car_array)
            await interaction.send(embed=embed)
    except:
        await on_command_error(interaction, sys.exc_info()[0])

@bot.slash_command(name='flags', description="Returns a guide on handling flags in GTA Online.", guild_ids=testserverid)
async def explain_handling_flags(interaction : Interaction):
    try:
        embed = nextcord.Embed( 
                title="Handling Flags Guide",
                color=0x03fc45,
                description="Advanced Handling Flags are certain values Rockstar places on GTA vehicles in the code to make them handle differently. Here's an explanation:"
            )
        embed.add_field(name="Bouncy", value="This gives the vehicle very bouncy suspension, which can lead to it being hard to control. But, it can also make it much faster. In GTA, when any vehicle without the Lower Shift Points flag goes over a bump, it gains speed. This is called 'curb boosting'. This is made much more significant on vehicles with this flag because of the bouncy suspension, hence why they accelerate faster over roads that aren't perfectly flat. Prime examples of vehicles with this flag are the Itali GTO and Toros.", inline=False)
        embed.add_field(name="Lower Shift Points", value="Rockstar nerfed this flag with Criminal Enterprises DLC, making it nearly ineffective in order to fix the Tuner cars' nerf. Cars with this flag are now only slightly slower than if they were non-flagged. It used to disable curb boosting, handbrake boosting, and make vehicles upshift sooner, but does none of these anymore. Prime examples of vehicles with this flag are the Calico GTF and ZR350.", inline=False)
        embed.add_field(name="Gear Shift Overrev", value="All vehicles with this flag also have the Lower Shift Points flag. All cars with this flag are broken - they rev at redline way too much before upshifting (caused by the Criminal Enterprises DLC flag change). Prime examples of vehicles with this flag are the Entity XXR and Jester Classic.")
        embed.add_field(name="Suspension", value="This is very simple - the lower the vehicle's suspension is, the better the grip is and the better lap times you'll get. Prime examples of vehicles with this flag are the Vectre and Sultan RS Classic.", inline=False)
        embed.add_field(name="Anti-Boost", value="This flag removes the vehicle's ability to curb boost and brake boost. It's currently only present on the Open Wheel cars (BR8, PR4, DR1, R88).", inline=False)
        embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)")
        await interaction.send(embed=embed)
    except:
        await on_command_error(interaction, sys.exc_info()[0])


# example: str = SlashOption(required=False, default=None)
@bot.slash_command(name='topvehicles', description="Returns a list of vehicles and their performance statistics.", guild_ids=testserverid)
async def find_top_vehicles(
    interaction: Interaction,
    vehicle_class:str = SlashOption(required=True, choices=['Sports Classics', 'Motorcycles', 'Boats', 'Commercial', 'Compacts', 'Coupes', 'Cycles', 'Emergency',
                                                            'Helicopters', 'Industrial', 'Military', 'Muscle', 'Off-Road', 'Open Wheel', 'Planes', 'Sedans',
                                                            'Service', 'Sports', 'Supers', 'SUVs', 'Tuners', 'Utility', 'Vans'
                                                            ]),
    number_of_vehicles:int = SlashOption(required=False, default=10), 
    metric:str = SlashOption(required=False, default='Lap Time', choices=['Lap Time', 'Top Speed'])
):
    try:
        print("INPUT TO TOPVEHICLES. Class: " + vehicle_class + ", number: " + str(number_of_vehicles) + ", metric: " + metric)
        number_of_vehicles = abs(number_of_vehicles) # in case of negative input
        if number_of_vehicles == 0: # stop here if user inputs 0 vehicles
            error_embed = nextcord.Embed(
                    title=":grey_exclamation: You Cannot Search for Zero Vehicles",
                    color=0xffdd00
            )
            await interaction.send(embed=error_embed)
            return     
        # otherwise, look for the data
        result = sheetparser_topvehicles.main(number_of_vehicles, vehicle_class, metric) # find what we need on sheet, returns array

        vehicle_string = ""
        i = 1
        for vehicle in result: # create columns for embeds
            if i == 1:
                vehicle_string += ":first_place: **__1st:__** "
            elif i == 2:
                vehicle_string += ":second_place: **__2nd:__** "
            elif i == 3:
                vehicle_string += ":third_place: **__3rd:__** "
            else:
                vehicle_string += "**__#" + str(i) + ":__** "
            
            if vehicle[11] == "-": # no manufacturer = don't include
                vehicle_string += "**" + vehicle[0] + ": **"
            else:
                vehicle_string += "**" + vehicle[11] + " " + vehicle[0] + ": **"
            if(metric == "Lap Time"):
                vehicle_string += vehicle[2] + " / " + vehicle[3] + "mph\n"
            else: # top speed
                vehicle_string += vehicle[3] + "mph / " + vehicle[2] + "\n"
            i += 1
                
        title_string = "" # used later if embed > 1024 characters
        if vehicle_class == "Tuners": # for title string if tuners
            result[0][1] = "Tuners"
        if(metric == "Lap Time"):
            title_string = "Top " + str(len(result)) + " " + str(result[0][1]) + " (Lap Time)"
            embed = nextcord.Embed(
                title="Top " + str(len(result)) + " " + str(result[0][1]) + " (Lap Time)",
                color=0x03fc45
            )
        else: # top speed
            title_string = "Top " + str(len(result)) + " " + str(result[0][1]) + " (Top Speed)"
            embed = nextcord.Embed(
                title="Top " + str(len(result)) + " " + str(result[0][1]) + " (Top Speed)",
                color=0x03fc45
            )
        
        if len(vehicle_string) > 1024:
            statistics_array = vehicle_string.splitlines()
            use_these_in_embeds = [] # strings of max of 1024 in length, one per embed used
            current_embed_string = ""
            non_statistics_strings_length = len(title_string + "Bot created by MrThankUvryMuch#9854. Thanks to Broughy1322 for much of the vehicle data!" + "Performance Statistics" + " Cont.")
            for vehicle in statistics_array:
                if len(current_embed_string + vehicle + "\n") <= (1024 - non_statistics_strings_length): # accomodates title etc in embed aside from actual data
                    current_embed_string += str(vehicle) + "\n"
                else:
                    use_these_in_embeds.append(current_embed_string)
                    current_embed_string = str(vehicle) + "\n"
            if len(current_embed_string) > 0: # adds last of vehicles to the embed string
                use_these_in_embeds.append(current_embed_string)
            embed.add_field(name="Performance Statistics", value=use_these_in_embeds[0], inline=True)
            embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854). Thanks to Broughy1322 for much of the vehicle data!")
            await interaction.send(embed=embed)
            for i in range(1, len(use_these_in_embeds)):
                new_embed = nextcord.Embed(
                    title=title_string + " Cont.",
                    color=0x03fc45
                )
                new_embed.add_field(name="Performance Statistics", value=use_these_in_embeds[i], inline=True)
                embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854). Thanks to Broughy1322 for much of the vehicle data!")
                await interaction.send(embed=new_embed)

        else:
            embed.add_field(name="Performance Statistics", value=vehicle_string, inline=True)
            embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854). Thanks to Broughy1322 for much of the vehicle data!")
            await interaction.send(embed=embed)
    except:
        await on_command_error(interaction, sys.exc_info()[0])

@bot.slash_command(name='podium', description="Returns current and future podium vehicles.", guild_ids=testserverid)
async def podium_cars(interaction: Interaction):
    try:
        embed = nextcord.Embed( 
                title="Podium Vehicles",
                color=0x03fc45
            )
        podium_data = sheetparser_podium.main('podium', '', '', '')
        current_vehicle = ""
        current_vehicle_image = ""
        future_vehicles = ""
        for vehicle_arr in podium_data:
            if vehicle_arr[2] == 'Current':
                current_vehicle = vehicle_arr[0]
                current_vehicle_image = vehicle_arr[1]
            elif vehicle_arr[2] == 'Future':
                future_vehicles += vehicle_arr[0] + '\n'
        
        future_vehicles = future_vehicles.rstrip() # remove trailing \n

        embed.add_field(name=":hourglass: Current Podium Vehicle :hourglass:", value=current_vehicle, inline=False)
        embed.set_image(url=current_vehicle_image)
        embed.add_field(name=":clock5: Future Podium Vehicles :clock5:", value=future_vehicles, inline=False)
        embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)")
        await interaction.send(embed=embed)
    except:
        await on_command_error(interaction, sys.exc_info()[0])

@bot.slash_command(name='podiumupdate', description="Used to update podium list. Only administrators can use this command.", guild_ids=testserverid)
async def podium_update(
    interaction: Interaction,
    vehicle_name:str,
    current_or_future:str = SlashOption(required=True, choices=["Change Current", "Add Future", "Remove Future"]),
    image_link:str = SlashOption(required=False, default=None)):

    try:
        if(not interaction.user.guild_permissions.ban_members):
            await on_command_error(interaction, "Missing Permissions")
        else:
            if current_or_future == "Change Current" and image_link == None: # if current and no image, don't allow it
                error_no_image_embed = nextcord.Embed( 
                        title=":grey_exclamation: Updating Current Vehicle Requires Image Link!",
                        color=0xffdd00,
                    )
                await interaction.send(embed=error_no_image_embed)
                return

            podium_data = sheetparser_podium.main('podiumupdate', vehicle_name, current_or_future, image_link)
            if current_or_future == "Change Current":
                embed = nextcord.Embed( 
                            title=":white_check_mark: Current Podium Vehicle Updated",
                            color=0x03fc45,
                            description="If present, the same vehicle has been removed from the future podium vehicle list also."
                        )
                embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)")
                await interaction.send(embed=embed)
            elif current_or_future == "Add Future":
                if podium_data == "VEHICLE ALREADY ADDED!":
                    embed = nextcord.Embed( 
                        title=":grey_exclamation: Vehicle Already In Podium List!",
                        description="Vehicle not added. It already exists in the podium list.",
                        color=0xffdd00
                    )
                    await interaction.send(embed=embed)
                else:
                    embed = nextcord.Embed( 
                            title=":white_check_mark: Vehicle Added",
                            description="Future vehicle added to podium list.",
                            color=0x03fc45
                    )
                    await interaction.send(embed=embed)
            else: # Remove Future
                if podium_data == "VEHICLE NOT FOUND FOR REMOVAL!":
                    embed = nextcord.Embed( 
                        title=":grey_exclamation: Vehicle Not Found!",
                        color=0xffdd00,
                        description="I can't find that vehicle on the podium list. Please try again."
                    )
                    await interaction.send(embed=embed)
                else:
                    embed = nextcord.Embed( 
                            title=":white_check_mark: Vehicle Removed",
                            description="Future vehicle removed from podium list.",
                            color=0x03fc45
                        )
                    await interaction.send(embed=embed)
    except:
        await on_command_error(interaction, sys.exc_info()[0])

@bot.slash_command(name='prizeride', description="Returns current and future prize ride vehicles.", guild_ids=testserverid)
async def prizeride_cars(interaction: Interaction):
    try:
        embed = nextcord.Embed( 
                title="Prize Ride Vehicles",
                color=0x03fc45
            )
        prizeride_data = sheetparser_prizeride.main('prizeride', '', '', '')
        current_vehicle = ""
        current_vehicle_image = ""
        future_vehicles = ""
        for vehicle_arr in prizeride_data:
            if vehicle_arr[2] == 'Current':
                current_vehicle = vehicle_arr[0]
                current_vehicle_image = vehicle_arr[1]
            elif vehicle_arr[2] == 'Future':
                future_vehicles += vehicle_arr[0] + '\n'
        
        future_vehicles = future_vehicles.rstrip() # remove trailing \n

        embed.add_field(name=":hourglass: Current Prize Ride Vehicle :hourglass:", value=current_vehicle, inline=False)
        embed.set_image(url=current_vehicle_image)
        embed.add_field(name=":clock5: Future Prize Ride Vehicles :clock5:", value=future_vehicles, inline=False)
        embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)")
        await interaction.send(embed=embed)
    except:
        await on_command_error(interaction, sys.exc_info()[0])

@bot.slash_command(name='prizerideupdate', description="Used to update prize ride list. Only administrators can use this command.", guild_ids=testserverid)
async def podium_update(
    interaction: Interaction,
    vehicle_name:str,
    current_or_future:str = SlashOption(required=True, choices=["Change Current", "Add Future", "Remove Future"]),
    image_link:str = SlashOption(required=False, default=None)):

    try:
        if(not interaction.user.guild_permissions.ban_members):
            await on_command_error(interaction, "Missing Permissions")
        else:
            if current_or_future == "Change Current" and image_link == None: # if current and no image, don't allow it
                error_no_image_embed = nextcord.Embed( 
                        title=":grey_exclamation: Updating Current Vehicle Requires Image Link!",
                        color=0xffdd00,
                    )
                await interaction.send(embed=error_no_image_embed)
                return

            prizeride_data = sheetparser_prizeride.main('prizerideupdate', vehicle_name, current_or_future, image_link)
            if current_or_future == "Change Current":
                embed = nextcord.Embed( 
                            title=":white_check_mark: Current Prize Ride Vehicle Updated",
                            color=0x03fc45,
                            description="If present, the same vehicle has been removed from the future prize ride vehicle list also."
                        )
                embed.set_footer(text="Bot created by Emperor (MrThankUvryMuch#9854)")
                await interaction.send(embed=embed)
            elif current_or_future == "Add Future":
                if prizeride_data == "VEHICLE ALREADY ADDED!":
                    embed = nextcord.Embed( 
                        title=":grey_exclamation: Vehicle Already In Prize Ride List!",
                        description="Vehicle not added. It already exists in the prize ride list.",
                        color=0xffdd00
                    )
                    await interaction.send(embed=embed)
                else:
                    embed = nextcord.Embed( 
                            title=":white_check_mark: Vehicle Added",
                            description="Future vehicle added to prize ride list.",
                            color=0x03fc45
                    )
                    await interaction.send(embed=embed)
            else: # Remove Future
                if prizeride_data == "VEHICLE NOT FOUND FOR REMOVAL!":
                    embed = nextcord.Embed( 
                        title=":grey_exclamation: Vehicle Not Found!",
                        color=0xffdd00,
                        description="I can't find that vehicle on the prize ride list. Please try again."
                    )
                    await interaction.send(embed=embed)
                else:
                    embed = nextcord.Embed( 
                            title=":white_check_mark: Vehicle Removed",
                            description="Future vehicle removed from prize ride list.",
                            color=0x03fc45
                        )
                    await interaction.send(embed=embed)
    except:
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


@bot.slash_command(name='staffvehicle', description="Returns a vehicle from a staff members' garage", guild_ids=testserverid)
async def find_staff_vehicle(
    interaction : Interaction, 
    vehicle:str,
    staff_member:str = SlashOption(choices=["Emperor", "Rad", "Alex"], required=True),
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
            final_veh_suggs = []
            for i in range(0, len(vehicle_suggestions)): # remove all really bad suggestions
                if not(vehicle_suggestions[i][1] < 0.5 and vehicle_suggestions[i][2] != "EP"):
                    final_veh_suggs.append(vehicle_suggestions[i])
            if(len(vehicle_suggestions) == 0): # no suggestions left, they were all bad :/ send stock vehicle not found embed
                await interaction.send(embed=embed)
            else: # still at least one good suggestion left, so show it/them
                not_found_suggestions_string = ""
                emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
                iterator = 0
                for i in range(0, len(final_veh_suggs)): # put together the suggestions for the embed
                    if(iterator < 5):
                        not_found_suggestions_string += emojis[i] + ": " + str(final_veh_suggs[i][0]) + "\n"
                        iterator += 1
                    else:
                        break
                embed.add_field(name="Did You Mean...", value=not_found_suggestions_string, inline=False) # add it to the embed and send it
                await interaction.send(embed=embed)
                message = await interaction.original_message() # grab message we just sent to add reactions to it
                for i in range(0, iterator):
                    await message.add_reaction(emojis[i])
                
                def check(reaction, user):
                    return str(reaction.emoji) in emojis and user == interaction.user
                confirmation = await bot.wait_for("reaction_add", check=check)
                car_to_use = '' # set below, used in call to sheetparser for newfound vehicle
                if "1️⃣" in str(confirmation):
                    car_to_use = final_veh_suggs[0][0]
                elif "2️⃣" in str(confirmation):
                    car_to_use = final_veh_suggs[1][0]
                elif "3️⃣" in str(confirmation):
                    car_to_use = final_veh_suggs[2][0]
                elif "4️⃣" in str(confirmation):
                    car_to_use = final_veh_suggs[3][0]
                elif "5️⃣" in str(confirmation):
                    car_to_use = final_veh_suggs[4][0]
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
        await on_command_error(interaction, sys.exc_info()[0])

    
    

    
    # TODO
    # BUG: # add future shock, nightmare, and apocalypse versions of each arena vehicle?
    # BUG: if two suggestion embeds are present and neither have been reacted to, reacting to one also will find the vehicle of the same reaction position
            # on the other one
    # HUGE BUG: heroku restarting every 24 hours removes the global commands from discord's cache. I'll need to use a database to 
                # keep record of the guild ids the bot is in dynamically, and then use that array in guild_ids if I plan to release it publicly
    # BUG: if podium or prize ride future vehicle list is empty, it will error. Auto-add something in this case?
    # FEATURE: proper bug report system
    # FEATURE: some sort of guide explaining how to access edge case stuff (min/max df on f1 cars)
    # FEATURE: armor resistances for armored vehicles in "other notes" - or additional column
    # FEATURE: vehicleinfo irl variants of cars
        
    # BIG FEATURE: future podium vehicle list
        # BUG: MAKE IT SO ONLY DCA SERVER STAFF WITH BAN PERM GET THE HELP TEXT VISIBLE
        # BUG: MAKE IT SO ONLY LOBO, TEST SERVER, AND DCA SERVER CAN USE PODIUMUPDATE COMMAND
    # BIG FEATURE: query staff garages
        # BUG: says it has suggestions but has no reactions for very far off guesses. i.e. try 'van', 'alk', 'bomb'
        # CLEAN UP CODE JEEZ
    # BIG FEATURE: expand to being public? need to consider cost

    # INVITE BOT BACK TO TEST SERVER USING https://discord.com/api/oauth2/authorize?client_id=800779921814323290&permissions=0&scope=bot%20applications.commands

bot.run(TOKEN)