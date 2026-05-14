from functions import config
import discord, sys, json, requests, ast
from discord.ext import commands
from azure.core import exceptions

from commands import CommandCog
from data import DataCog

#examples https://github.com/Rapptz/discord.py/tree/master/examples
token = config['BOT_TOKEN'] 
bot_test_token = config['BOT_TEST_TOKEN'] #token for testing bot commands in a private server

#initiate bot
intents = discord.Intents.default()
descrip = '''A discord bot to view on-demand statistics from the game Helldivers 2. Includes Planet info, Major Orders, Dispatches from Super Earth, and more.\n/report for bugs or feature requests.\nDiscord Contact: @sky.fury'''

class DemBot(commands.Bot):       
    async def setup_hook(self):
        if '--test' in sys.argv:
            pass
        else:
            await self.add_cog(DataCog(bot))
        await self.add_cog(CommandCog(bot))
        
    @commands.Cog.listener()
    async def on_ready(self):
        print('Logged on as', self.user)
        
    @commands.Cog.listener()
    async def on_connect(self):
        await self.change_presence(activity=discord.CustomActivity(name='Spreading Managed Democracy'))           

bot = DemBot(command_prefix='!', description=descrip, intents=intents)
                   
if'--MOData'.lower() in sys.argv: #print MO Data from API call only, does not run
    with requests.Session() as sess: #seeing if this makes data updates more consistant
        header = ast.literal_eval(config['HEADER'])
        ast.literal_eval(config['HEADER'])
        sess.headers.update(header)
    
        response = sess.get("https://api.helldivers2.dev/api/v1/assignments")
        print(json.dumps(response.json(), indent=2))
        sys.exit(0)
elif '--test'.lower() in sys.argv: #starts bot using test token, omits Data Cog
    bot.run(bot_test_token)
else:
    bot.run(token) #starts bot