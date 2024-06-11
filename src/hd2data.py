import os, re, schedule, requests, time, ast
from discord.ext import commands
from dateutil.relativedelta import relativedelta
from datetime import datetime as dt, timezone, timedelta, tzinfo
from dotenv import load_dotenv
from azure.cosmos import CosmosClient

#https://helldivers-2.github.io/api/docs/openapi/swagger-ui.html

data = {}
now = dt.now()
dt_string = now.strftime("%m%d%Y%H%M%S")
dt_formatted = now.strftime("%m-%d-%Y- %H:%M:%S")

load_dotenv()
session = requests.Session()
headers = ast.literal_eval(os.getenv('header1'))
session.headers.update(headers)

db_uri = os.getenv('account_uri')
db_key = os.getenv('account_key')
client = CosmosClient(url=db_uri, credential=db_key)
database_name = 'democracy_bot'
database = client.get_database_client(database_name)

# WAR DATA
def war_data():
    #gets only the highest ID for db key since the data doesnt have one itself
    container = database.get_container_client('war_status')
    for item in container.query_items(
            query='SELECT StringToNumber(c.id) as idint FROM c ORDER BY c.idint DESC OFFSET 0 LIMIT 1',
            enable_cross_partition_query=True):
        id = item['idint']
        
    #formats data to table schema
    data['id'] = str(id + 1)
    data['date'] = dt_formatted    

    response = session.get("https://api.helldivers2.dev/api/v1/war") #Overall War data
    war_stats = response.json()
    war_stats = war_stats['statistics']
    war_stats = {key: value for key,value in war_stats.items() if key not in ['revives','timePlayed','accuracy',]}
    data.update(war_stats)

    container.upsert_item(data)
    print('1 War Update Recorded')

#DISPATCH DATA
def dispatch_data():
    container = database.get_container_client('dispatch')
    response = session.get("https://api.helldivers2.dev//api/v1/dispatches") 
    data = response.json()

    #queries for last uploaded id
    for item in container.query_items( #queries for last uploaded id
        query='SELECT d.id as id FROM dispatch d ORDER BY d.id DESC OFFSET 0 LIMIT 1',
        enable_cross_partition_query=True):
        id = int(item['id'])

    count = 0
    for item in data: #inserts new items into db
        if item['id'] > id:
            item['id'] = str(item['id'])
            item['message'] = re.sub('<i=[0-9]>|</i>', '**', item['message'])
            container.upsert_item(item)
            count += 1     
    print(str(count) + ' New Dispatches Recorded')

#PLANET DATA
def planet_data():
    container = database.get_container_client('planets')
    response = session.get("https://api.helldivers2.dev/api/v1/planets")
    data = response.json()

    count = 0
    for item in data: #inserts new items into db
        item['id'] = str(item['index'])
        container.upsert_item(item)
        count += 1      
    print(str(count) + ' Planets Updated') 

#ORDERS DATA
def orders_data():
    response = session.get("https://api.helldivers2.dev/api/v1/assignments")
    data = response.json()
    
    container = database.get_container_client('major_orders')
    count = 0
    for item in data: #inserts new items into db
        item['id'] = str(item['id'])
        item['expiration'] = item['expiration'][0:10] + ' ' + item['expiration'][11:19]
        count += 1 
        container.upsert_item(item)
    print(str(count) + ' Orders Updated')
    
def campaign_data():
    response = session.get("https://api.helldivers2.dev//api/v1/campaigns")
    data = response.json()
    campIDs = []
    for item in data:
        campIDs.append(str(item['id']))
    count = 0
    container = database.get_container_client('campaigns')
    for item in container.query_items(query='SELECT * FROM campaigns c WHERE c.id NOT IN ("'+'", "'.join(campIDs)+'")',
        enable_cross_partition_query=True): #query to find and delete the items no longer in current campaign info
        container.delete_item(item, partition_key=item['name']) 
        count += 1
    cmpmsg = str(count) + ' Campaigns Deleted, '       
    count = 0
    for item in data:
        item['id'] = str(item['id'])
        item['name'] = item['planet']['name']
        count += 1
        container.upsert_item(item)
    print(cmpmsg + str(count) + ' Campaigns Updated')        
        
def data_upload():
    print('Data update started at '+str(dt.now()))
    war_data()
    dispatch_data()
    planet_data()
    orders_data()
    campaign_data()
    print('Data update completed at '+str(dt.now()))
        
schedule.every(30).minutes.do(data_upload)
    
while True:
    schedule.run_pending()
    time.sleep(1)