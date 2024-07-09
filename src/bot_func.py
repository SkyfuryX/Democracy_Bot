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
    query='SELECT * FROM war_status w ORDER BY w._ts DESC OFFSET 0 LIMIT 1'
    results = await db_query('war_status', query)
    war = results[0]
    msg = discord.Embed(title='**--Galactic War--**', type='rich')
    msg.add_field(name='Helldivers Active:', value=await commas(war['playerCount']))
    msg.add_field(name='Successful Missions:', value=await commas(war['missionsWon']))
    msg.add_field(name='Failed Missions:', value=await commas(war['missionsLost']))
    msg.add_field(name='Bullets Fired:', value=await commas(war['bulletsFired']))
    msg.add_field(name='Helldivers KIA:', value=await commas(war['deaths']), )
    msg.add_field(name='Accidentals:', value=await commas(war['friendlies']))
    msg.add_field(name='', value='', inline=False)
    msg.add_field(name='-Enemies Liberated-', value='',inline=False)
    msg.add_field(name='Automatons:', value=await commas(war['automatonKills']))
    msg.add_field(name='Terminids:', value=await commas(war['terminidKills']))
    msg.add_field(name='Illuminate:', value=await commas(war['illuminateKills']))
    return msg

async def orders():
    query='SELECT o.title, o.briefing, o.description, o.expiration, o.tasks, o.progress FROM major_orders o ORDER BY o.expiration DESC OFFSET 0 LIMIT 1'
    results = await db_query('major_orders', query)
    for item in results:
        order = item
    now = dt.now(timezone.utc) + timedelta(hours=4)
    timeleft = dt.strptime(order['expiration'], '%Y-%m-%d %H:%M:%S').astimezone(timezone.utc) - now #find time remaining for objective
    if timeleft.days < 0:
        msg = discord.Embed(title='-Awaiting Orders from Super Earth-', type='rich')
        return msg
    hoursleft = math.floor(timeleft.seconds/3600)
    minsleft =  math.floor((timeleft.seconds/3600-hoursleft)*60)
    msg = discord.Embed(title='**--' + order['title'] + '--**', type='rich')
    msg.add_field(name=order['briefing'], value= order['description'], inline = False)
    planetIDs = []
    for task in order['tasks']: #Determine objective type
        if task['type'] == 11 or task['type'] == 13:
            planetIDs.append(str(task['values'][2]))
    if len(planetIDs) > 0:
        i=0
        query = 'SELECT p.name, p.currentOwner, p.maxHealth, p.health FROM planets p WHERE p.index IN ('+', '.join(planetIDs)+')'
        results = await db_query('planets', query)
        for item in results:
            if item['currentOwner'] == 'Humans' and (item['health']/item['maxHealth']) == 1:
                i +=1
                msg.add_field(name= item['name'], value= '100% Liberated', inline=True)
            else:
                i +=1
                msg.add_field(name= item['name'], value= str(abs(round((item['health']/item['maxHealth'] -1)*100, 4))) + '% Liberated', inline= True)
        if i % 3 != 0:
            for x in range(int(round(i/3,0)), 3):
                msg.add_field(name='', value='')
        msg.add_field(name='Time Remaining', value= str(timeleft.days) + ' days ' + str(hoursleft) + ' hours ' + str(minsleft) + ' minutes', inline=False)
    return msg
    
async def planet(name):
    query='SELECT * FROM planets p WHERE p.name = "'+name.upper()+'"'
    results = await db_query('planets', query)  
    for item in results: 
        if item['currentOwner'] == 'Humans':
            item['currentOwner'] = 'Super Earth'
        stats = item['statistics']
        stats['enemiesKilled'] = stats['illuminateKills']+stats['automatonKills']+stats['terminidKills']
        #msg = discord.Embed(title='**--'+item['name']+'--**', description= item['currentOwner']+' Control', type='rich')
        #msg = '**--'+item['name']+'--** \n'+item['currentOwner']+' Control'
        if item['currentOwner'] == 'Super Earth' and (item['health']/item['maxHealth']) == 1 and item['event'] == None:
            msg = discord.Embed(title='**--'+item['name']+'--**', description= item['currentOwner']+' Control\n100% Liberated', type='rich')
        elif item['currentOwner'] == 'Super Earth' and (item['health']/item['maxHealth']) == 1 and item['event'] == True:
            event = item['event']
            msg = discord.Embed(title='**--'+item['name']+'--**', description= item['currentOwner']+' Control\n'+str(abs(round((event['health']/event['maxHealth'] -1)*100, 4))) + '% Defended', type='rich')
        else:
            msg = discord.Embed(title='**--'+item['name']+'--**', description= item['currentOwner']+' Control\n'+str(abs(round((item['health']/item['maxHealth'] -1)*100, 4))) + '% Liberated', type='rich')
        msg.add_field(name='Sector:', value=item['sector'])
        if len(item['hazards']) > 1:
            msg.add_field(name='Biome and Hazards:', value=item['biome']['name']+' - '+ item['hazards'][0]['name'] + ', '+ item['hazards'][1]['name'])
        else:
            msg.add_field(name='Biome and Hazards:', value=item['biome']['name']+' - '+ item['hazards'][0]['name'])
        query2='SELECT p.name FROM planets p WHERE p.id IN ("'+ '","'.join(str(x) for x in item['waypoints'])  +'")'
        planetlst = await db_query('planets', query2)
        if len(planetlst) > 0:
            msg.add_field(name='Supply Lines:', value=', '.join(x['name'] for x in planetlst)) 
        else:
            msg.add_field(name ='', value='')
        msg.add_field(name='----------------------------------', value='', inline= False)
        msg.add_field(name='Helldivers Active:', value=await commas(stats['playerCount']))
        msg.add_field(name='Bullets Fired:', value=await commas(stats['bulletsFired']))
        msg.add_field(name='', value='')
        msg.add_field(name='Helldivers KIA:', value=await commas(stats['deaths']), )
        msg.add_field(name='Enemies Liberated:', value=await commas(stats['enemiesKilled']))
        msg.add_field(name='', value='')
        return msg
    msg = discord.Embed(title='-Planet Not Found-', type='rich')
    return msg
            
