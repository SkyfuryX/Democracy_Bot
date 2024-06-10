import bot_func as bf
import os, re, random, discord, asyncio
from discord.ext import commands
from dateutil.relativedelta import relativedelta
from datetime import datetime as dt, timezone, timedelta, tzinfo
from dotenv import load_dotenv

#examples https://github.com/Rapptz/discord.py/tree/master/examples

load_dotenv()
token = os.getenv('bot_token')
inspiration = open('liberty.txt', 'r').readlines()
message_time = {}

#initialize db connection
'''client = CosmosClient(url=db_uri, credential=db_key)
database_name = 'democracy_bot'
database = client.get_database_client('democracy_bot')'''

#initiate bot
intents = discord.Intents.default()
intents.message_content = True
descrip = '''A discord bot to view on-demand statistics from the game Helldrivers 2: Includes planet info, 
Major Orders, dispatches from Super Earth, and more.'''
bot = commands.Bot(command_prefix='!', description=descrip, intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    await bot.change_presence(activity=discord.CustomActivity(name='Spreading Managed Democracy'))
    print('Logged on as', bot.user)

@bot.listen('on_message')
async def on_message(message):
    now = dt.now()
    #print(message.content)
    if bool(re.search('Democracy|democracy|democrat|Democrat', message.content)) == True:
        #don't respond to ourselves
        if message.author == bot.user:
            return
        #prevent democratic spam unless last message sent on a server by the bot was over a mins prior
        elif (message.guild.id in message_time.keys()) == False:
            message_time[message.guild.id] = dt.now()
            print(message_time[message.guild.id])
            i = random.randint(1,len(inspiration))
            await message.channel.send(inspiration[i-1][0:-1])
        elif (message.guild.id in message_time.keys()) == True:
            if (dt.now() - message_time[message.guild.id]).total_seconds() > 60:
                message_time[message.guild.id] = dt.now()
                i = random.randint(1,len(inspiration))
                await message.channel.send(inspiration[i-1][0:-1])
        
@bot.tree.command(name='war',description='Show the stats of the current Galactic War') #shows info on the galatic war in general
async def war(interaction: discord.Interaction):
    msg = await bf.war()   
    await interaction.response.send_message(msg)

@bot.tree.command(name='orders',description='Returns the current Major Order') #shows info on the current Major Order in general
async def orders(interaction: discord.Interaction):
    msg = await bf.orders()
    await interaction.response.send_message(msg)

@bot.tree.command(name='dispatch', description='Returns most recent dispatch message from Super Earth.')
async def dispatch(interaction: discord.Interaction, number: int = 1):
    #displays latest dispatch messages
    query='SELECT d.published, d.message FROM dispatch d ORDER BY d.id DESC OFFSET 0 LIMIT 1'
    results = await bf.db_query('dispatch', query)
    msg = 'Latest message(s) from Super Earth:'
    for item in results:
        msg += '\n\nDate: ' + str(dt.strptime(item['published'][0:10], '%Y-%m-%d') + relativedelta(years=160))[0:10] + '\n' + item['message'] #adds 160 years to date to make message more thematic
    if number <= 3:
        await interaction.response.send_message(msg)
    elif number >= 4:
        await interaction.response.send_message('-Dispatches sent via Democratic Direct Message-')
        await interaction.user.send(msg)
                   
@bot.tree.command(name='planets',description='Displays information on a specific planet')#gathers liberation info and stats on a specific planet
async def planets(interaction: discord.Interaction, name: str):
    msg = await bf.planet(name)
    await interaction.response.send_message(msg)
    
@bot.tree.command(name='campaigns',description='Show the current active Libration and Defense campaigns.') 
async def campaigns(interaction: discord.Interaction): 
    msg = await bf.campaigns()
    await interaction.response.send_message(msg)

@bot.tree.command(name='weapons',description='In Progress') #show information on weapons
async def weapons(interaction: discord.Interaction,weapon: str):
    msg = 'Work in progress'  
    await interaction.response.send_message(msg)

@bot.tree.command(name='stratgems',description='In Progress') #show info on requested stratgems
async def strategems(interaction: discord.Interaction,strat: str):
    msg = 'Work in progress'  
    await interaction.response.send_message(msg)
    
@bot.command()
async def shutdown(ctx):
    if ctx.author.id == 157695574580264960: 
        await bot.close()    
    
bot.run(token) #starts bot and begins listening for events and commands