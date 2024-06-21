import bot_func as bf
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
    msg = await bf.war()   
    await interaction.response.send_message(content=msg, ephemeral=not public)

@bot.tree.command(name='orders', description='Displays the current Major Order') #shows info on the current Major Order in general
@app_commands.describe(public='Select True to share the response in this channel.')
async def orders(interaction: discord.Interaction, public: bool=False):
    msg = await bf.orders()
    await interaction.response.send_message(content=msg, ephemeral=not public)

@bot.tree.command(name='dispatch', description='Displays the [number] most recent dispatch message(s) from Super Earth. Defaults to 1, max 3')
@app_commands.describe(number='The number of messages requested. Max 3', public='Select True to share the response in this channel.')
async def dispatch(interaction: discord.Interaction, number: int=1, public: bool=False):
    #displays latest dispatch messages
    query='SELECT d.published, d.message FROM dispatch d ORDER BY d.id DESC OFFSET 0 LIMIT '+ str(number)
    results = await bf.db_query('dispatch', query)
    msg = 'Latest message(s) from Super Earth:'
    for item in results:
        msg += '\n\nDate: ' + str(dt.strptime(item['published'][0:10], '%Y-%m-%d') + relativedelta(years=160))[0:10] + '\n' + item['message'] #adds 160 years to date to make message more thematic
    if number <= 3:
        await interaction.response.send_message(content=msg, ephemeral=not public)
    elif number >= 4:
        await interaction.response.send_message(content='Super Earth cannot grant your information request at this time. Request 3 or less dispatches.', ephemeral=True)
                           
@bot.tree.command(name='planets',description='Displays information on a specific planet') #gathers liberation info and stats on a specific planet
@app_commands.describe(name='The name of the planet to view.', public='Select True to share the response in this channel.')
async def planets(interaction: discord.Interaction, name: str, public: bool=False):
    msg = await bf.planet(name)
    await interaction.response.send_message(content=msg,ephemeral= not public)
    
@planets.autocomplete('name')
async def planets_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    return [
        app_commands.Choice(name=planet, value=planet)
        for planet in planetlist if current.upper() in planet]
        
@bot.tree.command(name='campaigns',description='Displays the currently available Liberation and Defense campaigns.') 
@app_commands.describe(public='Select True to share the response in this channel.')
async def campaigns(interaction: discord.Interaction, public: bool=False): 
    msg = await bf.campaigns()
    await interaction.response.send_message(content=msg,ephemeral= not public)

'''@bot.tree.command(name='weapons',description='In Progress') #show information on weapons
async def weapons(interaction: discord.Interaction,weapon: str):
    msg = 'Work in progress'  
    await interaction.response.send_message(content=msg)'''

@bot.tree.command(name='stratagems',description='Displays information for any stratagems containing the name included') #show info on requested stratgems
@app_commands.describe(name='The name of the stratagem to view.', public='Select True to share the response in channel.')
async def stratagems(interaction: discord.Interaction, name: str, public: bool=False):
    msg = await bf.stratagems(name)
    await interaction.response.send_message(content=msg, ephemeral= not public)
    
@stratagems.autocomplete('name')
async def stratagems_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    return [
        app_commands.Choice(name=stratagem, value=stratagem)
        for stratagem in stratlist if current.lower() in stratagem.lower()]
    
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

@bot.tree.command(name='settings', description='Configuration settings')
@commands.check_any(commands.has_permissions(administrator=True))
async def settings(interaction: discord.Interaction, public: bool, inspiration_freq: int, role:str):
    guild_set = {'id':str(interaction.guild_id)}
    guild_set['settings'] =  {'default_privacy': public,'inspiration_freq': inspiration_freq, 'role': role}
    container = await bf.data_upload('settings')
    #settings[interaction.guild_id] = guild_set['settings']
    await container.upsert_item(guild_set)
    await interaction.response.send_message(content='-Settings Saved-\nPrivacy: '+ str(guild_set['settings']['privacy'])+'\nInspiration Freq: '+
                                            str(guild_set['settings']['privacy'])+ 's\nMinimum Role: '+ guild_set['settings']['privacy'], ephemeral=True)
    
@bot.tree.command(name='report', description='Issues the F-33D form link to provide feedback to Super Earth High Command')  
async def report(interaction: discord.Interaction):
    await interaction.response.send_message(content = 'Please submit bug reports and feature requests via form [F-33D](https://forms.gle/mAPt9wcj4qeaT2g26) \n\nThank you for your service, Helldiver!',ephemeral=True)    
       
bot.run(token) #starts bot and begins listening for events and commands