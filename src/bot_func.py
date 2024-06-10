import os, re, random, math, discord
from discord.ext import commands
from dateutil.relativedelta import relativedelta
from datetime import datetime as dt, timezone, timedelta
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from azure.cosmos import CosmosClient

load_dotenv()
token = os.getenv('bot_token')
db_uri = os.getenv('account_uri')
db_key = os.getenv('account_key')

client = CosmosClient(url=db_uri, credential=db_key)
database_name = 'democracy_bot'
database = client.get_database_client(database_name)

def commas(number):
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

def war():
    container = database.get_container_client('war_status')
    for item in container.query_items(
        query='SELECT * FROM war_status w ORDER BY w.id DESC OFFSET 0 LIMIT 1',
        enable_cross_partition_query=True):
        war = item 
    msg = ('**--Galactic War Stats--**\nHelldivers Active: '+ commas(war['playerCount']) +'\nHelldivers KIA: ' + commas(war['deaths']) + 
           '\nAutomatons Killed: '+ commas(war['automatonKills']) +'\nTerminids Killed: '+ commas(war['terminidKills']) +
           '\nIlluminate Killed: '+ commas(war['illuminateKills']) +'\nBullets Fired: ' + commas(war['bulletsFired']))
    return msg

def orders():
    container = database.get_container_client('major_orders')
    for item in container.query_items(
        query='SELECT o.title, o.briefing, o.description, o.expiration, o.tasks, o.progress FROM major_orders o ORDER BY o.id DESC OFFSET 0 LIMIT 1',
        enable_cross_partition_query=True):
        order = item
    msg = ('**--' + order['title'] + '--**\n' + order['briefing'] + '\n'+order['description'])
    now = dt.now(timezone.utc) + timedelta(hours=4)
    timeleft = dt.strptime(order['expiration'], '%Y-%m-%d %H:%M:%S').astimezone(timezone.utc) - now #find time remaining for objective
    hoursleft = math.floor(timeleft.seconds/3600)
    minsleft =  math.floor((timeleft.seconds/3600-hoursleft)*60)
    planetIDs = []
    for task in order['tasks']: #Determine objective type
        if task['type'] == 11:
            planetIDs.append(str(task['values'][2]))
    if len(planetIDs) > 0:
        container = database.get_container_client('planets')
        for item in container.query_items(query='SELECT p.name, p.currentOwner, p.maxHealth, p.health FROM planets p WHERE p.index IN ('+', '.join(planetIDs)+')',
            enable_cross_partition_query=True):
            if item['currentOwner'] == 'Humans' and (item['health']/item['maxHealth']) == 1:
                msg += '\n> '+ item['name'] + ' - 100% Liberated'
            else:
                msg += '\n> '+ item['name'] + ' - ' + str(abs(round((item['health']/item['maxHealth'] -1)*100, 4))) + '% Liberated'
        msg += ('\nTime Remaining: ' + str(timeleft.days) + ' days ' + str(hoursleft) + ' hours ' + str(minsleft) + ' minutes')
        return msg
    
def planet(name):
    container = database.get_container_client('planets')    
    for item in container.query_items(query='SELECT * FROM planets p WHERE p.name = "'+name.upper()+'"',
            enable_cross_partition_query=True): 
        if item['currentOwner'] == 'Humans':
            item['currentOwner'] = 'Super Earth'
        stats = item['statistics']
        stats['enemiesKilled'] = stats['illuminateKills']+stats['automatonKills']+stats['terminidKills']
        msg = '**--'+item['name']+'--** \n'+item['currentOwner']+' Control'
        if item['currentOwner'] == 'Super Earth' and (item['health']/item['maxHealth']) == 1 and item['event'] == None:
            msg += '\n100% Liberated'
        elif item['currentOwner'] == 'Super Earth' and (item['health']/item['maxHealth']) == 1 and item['event'] == True:
            event = item['event']
            msg += '\n'+str(abs(round((event['health']/event['maxHealth'] -1)*100, 4))) + '% Defended'
        else:
            msg += '\n'+str(abs(round((item['health']/item['maxHealth'] -1)*100, 4))) + '% Liberated'
        msg += ('\n------------------\nHelldivers Active: '+ commas(stats['playerCount']) +'\nEnemies Killed: '+commas(stats['enemiesKilled'])+
                '\nHelldivers KIA: ' + commas(stats['deaths']) + '\nBullets Fired: '+commas(stats['bulletsFired']))
        return msg
    msg = '-Planet not found-'
    return msg
            
  
def campaigns():      
    container = database.get_container_client('campaigns')
    msg = '**--Active Campaigns--**'
    defense = '\n-Defense Campaigns- \n|'
    autofrnt = '\n-Automaton Front-\n|'
    bugfrnt = '\n-Terminid Front-\n|'
    illufrnt = '\n-Illuminate Front-\n|' # in preparation for Illuminate to be in-game
    for item in container.query_items(query='SELECT * FROM campaigns c',
            enable_cross_partition_query=True):
        if item['planet']['currentOwner'] == 'Humans' and item['planet']['event'] == True:
            defense += ' ' + item['planet']['name'] + ' ' + str(abs(round((item['planet']['event']['health']/item['planet']['event']['maxHealth'] -1)*100, 4))) + '% |'
        elif item['planet']['currentOwner'] == 'Automaton':
            autofrnt += ' '+ item['planet']['name'] + ' ' + str(abs(round((item['planet']['health']/item['planet']['maxHealth'] -1)*100, 4))) + '% |'
        elif item['planet']['currentOwner'] == 'Terminids':
            bugfrnt += ' '+ item['planet']['name'] + ' ' + str(abs(round((item['planet']['health']/item['planet']['maxHealth'] -1)*100, 4))) + '% |'
        elif item['planet']['currentOwner'] == 'Illuminate':
            illufrnt += ' '+ item['planet']['name'] + ' ' + str(abs(round((item['planet']['health']/item['planet']['maxHealth'] -1)*100, 4))) + '% |'
    if len(autofrnt) > 20:
        msg += autofrnt
    if len(bugfrnt) > 19:
        msg += bugfrnt    
    if len(illufrnt) > 21:
        msg += illufrnt    
    if len(defense) > 23:
        msg += defense
    return msg
            
            