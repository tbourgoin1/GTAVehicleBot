import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
import sheetparser
import json
import keep_alive # file for server hosting

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

def get_prefix(ctx, arg): # gets the prefix for the guild id given
    with open('prefixes.json', 'r') as my_json:
        all_prefixes = json.load(my_json)
    return all_prefixes[str(arg.guild.id)]

bot = commands.Bot(command_prefix=get_prefix)

@bot.event 
async def on_ready(): # prints to the console when the bot starts
    print("Bot started!")


@bot.event
async def on_guild_join(guild):
    with open('prefixes.json', 'r') as my_json: # read in all current prefixes
        prefixes = json.load(my_json)
    
    prefixes[str(guild.id)] = '$' # add new guild to prefixes list and give it the default prefix

    with open('prefixes.json', 'w') as my_json: # write new guild/prefix combo to the json file
        json.dump(prefixes, my_json, indent=4)

@bot.event
async def on_guild_remove(guild):
    with open('prefixes.json', 'r') as my_json: # read in all current prefixes
        prefixes = json.load(my_json)
    
    prefixes.pop(str(guild.id)) # remove line in json corresponding to the guild that was removed

    with open('prefixes.json', 'w') as my_json: # write new info json file - removed guild
        json.dump(prefixes, my_json, indent=4)


@bot.event
async def on_command_error(ctx, error): # provides error embeds when things go wrong
    if(isinstance(error, commands.MissingRequiredArgument)): # if someone calls $vehicleinfo without a vehicle as an argument
        embed = discord.Embed(
            title=":grey_exclamation: No Arguments Given!",
            color=0xffdd00,
            description="This command requires an argument. Use the 'helpme' command for more information."
        )
        embed.set_footer(text="Bot created by MrThankUvryMuch#9854")
        await ctx.send(embed=embed)
    elif(isinstance(error, commands.CommandNotFound)): # general command not found error
        print(error)
        embed = discord.Embed(
            title=":x: Command Not Found!",
            color=0xff2600,
            description="This command requires an argument. Use the 'helpme' command for more information."
        )
        embed.set_footer(text="Bot created by MrThankUvryMuch#9854")
        await ctx.send(embed=embed)
    elif(isinstance(error, commands.MissingPermissions)):
        print(error)
        embed = discord.Embed(
            title=":grey_exclamation: Insufficient Permissions",
            color=0xffdd00,
            description="Only administrators can run this command."
        )
        await ctx.send(embed=embed)
    else:
        print(error)
        embed = discord.Embed(
            title=":x: An Error Has Occurred!",
            color=0xff2600,
            description="What happened was probably bad. Contact MrThankUvryMuch#9854 to submit a bug report."
        )
        embed.set_footer(text="Bot created by MrThankUvryMuch#9854")
        await ctx.send(embed=embed)


@bot.command('prefix') # NOT PERMANENT, NEED JSON - https://stackoverflow.com/questions/51915962/per-server-prefixs
@commands.has_permissions(administrator=True) # only admins can change prefixes
async def set_prefix(ctx, arg):
    with open('prefixes.json', 'r') as my_json: # read in all current prefixes
        prefixes = json.load(my_json)
    
    prefixes[str(ctx.guild.id)] = arg # change current guild prefix to the arg given

    with open('prefixes.json', 'w') as my_json: # write new info to json file - guild prefix changed
        json.dump(prefixes, my_json, indent=4)
    
    embed = discord.Embed(
            title=":white_check_mark: Prefix Set!",
            description="Prefix is now " + arg,
            color=0x03fc45
        )
    embed.set_footer(text="Bot created by MrThankUvryMuch#9854")
    await ctx.send(embed=embed)


@bot.command('helpme') # general help embed
async def help_func(ctx):
    embed = discord.Embed(
        title="Welcome to GTABot!",
        description="**Use this bot to look up information about all cars in GTA V and Online!**\n\n",
        color=0x34ebae
    )
    embed.add_field(name="Commands", value="**vehicleinfo [carName]:** Provides information on GTA V and GTA Online vehicles\n**prefix [new_prefix]:** Sets new prefix to use with this bot.", inline=False)
    embed.set_footer(text="Bot created by MrThankUvryMuch#9854")
    await ctx.send(embed=embed)



@bot.command(name='vehicleinfo')
async def give_car(ctx, *, arg): # main function to get GTA vehicle info from the google sheet. on_command_error handles all errors
    embed_wait = discord.Embed(
        title=":mag: Searching for vehicle...",  
        color=0x7d7d7d
    )
    await ctx.send(embed=embed_wait, delete_after=1)
    car_array = sheetparser.main(arg)
    if("ERROR: Vehicle not found in spreadsheet" in car_array):
        embed = discord.Embed(
            title=":grey_exclamation: Vehicle Not Found!",
            color=0xffdd00,
            description="Enter a valid vehicle name."
        )
        await ctx.send(embed=embed)
    elif("VEHICLE DATA INCOMPLETE! Spreadsheet #" in car_array):
        embed = discord.Embed(
            title=":grey_exclamation: Vehicle Data Incomplete!",
            color=0x6911cf,
            description="Some of this vehicle's info hasn't been completed yet. Check back later."
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title=car_array[0], 
            color=0x03fc45
        )
        embed.add_field(name="Class", value=car_array[1], inline=True)
        embed.add_field(name="Base Price", value='$' + car_array[9], inline=True)
        embed.add_field(name="Lap Time", value=car_array[2], inline=True)
        embed.add_field(name="Lap Time Position in Class", value=car_array[5], inline=True)
        embed.add_field(name="Top Speed", value=car_array[3] + 'mph', inline=True)
        embed.add_field(name="Top Speed Position in Class", value=car_array[6], inline=True)
        embed.add_field(name="Drivetrain", value=car_array[7], inline=True)
        embed.add_field(name="Number of Seats", value=car_array[8], inline=True)
        embed.set_thumbnail(url=car_array[4])
        embed.set_footer(text="Thanks to Broughy1322 for vehicle top speed and lap time data. Bot created by MrThankUvryMuch#9854")
        await ctx.send(embed=embed)

    
    # TODO
    # ONLY can do 1 command at a time - look into threading
    # get it hosted
    # helpme command can't get prefixes accuratedly - would need to revamp entire code structure. Here: https://stackoverflow.com/questions/63495237/how-to-make-discord-py-custom-prefixes-system
    # deploy to DCA server

keep_alive.keep_alive() # for server hosting

bot.run(TOKEN)