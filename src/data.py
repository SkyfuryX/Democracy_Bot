import discord, re
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime as dt
from database import db_query, db_upload, db_delete
from functions import session

class DataCog(commands.Cog, name='Data'):
    def __init__(self, bot):
        super().__init__()
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
        await war_data()
        await dispatch_data()
        await orders_data()
        await campaign_and_planet_data()
        print('10 min update finshed at '+ str(dt.now()))
    
    @primary_data.before_loop
    async def before_upload_primary(self):
        print('Primary Waiting...')
        await self.bot.wait_until_ready()
        print('Primary Ready!')
        
    @tasks.loop(minutes=60)
    async def secondary_data(self):
        print('60 min update started at '+ str(dt.now()))
        await planet_data()
        print('60 min update finshed at '+ str(dt.now()))
        
    @secondary_data.before_loop
    async def before_upload_secondary(self):
        print('Secondary Waiting...')
        await self.bot.wait_until_ready()
        print('Secondary Ready!')
        
#DATA UPLOAD FUNCTIONS
async def war_data():
    #gets only the highest ID for db key since the data doesnt have one itself
    results = await db_query('war_status', 'SELECT StringToNumber(c.id) as idint FROM c ORDER BY c.idint DESC OFFSET 0 LIMIT 1')
    id = results[0]['idint']

    now = dt.now()
    dt_formatted = now.strftime("%m-%d-%Y %H:%M:%S")
    #formats data to table schema
    data = {}
    data['id'] = str(id + 1)
    data['date'] = dt_formatted

    response = session.get("https://api.helldivers2.dev/api/v1/war") #Overall War data
    war_stats = response.json()
    war_stats = war_stats['statistics']
    war_stats = {key: value for key,value in war_stats.items() if key not in ['revives','timePlayed','accuracy',]}
    data.update(war_stats)

    await db_upload('war_status', data, 0)
    print('1 War Update Recorded')

#DISPATCH DATA
async def dispatch_data():
    response = session.get("https://api.helldivers2.dev/api/v1/dispatches")
    data = response.json()

    #queries for last uploaded id
    results = await db_query('dispatch', 'SELECT d.id as id FROM dispatch d ORDER BY d.id DESC OFFSET 0 LIMIT 1')
    for item in results:
        id = int(item['id'])
    count = 0
    upload = []
    for item in data: #inserts new items into db
        if item['id'] > id:
            item['id'] = str(item['id'])
            item['message'] = re.sub('<i=[0-9]>|</i>', '**', item['message'])
            count += 1
            upload.append(item)
    if len(upload) > 0:
        await db_upload('dispatch', upload, 0)
    print(str(count) + ' New Dispatches Recorded')

#PLANET DATA
async def planet_data():
    response = session.get("https://api.helldivers2.dev/api/v1/planets")
    data = response.json()
    data[107]['name'] = 'POPLI IX' #manual correction to prevent UTF-8 encoding errors
    count = 0
    for item in data: #inserts new items into db
        item['id'] = str(item['index'])
        count += 1
    await db_upload('planets', data, 0)
    print(str(count) + ' Planets Updated')

#ORDERS DATA
async def orders_data():
    response = session.get("https://api.helldivers2.dev/api/v1/assignments")
    data = response.json()
    count = 0
    for item in data: #inserts new items into db
        item['id'] = str(item['id'])
        item['expiration'] = item['expiration'][0:10] + ' ' + item['expiration'][11:19]
        count += 1

    if count > 0:
        await db_upload('major_orders', data, 0)
    print(str(count) + ' Orders Updated')

async def campaign_and_planet_data():
    response = session.get("https://api.helldivers2.dev/api/v1/campaigns")
    data = response.json()
    campIDs = []
    for item in data:
        campIDs.append(str(item['id']))

    count = await db_delete('campaigns', 'SELECT * FROM campaigns c WHERE c.id NOT IN ("'+'", "'.join(campIDs)+'")')
    cmpmsg = str(count) + ' Campaigns Deleted, '

    # for item in container.query_items(query='SELECT * FROM campaigns c WHERE c.id NOT IN ("'+'", "'.join(campIDs)+'")',
    #     enable_cross_partition_query=True): #query to find and delete the items no longer in current campaign info
    #     await container.delete_item(item, partition_key=item['name'])
    #     count += 1
    # cmpmsg = str(count) + ' Campaigns Deleted, '
    count = 0
    for item in data:
        item['id'] = str(item['id'])
        item['name'] = item['planet']['name']
        count += 1
    await db_upload('campaigns', data, 0)
    print(cmpmsg + str(count) + ' Campaigns Updated')
    count = 0
    for item in data:
        item['planet']['id'] = str(item['planet']['index'])
        count += 1
    await db_upload('planets', data, 1)
    print(str(count) + ' Planets Updated')