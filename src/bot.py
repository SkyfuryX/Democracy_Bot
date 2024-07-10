import bot_func as tf
import os, re, random, discord, asyncio
from discord import app_commands
from discord.ext import commands
from dateutil.relativedelta import relativedelta
from datetime import datetime as dt, timezone, timedelta, tzinfo
from dotenv import load_dotenv

#examples https://github.com/Rapptz/discord.py/tree/master/examples

load_dotenv()
token = os.getenv('bot_token')
inspiration = open('liberty.txt', 'r').readlines()
message_time = {}
settings = {}
with open('auto\\planetlist.txt', 'r') as file:
    planetlist = file.read().split(', ')
    file.close()
with open('auto\\sectorlist.txt', 'r') as file:
    sectorlist = file.read().split(', ')
    file.close()
with open('auto\\stratlist.txt', 'r') as file:
    stratlist = file.read().split(', ')
    file.close()

#initiate bot
intents = discord.Intents.default()
intents.message_content = True
descrip = '''A discord bot to view on-demand statistics from the game Helldrivers 2. Includes Planet info, Major Orders, Dispatches from Super Earth, and more.\n/report for bugs or feature requests.\nDiscord Contact: @sky.fury'''
bot = commands.Bot(command_prefix='!', description=descrip, intents=intents)

@bot.event
async def on_ready():
    print('Logged on as', bot.user)
    
@bot.event
async def on_connect():
    await bot.change_presence(activity=discord.CustomActivity(name='Spreading Managed Democracy'))

@bot.listen('on_message')
async def on_message(message):
    now = dt.now()
    #print(message.content)
    if bool(re.search('democracy|democrat', message.content.lower())) == True:
        #don't respond to ourselves
        try:
            if message.author == bot.user:
                return
            #prevent democratic spam unless last message sent on a server by the bot was over a min prior
            #tracks the last 5 response sent from the inpiration list to prevent the same message being sent in the same server within the last 5 responses sent
            elif (message.guild.id in message_time.keys()) == False:
                i = random.randint(1,len(inspiration))
                message_time[message.guild.id] = {'time':'','reply': [99,99,99,99,99] }
                message_time[message.guild.id]['time'] = dt.now()
                message_time[message.guild.id]['reply'][4] = i
                #print (str(message.guild.id),str(message_time[message.guild.id]))
                await message.channel.send(inspiration[i-1][0:-1])
            elif (message.guild.id in message_time.keys()) == True:
                if (dt.now() - message_time[message.guild.id]['time']).total_seconds() > 60:
                    message_time[message.guild.id]['time'] = dt.now()
                    x = random.choice([e for e in range(len(inspiration)) if e not in message_time[message.guild.id]['reply']])
                    for a in range(4):
                        message_time[message.guild.id]['reply'][a] = message_time[message.guild.id]['reply'][a+1] 
                    message_time[message.guild.id]['reply'][4] = x  
                    #print(str(message.guild.id),(str(message_time[message.guild.id]['reply'])))
                    await message.channel.send(inspiration[x][0:-1])
        except AttributeError: #respond to messages in DMs since they have no guildID
            i = random.randint(1,len(inspiration))
            await message.channel.send(inspiration[i-1][0:-1])
        
@bot.tree.command(name='war',description='Display the overall stats of the current Galactic War') #shows info on the galatic war in general
@app_commands.describe(public='Select True to share the response in this channel.')
async def war(interaction: discord.Interaction, public: bool=False):
    msg = await tf.war()   
    await interaction.response.send_message(embed=msg, ephemeral=not public)

@bot.tree.command(name='orders', description='Displays the current Major Order') #shows info on the current Major Order in general
@app_commands.describe(public='Select True to share the response in this channel.')
async def orders(interaction: discord.Interaction, public: bool=False):
    msg = await tf.orders()
    await interaction.response.send_message(embed=msg, ephemeral=not public)

