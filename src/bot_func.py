import os, re, random, math, discord
from discord.ext import commands
from dateutil.relativedelta import relativedelta
from datetime import datetime as dt, timezone, timedelta
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from azure.cosmos.aio import CosmosClient

load_dotenv()
db_uri = os.getenv('account_uri')
db_key = os.getenv('account_key')

async def db_query(cont_name, db_query):
    async with CosmosClient(url=db_uri, credential=db_key) as client:
        database =  client.get_database_client('democracy_bot')
        container = database.get_container_client(cont_name)
        results = [item async for item in container.query_items(query=db_query)]
        return results
    
async def db_upload(cont_name):
    async with CosmosClient(url=db_uri, credential=db_key) as client:
        database =  client.get_database_client('democracy_bot')
        container = database.get_container_client(cont_name)
        return container

async def commas(number):
    numlst = list(str(number))
    x = int(math.floor(len(numlst) / 3))
    i = 1
    if len(numlst) <=3:
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

async def war():
    query='SELECT * FROM war_status w ORDER BY w.id DESC OFFSET 0 LIMIT 1'
    results = await db_query('war_status', query)
    for item in results:
        war = item 
    msg = ('**--Galactic War Stats--**\nHelldivers Active: '+ await commas(war['playerCount']) +'\nHelldivers KIA: ' + await commas(war['deaths']) + 
           '\nAutomatons Killed: '+ await commas(war['automatonKills']) +'\nTerminids Killed: '+ await commas(war['terminidKills']) +
           '\nIlluminate Killed: '+ await commas(war['illuminateKills']) +'\nBullets Fired: ' + await commas(war['bulletsFired']))
    return msg

async def orders():
    query='SELECT o.title, o.briefing, o.description, o.expiration, o.tasks, o.progress FROM major_orders o ORDER BY o.expiration DESC OFFSET 0 LIMIT 1'
    results = await db_query('major_orders', query)
    for item in results:
        order = item
    msg = ('**--' + order['title'] + '--**\n' + order['briefing'] + '\n'+order['description'])
    now = dt.now(timezone.utc) + timedelta(hours=4)
    timeleft = dt.strptime(order['expiration'], '%Y-%m-%d %H:%M:%S').astimezone(timezone.utc) - now #find time remaining for objective
    if timeleft.days < 0:
        msg = '-Awaiting Orders from Super Earth-'
        return msg
    hoursleft = math.floor(timeleft.seconds/3600)
    minsleft =  math.floor((timeleft.seconds/3600-hoursleft)*60)
    planetIDs = []
    for task in order['tasks']: #Determine objective type
        if task['type'] == 11:
            planetIDs.append(str(task['values'][2]))
    if len(planetIDs) > 0:
        query = 'SELECT p.name, p.currentOwner, p.maxHealth, p.health FROM planets p WHERE p.index IN ('+', '.join(planetIDs)+')'
        results = await db_query('planets', query)
        for item in results:
            if item['currentOwner'] == 'Humans' and (item['health']/item['maxHealth']) == 1:
                msg += '\n> '+ item['name'] + ' - 100% Liberated'
            else:
                msg += '\n> '+ item['name'] + ' - ' + str(abs(round((item['health']/item['maxHealth'] -1)*100, 4))) + '% Liberated'
        msg += ('\nTime Remaining: ' + str(timeleft.days) + ' days ' + str(hoursleft) + ' hours ' + str(minsleft) + ' minutes')
        return msg
    
async def planet(name):
    query='SELECT * FROM planets p WHERE p.name = "'+name.upper()+'"'
    results = await db_query('planets', query)  
    for item in results: 
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
        msg += '\nSector: '+ item['sector'] +'\nBiome and Hazards: ' + item['biome']['name'] + ' - '
        if len(item['hazards']) > 1:
            msg += item['hazards'][0]['name'] + ', '+ item['hazards'][1]['name']
        else:
            msg += item['hazards'][0]['name']
        query2='SELECT p.name FROM planets p WHERE p.id IN ("'+ '","'.join(str(x) for x in item['waypoints'])  +'")'
        planetlst = await db_query('planets', query2)
        if len(planetlst) > 0:
            msg += '\nSupply Lines: ' + ', '.join(x['name'] for x in planetlst)
        msg += ('\n------------------\nHelldivers Active: '+ await commas(stats['playerCount']) +'\nEnemies Killed: '+ await commas(stats['enemiesKilled'])+
                '\nHelldivers KIA: ' + await commas(stats['deaths']) + '\nBullets Fired: '+ await commas(stats['bulletsFired']))
        return msg
    msg = '-Planet not found-'
    return msg
            
async def campaigns():      
    msg = '**--Active Campaigns--**'
    defense = '\n-Defense Campaigns- \n|'
    autofrnt = '\n-Automaton Front-\n|'
    bugfrnt = '\n-Terminid Front-\n|'
    illufrnt = '\n-Illuminate Front-\n|' #in preparation for Illuminate to be in game
    query='SELECT * FROM campaigns c'
    results = await db_query('campaigns', query)
    for item in results:
        if item['planet']['currentOwner'] == 'Humans' and len(item['planet']['event']) > 0:
            defense += ' ' + item['planet']['name'] + ' ' + str(abs(round((item['planet']['event']['health']/item['planet']['event']['maxHealth'] -1)*100, 4))) + '% |'
        elif item['planet']['currentOwner'] == 'Automaton':
            autofrnt += ' '+ item['planet']['name'] + ' ' + str(abs(round((item['planet']['health']/item['planet']['maxHealth'] -1)*100, 4))) + '% |'
        elif item['planet']['currentOwner'] == 'Terminids':
            bugfrnt += ' '+ item['planet']['name'] + ' ' + str(abs(round((item['planet']['health']/item['planet']['maxHealth'] -1)*100, 4))) + '% |'
        elif item['planet']['currentOwner'] == 'Illuminate':
            illufrnt += ' '+ item['planet']['name'] + ' ' + str(abs(round((item['planet']['health']/item['planet']['maxHealth'] -1)*100, 4))) + '% |'
    #only add each section is it has extra content
    if len(autofrnt) > 20:
        msg += autofrnt
    if len(bugfrnt) > 19:
        msg += bugfrnt    
    if len(illufrnt) > 21:
        msg += illufrnt    
    if len(defense) > 23:
        msg += defense
    return msg
            
async def stratagems(name):
    emojikeys = {'up': ':arrow_up:','down':':arrow_down:','left':':arrow_left:','right':':arrow_right:'}
    query = 'SELECT * FROM stratagems s WHERE CONTAINS(s.name, "'+name+'", true) OFFSET 0 LIMIT 1'
    results = await db_query('stratagems', query)
    if results == None:
        msg = '-Stratagem Not Found-'
        return msg
    else:
        msg = '**--Stratagem Info--**\n'
        for item in results:
            if item['codename'] != None:
                msg += item['codename'] + ' - ' + item['name']
            else:
                msg += item['name']
            if item['activation'] == None:
                item['activation'] = 0
            if item['cooldown'] == None:
                item['cooldown'] = 0      
            msg += '\n> Call-in Time: ' + str(item['activation']) + ' sec\n> Uses: ' + item['uses'] + '\n> Cooldown Time: '+ str(item['cooldown']) + ' sec\n> Keys: '
            for key in item['keys']:
                msg += emojikeys[key]
        return msg