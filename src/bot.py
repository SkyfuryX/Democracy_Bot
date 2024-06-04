import discord
from discord.ext import commands
import os
import re
import random
import math
from dateutil.relativedelta import relativedelta
from datetime import datetime
from dotenv import load_dotenv
from azure.cosmos import CosmosClient
#examples https://github.com/Rapptz/discord.py/tree/master/examples

load_dotenv()
token = os.getenv('bot_token')
db_uri = os.getenv('account_uri')
db_key = os.getenv('account_key')

#initialize db connection
client = CosmosClient(url=db_uri, credential=db_key)
database_name = 'democracy_bot'
database = client.get_database_client(database_name)

#initiate bot
intents = discord.Intents.default()
intents.message_content = True
descrip = '''A discord bot to view on-demand statistics from the game Helldrivers 2: Includes planet info, 
Major Orders, dispatches from Super Earth, and more.'''
bot = commands.Bot(command_prefix='/', description=descrip, intents=intents)
tree = discord.app_commands.CommandTree

inspiration = open('liberty.txt', 'r').readlines()

@bot.event
async def on_ready():
    await bot.tree.sync()
    print('Logged on as', bot.user)

message_time = {}

@bot.listen('on_message')
async def on_message(message):
    now = datetime.now()
    print(message.content)
    if bool(re.search('Democracy|democracy|democrat|Democrat', message.content)) == True:
        #don't respond to ourselves
        if message.author == bot.user:
            return
        #prevent democratic spam unless last message sent on a server by the bot was over a mins prior
        elif (message.guild.id in message_time.keys()) == False:
            message_time[message.guild.id] = datetime.now()
            print(message_time[message.guild.id])
            i = random.randint(1,len(inspiration))
            print(i)
            await message.channel.send(inspiration[i-1][0:-1])
        elif (message.guild.id in message_time.keys()) == True:
            if (datetime.now() - message_time[message.guild.id]).total_seconds() > 60:
                message_time[message.guild.id] = datetime.now()
                i = random.randint(1,len(inspiration))
                await message.channel.send(inspiration[i-1][0:-1])
        
def addcommas(number):
    numlst = list(str(number))
    x = int(math.floor(len(numlst) / 3))
    i = 1
    if len(numlst) <=1:
       pass #do nothing since it needs no commas added 
    elif len(numlst) % 3 == 0:
        for n in range(x-1):
            i = i - 4 
            numlst.insert(i, ',')     
    else:
        for n in range(x):
            i = i - 4
            numlst.insert(i, ',')
    numlst = ''.join(numlst)
    return numlst #return string to be concat'd into messages

@bot.tree.command(name='war',description='Show the stats of the current Galactic War') #shows info on the galatic war in general
async def war(interaction: discord.Interaction):
    container = database.get_container_client('war_status')
    for item in container.query_items(
        query='SELECT * FROM war_status w ORDER BY w.id DESC OFFSET 0 LIMIT 1',
        enable_cross_partition_query=True):
        war = item       
    await interaction.channel.send('**Galactic War Stats:**\nHelldivers Active: '+ addcommas(war['playerCount']) +'\nHelldivers KIA:' + addcommas(war['deaths']) + 
                                   '\nAutomatons Killed: '+ addcommas(war['automatonKills']) +'\nTerminids Killed: '+ addcommas(war['terminidKills']) +
                                   '\nIlluminate Killed: '+ addcommas(war['illuminateKills']) +'\nBullets Fired: ' + addcommas(war['bulletsFired']))

@bot.tree.command(name='orders',description='Returns the current Major Order') #shows info on the current Major Order in general
async def orders(interaction: discord.Interaction):
    pass
    #await interaction.channel.send('Current Major Order:')

@bot.tree.command(name='dispatch', description='Returns most recent dispatch message from Super Earth.')
async def dispatch(interaction: discord.Interaction, number: int = 1):
    #displays latest dispatch messages
    container = database.get_container_client('dispatch')
    msg = 'Latest message(s) from Super Earth:'
    for item in container.query_items(
        query='SELECT d.published, d.message FROM dispatch d ORDER BY d.id DESC OFFSET 0 LIMIT ' + str(number),
        enable_cross_partition_query=True):
        msg += '\n\nDate: ' + item['published'][0:10]  + '\n' + item['message']
    if number <= 3:
        await interaction.channel.send(msg)
    elif number >= 4:
        await interaction.user.send(msg)
            
        
@bot.tree.command(name='planets',description='In Progress')
async def planets(interaction: discord.Interaction,arg: str):
    #gathers liberation info on a specific planet
    await interaction.channel.send(arg)

@bot.tree.command(name='weapons',description='In Progress')
async def weapons(interaction: discord.Interaction,weapon: str):
    # show information on weapons
    pass

@bot.tree.command(name='stratgems',description='In Progress')
async def strategems(interaction: discord.Interaction,strat: str):
    #pull/show info on stratgems
    pass

#starts bot and begins listening for events and commands
bot.run(token)



addcommas(317520822030)