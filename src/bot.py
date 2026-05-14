from aiohttp import ClientSession
import asyncio
from functions import config
import discord, sys, json, ast
from discord.ext import commands

from commands import CommandCog
from data import DataCog

#examples https://github.com/Rapptz/discord.py/tree/master/examples
token = config['BOT_TOKEN'] 
bot_test_token = config['BOT_TEST_TOKEN'] #token for testing bot commands in a private server

class DemBot(commands.Bot):       
    def __init__(
        self,
        *args,
        web_client: ClientSession,
        **kwargs 
    ):
        super().__init__(*args, **kwargs)
        self.web_client = web_client
        
    async def setup_hook(self):
        if '--test' in sys.argv:
            pass
        else:
            await self.add_cog(DataCog(self))
            await self.add_cog(CommandCog(self))
      
    @commands.Cog.listener()
    async def on_ready(self):
        print('Logged on as', self.user)
        
    @commands.Cog.listener()
    async def on_connect(self):
        await self.change_presence(activity=discord.CustomActivity(name='Spreading Managed Democracy'))           

async def main():
    async with ClientSession(headers=ast.literal_eval(config['HEADER'])) as our_client:
        
        intents = discord.Intents.default()
        descrip = '''A discord bot to view on-demand statistics from the game Helldivers 2. Includes Planet info, Major Orders, Dispatches from Super Earth, and more.\n/report for bugs or feature requests.\nDiscord Contact: @sky.fury'''
        intents.message_content = False
        async with DemBot(
            command_prefix='!',
            intents= intents,
            description = descrip,
            web_client= our_client
        ) as bot:
            if'--MOData'.lower() in sys.argv: #print MO Data from API call only, does not run                
                async with bot.web_client.get("https://api.helldivers2.dev/api/v1/assignments") as response:
                    print(json.dumps(await response.json(), indent=2))
                sys.exit(0)
            elif '--test'.lower() in sys.argv: #starts bot using test token, omits Data Cog
                await bot.start(bot_test_token)
            else:
                await bot.start(token) #starts bot
            
asyncio.run(main())                  