from email import message
import discord, sys, json, re, random
from discord import app_commands
from discord.ext import commands
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from functions import (
    war, 
    orders,
    planet,
    campaigns,
    stratagems, 
    stratlist,
    planetlist
)
from database import db_query, db_upload, db_delete

with open('liberty.txt', 'r') as file:
    inspiration = file.readlines()

class CommandCog(commands.Cog, name="Commands"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.inspiration_tracker = {}
        
    @app_commands.command(name='war',description='Display the overall stats of the current Galactic War') #shows info on the galatic war in general
    @app_commands.describe(public='Select True to share the response in this channel.')
    async def war(self, interaction: discord.Interaction, public: bool=False):
        await interaction.response.defer(ephemeral=not public, thinking=True)
        msg = await war()
        await interaction.followup.send(embed=msg)

    @app_commands.command(name='orders', description='Displays the current Major Order') #shows info for the current Major Order(s)
    @app_commands.describe(public='Select True to share the response in this channel.')
    async def orders(self, interaction: discord.Interaction, public: bool=False):
        await interaction.response.defer(ephemeral=not public, thinking=True)
        msg = await orders()
        await interaction.followup.send(embeds=msg)

    @app_commands.command(name='dispatch', description='Displays the [number] most recent dispatch message(s) from Super Earth. Defaults to 1, max 10')
    @app_commands.describe(number='The number of messages requested.', public='Select True to share the response in this channel.')
    async def dispatch(self, interaction: discord.Interaction, number: int=1, public: bool=False):
        #displays latest dispatch messages
        await interaction.response.defer(ephemeral=not public, thinking=True)
        if number > 10:
            await interaction.followup.send(embed = discord.Embed(title="--Error--", description="Maximum number of dispatch messages is 10."))
        query= f'SELECT d.published, d.message FROM dispatch d ORDER BY d.id DESC OFFSET 0 LIMIT {number}'
        results = await db_query('dispatch', query)
        msg = []
        for item in results:
            msg.append(discord.Embed(title=str(dt.strptime(item['published'][0:10], '%Y-%m-%d') + relativedelta(years=160))[0:10])) 
            msg[-1].add_field(name='', value= item['message'], inline=False) 
        await interaction.followup.send(embeds=msg)

    @app_commands.command(name='planets',description='Displays information on a specific planet') #gathers liberation info and stats on a specific planet
    @app_commands.describe(name='The name of the planet to view.', public='Select True to share the response in this channel.')
    async def planets(self, interaction: discord.Interaction, name: str, public: bool=False):
        await interaction.response.defer(ephemeral=not public, thinking=True)
        msg = await planet(name)
        await interaction.followup.send(embed=msg)

    @planets.autocomplete('name')
    async def planets_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        try:
            return [
                app_commands.Choice(name=planet, value=planet)
                for planet in planetlist if current.upper() in planet.upper()][:25]
        except discord.errors.HTTPException:
            print('Too Many Autocomplete Results')

    @app_commands.command(name='campaigns',description='Displays the currently available Liberation and Defense campaigns.')
    @app_commands.describe(public='Select True to share the response in this channel.')
    async def campaigns(self, interaction: discord.Interaction, public: bool=False):
        await interaction.response.defer(ephemeral=not public, thinking=True)
        libcam, defcam = await campaigns()
        if len(defcam) > 25:
            await interaction.followup.send(embeds=[libcam,defcam])
        else:
            await interaction.followup.send(embed=libcam)

    @app_commands.command(name='stratagems',description='Displays information for any stratagems containing the name included') #show info on requested stratgems
    @app_commands.describe(name='The name of the stratagem to view.', public='Select True to share the response in channel.')
    async def stratagems(self, interaction: discord.Interaction, name: str, public: bool=False):
        await interaction.response.defer(ephemeral=not public, thinking=True)
        msg = await stratagems(name)
        await interaction.followup.send(embed=msg)

    @stratagems.autocomplete('name')
    async def stratagems_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        try:
            return [
                app_commands.Choice(name=stratagem, value=stratagem)
                for stratagem in stratlist if current.lower() in stratagem.lower()][:25]
        except discord.errors.HTTPException:
            pass    
        
    @app_commands.command(name='inspiration', description='Brings you quotes from the front lines across the galaxy!')
    async def inspirtation(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False, thinking=True)
        userid = interaction.user.id
        if userid not in self.inspiration_tracker.keys():
            i = random.randint(0,len(inspiration)-1)
            self.inspiration_tracker[userid] = [99,99,99,99,99]
            self.inspiration_tracker[userid][4] = i
            await interaction.followup.send(embed=discord.Embed(title=inspiration[i].strip()))
        else:
            x = random.choice([e for e in range(len(inspiration)) if e not in self.inspiration_tracker[userid]])
            for a in range(4):
                self.inspiration_tracker[userid][a] = self.inspiration_tracker[userid][a+1] 
            self.inspiration_tracker[userid][4] = x  
            await interaction.followup.send(embed=discord.Embed(title=inspiration[x].strip()))
    
    @app_commands.command(name='report', description='Issues the F-33D form link to provide feedback to Super Earth High Command')
    async def report(self, interaction: discord.Interaction):
        msg = discord.Embed(title='--Reports to Super Earth--', description= 'Please submit bug reports and feature requests via the [Support Discord](https://discord.gg/jtcRdqsG)\n\nThank you for your service, Helldiver!', type='rich')
        await interaction.response.send_message(embed=msg, ephemeral=True)        
    
    @commands.command(hidden=True)
    async def shutdown(self, ctx):
        if ctx.author.id == 157695574580264960: 
            await self.close()
            
    @commands.command(hidden=True)
    async def sync(self, ctx):
        if ctx.author.id == 157695574580264960: 
            await self.bot.tree.sync() 
            await ctx.channel.send(content='Commands Synchronized')