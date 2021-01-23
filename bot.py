import os
import discord
from dotenv import load_dotenv
from discord.ext import commands
import sheetparser

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='$')

@bot.event 
async def on_ready(): # prints to the console when the bot starts
    print("Bot started!")



@bot.event
async def on_command_error(ctx, error): # provides error embeds when things go wrong
    if(isinstance(error, commands.MissingRequiredArgument)): # if someone calls $vehicleinfo without a vehicle as an argument
        embed = discord.Embed(
            title=":grey_exclamation: No Arguments Given!",
            color=0xffdd00,
            description="This command requires an argument. Use " + bot.command_prefix + "helpme for more information."
        )
        embed.set_footer(text="Bot created by MrThankUvryMuch#9854")
        await ctx.send(embed=embed)
    elif(isinstance(error, commands.CommandNotFound)): # general command not found error
        print(error)
        embed = discord.Embed(
            title=":x: Command Not Found!",
            color=0xff2600,
            description="This isn't a valid command. Use " + bot.command_prefix + "helpme for a list of commands."
        )
        embed.set_footer(text="Bot created by MrThankUvryMuch#9854")
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
async def set_prefix(ctx, arg):
    bot.command_prefix = arg
    embed = discord.Embed(
            title=":white_check_mark: Prefix Set!",
            color=0x03fc45
        )
    embed.set_footer(text="Bot created by MrThankUvryMuch#9854")
    await ctx.send(embed=embed)


@bot.command('helpme') # general help embed
async def help_func(ctx):
    embed = discord.Embed(
        title="Welcome to GTABot!",
        description="**prefix is '$'**.\n Use this bot to look up information about all cars in GTA V and Online!\n\n",
        color=0x34ebae
    )
    embed.add_field(name="Commands", value="**$vehicleinfo [carName]:** Provides information on GTA V and GTA Online vehicles\n**$prefix [new_prefix]:** Sets new prefix to use with this bot.", inline=False)
    embed.set_footer(text="Bot created by MrThankUvryMuch#9854")
    await ctx.send(embed=embed)



@bot.command(name='vehicleinfo')
async def give_car(ctx, *, arg): # main function to get GTA vehicle info from the google sheet. on_command_error handles all errors
    if(len(arg) < 3):
        embed_characters = discord.Embed(
            title=":grey_exclamation: Keyword Not Long Enough!",  
            color=0xffdd00,
            description="Vehicle keyword must be at least 3 characters in length."
        )
        await ctx.send(embed=embed_characters)
        return
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
    
    # stress test

    # get it hosted somewhere

    # stress test 2

    # deploy to DCA server

    # allow users to change prefix

bot.run(TOKEN)