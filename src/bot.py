from encodings.punycode import selective_find
import bot_func as bf
import discord, sys, json
from discord import app_commands
from discord.ext import commands, tasks
from dateutil.relativedelta import relativedelta
from datetime import datetime as dt
from azure.core import exceptions

#examples https://github.com/Rapptz/discord.py/tree/master/examples

token = bf.config['BOT_TOKEN'] 
bot_test_token = bf.config['BOT_TEST_TOKEN'] #token for testing bot commands in a private server
#inspiration = open('liberty.txt', 'r').readlines()
message_time = {}
settings = {}
with open('./auto/planetlist.txt', 'r') as file:
    planetlist = file.read().split(', ')
    file.close()
with open('./auto/sectorlist.txt', 'r') as file:
    sectorlist = file.read().split(', ')
    file.close()
with open('./auto/stratlist.txt', 'r') as file:
    stratlist = file.read().split(', ')
    file.close()

#initiate bot
intents = discord.Intents.default()
descrip = '''A discord bot to view on-demand statistics from the game Helldrivers 2. Includes Planet info, Major Orders, Dispatches from Super Earth, and more.\n/report for bugs or feature requests.\nDiscord Contact: @sky.fury'''
#bot = commands.Bot(command_prefix='!', description=descrip, intents=intents)

class DemBot(commands.Bot):
           
    async def setup_hook(self):
        if '--test' in sys.argv:
            pass
        else:
            await self.add_cog(DataCog(self))
        
    @commands.Cog.listener()
    async def on_ready(self):
        print('Logged on as', self.user)
        
    @commands.Cog.listener()
    async def on_connect(self):
        await self.change_presence(activity=discord.CustomActivity(name='Spreading Managed Democracy'))
            
    # @commands.Cog.listener('on_message')
    # async def on_message(self, message):
    #     # now = dt.now()
    #     #print(message.content)
    #     if bool(re.search('democracy|democrat', message.content.lower())) == True:
    #         #don't respond to ourselves
    #         try:
    #             if message.author == self.user:
    #                 return
    #             #prevent democratic spam unless last message sent on a server by the bot was over a min prior
    #             #tracks the last 5 response sent from the inpiration list to prevent the same message being sent in the same server within the last 5 responses sent
    #             elif (message.guild.id in message_time.keys()) == False:
    #                 i = random.randint(1,len(inspiration))
    #                 message_time[message.guild.id] = {'time':'','reply': [99,99,99,99,99] }
    #                 message_time[message.guild.id]['time'] = dt.now()
    #                 message_time[message.guild.id]['reply'][4] = i
    #                 #print (str(message.guild.id),str(message_time[message.guild.id]))
    #                 await message.channel.send(inspiration[i-1][0:-1])
    #             elif (message.guild.id in message_time.keys()) == True:
    #                 if (dt.now() - message_time[message.guild.id]['time']).total_seconds() > 60:
    #                     message_time[message.guild.id]['time'] = dt.now()
    #                     x = random.choice([e for e in range(len(inspiration)) if e not in message_time[message.guild.id]['reply']])
    #                     for a in range(4):
    #                         message_time[message.guild.id]['reply'][a] = message_time[message.guild.id]['reply'][a+1] 
    #                     message_time[message.guild.id]['reply'][4] = x  
    #                     #print(str(message.guild.id),(str(message_time[message.guild.id]['reply'])))
    #                     await message.channel.send(inspiration[x][0:-1])
    #         except AttributeError: #respond to messages in DMs since they have no guildID
    #             i = random.randint(1,len(inspiration))
    #             await message.channel.send(inspiration[i-1][0:-1])
                
class DataCog(commands.Cog, name='Data'):
    def __init__(self, bot):
        self.bot = bot
    
    def cog_load(self):
        print('Tasks loaded.')
        self.primary_data.start()
        self.secondary_data.start()
            
    def cog_unload(self):
        self.primary_data.stop()
        self.secondary_data.stop()
        
    @commands.Cog.listener()
    async def on_ready(self):
        pass
           
    @tasks.loop(minutes=10)
    async def primary_data(self):
        print('10 min update started at '+ str(dt.now()))
        await bf.war_data()
        await bf.dispatch_data()
        await bf.orders_data()
        await bf.campaign_and_planet_data()
        print('10 min update finshed at '+ str(dt.now()))
    
    @primary_data.before_loop
    async def before_upload(self):
        print('Primary Waiting...')
        await self.bot.wait_until_ready()
        print('Primary Ready!')
        
    @tasks.loop(minutes=60)
    async def secondary_data(self):
        print('60 min update started at '+ str(dt.now()))
        await bf.planet_data()
        print('60 min update finshed at '+ str(dt.now()))
        
    @secondary_data.before_loop
    async def before_upload(self):
        print('Secondary Waiting...')
        await self.bot.wait_until_ready()
        print('Secondary Ready!')


            
bot = DemBot(command_prefix='!', description=descrip, intents=intents)
    