async def campaigns():      
    autodef = []
    bugdef = []
    illudef= []
    autolib = []
    buglib = []
    illulib = [] #in preparation for Illuminate to be in game
    libcam = discord.Embed(title='**--Liberation Campaigns--**', type='rich')
    defcam = discord.Embed(title='**--Defense Campaigns--**', type='rich')
    query='SELECT * FROM campaigns c'
    results = await db_query('campaigns', query)
    for item in results:
        if item['planet']['currentOwner'] == 'Humans' and len(item['planet']['event']) > 0:
            if item['planet']['event']['faction'] == 'Terminids':
                bugdef.append(item['planet']['name'] + ' ' + str(abs(round((item['planet']['event']['health']/item['planet']['event']['maxHealth'] -1)*100, 4))) + '%')
            if item['planet']['event']['faction'] == 'Automaton':
                autodef.append(item['planet']['name'] + ' ' + str(abs(round((item['planet']['event']['health']/item['planet']['event']['maxHealth'] -1)*100, 4))) + '%')
            if item['planet']['event']['faction'] == 'Illuminate':
                illudef.append(item['planet']['name'] + ' ' + str(abs(round((item['planet']['event']['health']/item['planet']['event']['maxHealth'] -1)*100, 4))) + '%')
        elif item['planet']['currentOwner'] == 'Automaton':
            autolib.append(item['planet']['name'] + ' ' + str(abs(round((item['planet']['health']/item['planet']['maxHealth'] -1)*100, 4))) + '%')
        elif item['planet']['currentOwner'] == 'Terminids':
            buglib.append(item['planet']['name'] + ' ' + str(abs(round((item['planet']['health']/item['planet']['maxHealth'] -1)*100, 4))) + '%')
        elif item['planet']['currentOwner'] == 'Illuminate':
            illulib.append(item['planet']['name'] + ' ' + str(abs(round((item['planet']['health']/item['planet']['maxHealth'] -1)*100, 4))) + '%')
    #only add each section is it has extra content
    if len(autolib) > 0:
        libcam.add_field(name ='Automaton Front:', value = ', '.join(autolib),inline=False) 
    if len(buglib) > 0:
        libcam.add_field(name ='Terminid Front:', value = ', '.join(buglib),inline=False)   
    if len(illulib) > 0:
        libcam.add_field(name ='Illuminate Front:', value = ', '.join(illulib), inline=False)     
    if len(autodef) > 0:
        defcam.add_field(name ='Automaton Front:', value = ', '.join(autodef), inline=False) 
    if len(bugdef) > 0:
        defcam.add_field(name ='Terminid Front:', value = ', '.join(bugdef), inline=False)
    if len(illudef) > 0:
        defcam.add_field(name ='Illuminate Front:', value = ', '.join(illudef), inline=False)
    return libcam, defcam

            
async def stratagems(name):
    emojikeys = {'up': ':arrow_up:','down':':arrow_down:','left':':arrow_left:','right':':arrow_right:'}
    query = 'SELECT * FROM stratagems s WHERE CONTAINS(s.name, "'+name+'", true) OFFSET 0 LIMIT 1'
    results = await db_query('stratagems', query)
    if len(results) == 0:
        msg = discord.Embed(title='-Stratagem Not Found-', type='rich')
        return msg
    else:
        for item in results:
            if item['codename'] != None:
                msg = discord.Embed(title='**--'+item['codename'] + ' - ' + item['name']+'--**', type='rich')
            else:
                msg = discord.Embed(title='**--'+item['name']+'--**', type='rich')
            if item['activation'] == None:
                item['activation'] = 0
            if item['cooldown'] == None:
                item['cooldown'] = 0      
            keys = ''
            for key in item['keys']:
                keys += emojikeys[key]
            msg.add_field(name='Call-in Time:', value= str(item['activation']) + ' sec')
            msg.add_field(name='Cooldown Time:', value= str(item['cooldown']) + ' sec')
            msg.add_field(name='', value = '')
            msg.add_field(name='Uses:', value= item['uses'])
            msg.add_field(name='Activation:', value= keys)
            msg.add_field(name='', value = '')
        return msg