@bot.tree.command(name='dispatch', description='Displays the [number] most recent dispatch message(s) from Super Earth. Defaults to 1')
@app_commands.describe(number='The number of messages requested.', public='Select True to share the response in this channel.')
async def dispatch(interaction: discord.Interaction, number: int=1, public: bool=False):
    #displays latest dispatch messages
    query='SELECT d.published, d.message FROM dispatch d ORDER BY d.id DESC OFFSET 0 LIMIT '+ str(number)
    results = await tf.db_query('dispatch', query)
    msg = discord.Embed(title='**--Latest Message(s) from Super Earth--**')
    for item in results:
        msg.add_field(name='Date: ' + str(dt.strptime(item['published'][0:10], '%Y-%m-%d') + relativedelta(years=160))[0:10], value= item['message'], inline=False) #adds 160 years to date to make message more thematic
    if len(msg) <= 6000:
        await interaction.response.send_message(embed=msg, ephemeral=not public)
    elif len(msg) > 6000:
        msg = discord.Embed(title='',desctiption='Super Earth cannot grant your information request at this time. Request fewer dispatches.')
        await interaction.response.send_message(embed= msg, ephemeral=True)
                           
@bot.tree.command(name='planets',description='Displays information on a specific planet') #gathers liberation info and stats on a specific planet
@app_commands.describe(name='The name of the planet to view.', public='Select True to share the response in this channel.')
async def planets(interaction: discord.Interaction, name: str, public: bool=False):
    msg = await tf.planet(name)
    await interaction.response.send_message(embed=msg,ephemeral= not public)
    
@planets.autocomplete('name')
async def planets_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    try:
        return [
            app_commands.Choice(name=planet, value=planet)
            for planet in planetlist if current.upper() in planet]
    except discord.errors.HTTPException:
        print('Too Many Autocomplete Results')
        
@bot.tree.command(name='campaigns',description='Displays the currently available Liberation and Defense campaigns.') 
@app_commands.describe(public='Select True to share the response in this channel.')
async def campaigns(interaction: discord.Interaction, public: bool=False): 
    libcam, defcam = await tf.campaigns()
    if len(defcam) > 25:
        await interaction.response.send_message(embeds=[libcam,defcam], ephemeral= not public)
    else:
        await interaction.response.send_message(embed=libcam, ephemeral= not public)

@bot.tree.command(name='stratagems',description='Displays information for any stratagems containing the name included') #show info on requested stratgems
@app_commands.describe(name='The name of the stratagem to view.', public='Select True to share the response in channel.')
async def stratagems(interaction: discord.Interaction, name: str, public: bool=False):
    msg = await tf.stratagems(name)
    await interaction.response.send_message(embed=msg, ephemeral= not public,)
    
@stratagems.autocomplete('name')
async def stratagems_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    try:
        return [
            app_commands.Choice(name=stratagem, value=stratagem)
            for stratagem in stratlist if current.lower() in stratagem.lower()]
    except discord.errors.HTTPException:
       pass
 
@bot.tree.command(name='report', description='Issues the F-33D form link to provide feedback to Super Earth High Command')  
async def report(interaction: discord.Interaction):
    msg = discord.Embed(title='--Reports to Super Earth--', description= 'Please submit bug reports and feature requests via form [F-33D](https://forms.gle/mAPt9wcj4qeaT2g26)\n\nThank you for your service, Helldiver!', type='rich')
    await interaction.response.send_message(embed= msg,ephemeral=True)    
          
@bot.command()
async def shutdown(ctx):
    if ctx.author.id == 157695574580264960: 
        await bot.close()
        
@bot.command()
async def sync(ctx):
    if ctx.author.id == 157695574580264960: 
        await bot.tree.sync() 
        await ctx.channel.send(content='Commands Synchronized') 

async def guild_id(interaction: discord.Interaction):
    return interaction.guild_id    
     
bot.run(token) #starts bot and begins listening for events and commands