@bot.tree.command(name='war',description='Display the overall stats of the current Galactic War') #shows info on the galatic war in general
@app_commands.describe(public='Select True to share the response in this channel.')
async def war(interaction: discord.Interaction, public: bool=False):
    await interaction.response.defer(ephemeral=not public, thinking=True)
    msg = await bf.war()
    await interaction.followup.send(embed=msg)

@bot.tree.command(name='orders', description='Displays the current Major Order') #shows info on the current Major Order in general
@app_commands.describe(public='Select True to share the response in this channel.')
async def orders(interaction: discord.Interaction, public: bool=False):
    await interaction.response.defer(ephemeral=not public, thinking=True)
    msg = await bf.orders()
    await interaction.followup.send(embeds=msg)

@bot.tree.command(name='dispatch', description='Displays the [number] most recent dispatch message(s) from Super Earth. Defaults to 1, max 10')
@app_commands.describe(number='The number of messages requested.', public='Select True to share the response in this channel.')
async def dispatch(interaction: discord.Interaction, number: int=1, public: bool=False):
    #displays latest dispatch messages
    await interaction.response.defer(ephemeral=not public, thinking=True)
    if number > 10:
        await interaction.followup.send(embed = discord.Embed(title="--Error--", description="Maximum number of dispatch messages is 10."))
    query= f'SELECT d.published, d.message FROM dispatch d ORDER BY d.id DESC OFFSET 0 LIMIT {number}'
    results = await bf.db_query('dispatch', query)
    msg = []
    for item in results:
        msg.append(discord.Embed(title=str(dt.strptime(item['published'][0:10], '%Y-%m-%d') + relativedelta(years=160))[0:10])) 
        msg[-1].add_field(name='', value= item['message'], inline=False) 
    await interaction.followup.send(embeds=msg)


@bot.tree.command(name='planets',description='Displays information on a specific planet') #gathers liberation info and stats on a specific planet
@app_commands.describe(name='The name of the planet to view.', public='Select True to share the response in this channel.')
async def planets(interaction: discord.Interaction, name: str, public: bool=False):
    await interaction.response.defer(ephemeral=not public, thinking=True)
    msg = await bf.planet(name)
    await interaction.followup.send(embed=msg)

@planets.autocomplete('name')
async def planets_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    try:
        return [
            app_commands.Choice(name=planet, value=planet)
            for planet in planetlist if current.upper() in planet.upper()]
    except discord.errors.HTTPException:
        print('Too Many Autocomplete Results')

@bot.tree.command(name='campaigns',description='Displays the currently available Liberation and Defense campaigns.')
@app_commands.describe(public='Select True to share the response in this channel.')
async def campaigns(interaction: discord.Interaction, public: bool=False):
    await interaction.response.defer(ephemeral=not public, thinking=True)
    libcam, defcam = await bf.campaigns()
    if len(defcam) > 25:
        await interaction.followup.send(embeds=[libcam,defcam])
    else:
        await interaction.followup.send(embed=libcam)

@bot.tree.command(name='stratagems',description='Displays information for any stratagems containing the name included') #show info on requested stratgems
@app_commands.describe(name='The name of the stratagem to view.', public='Select True to share the response in channel.')
async def stratagems(interaction: discord.Interaction, name: str, public: bool=False):
    await interaction.response.defer(ephemeral=not public, thinking=True)
    msg = await bf.stratagems(name)
    await interaction.followup.send(embed=msg)

@stratagems.autocomplete('name')
async def stratagems_autocomplete(
    interaction: discord.Interaction,
    current: str
) -> list[app_commands.Choice[str]]:
    try:
        return [
            app_commands.Choice(name=stratagem, value=stratagem)
            for stratagem in stratlist if current.lower() in stratagem.lower()][:25]
    except discord.errors.HTTPException:
        pass

@bot.tree.command(name='report', description='Issues the F-33D form link to provide feedback to Super Earth High Command')
async def report(interaction: discord.Interaction):
    msg = discord.Embed(title='--Reports to Super Earth--', description= 'Please submit bug reports and feature requests via form [F-33D](https://forms.gle/mAPt9wcj4qeaT2g26)\n\nThank you for your service, Helldiver!', type='rich')
    await interaction.followup.send(embed= msg,ephemeral=True)   
        
@bot.command()
async def shutdown(self, ctx):
    if ctx.author.id == 157695574580264960: 
        await self.close()
        
@bot.command()
async def sync(self, ctx):
    if ctx.author.id == 157695574580264960: 
        await self.tree.sync() 
        await ctx.channel.send(content='Commands Synchronized') 
               
 #testing to access MO Data
if'--MOData'.lower() in sys.argv:
    response = bf.session.get("https://api.helldivers2.dev/api/v1/assignments")
    print(json.dumps(response.json(), indent=2))
    sys.exit()
elif '--test'.lower() in sys.argv:
    bot.run(bot_test_token)
else:
    bot.run(token) #starts bot and begins listening for events and commands