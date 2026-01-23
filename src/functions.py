import re, math, discord, requests, ast, os
from datetime import datetime as dt, timezone
from dotenv import dotenv_values
from azure.cosmos.aio import CosmosClient
from database import db_query

config = dotenv_values('./.env')
#load_dotenv(encoding="latin-1") #loads environment variables from .env file
db_uri = config['ACCOUNT_URI']
db_key = config['ACCOUNT_KEY']

data = {}
session = requests.Session()
header = ast.literal_eval(config['HEADER'])
session.headers.update(header)

with open('./auto/planetlist.txt', 'r') as file:
    planetlist = file.read().split(', ')
    file.close()
with open('./auto/sectorlist.txt', 'r') as file:
    sectorlist = file.read().split(', ')
    file.close()
with open('./auto/stratlist.txt', 'r') as file:
    stratlist = file.read().split(', ')
    file.close()

factions = {1:'Super Earth', 2: 'Terminids', 3:'Automatons', 4:'Illuminate'}
difficulty = {1:'Trivial', 2:'Easy', 3:'Medium', 4:'Challenging', 5:'Hard', 6:'Extreme', 7:'Suicide Mission', 8:'Impossible', 9:'Helldive', 10:'Super Helldive'}

#MISC FUNCTION
async def commas(number):
    numlst = list(str(number))
    x, i = int(math.floor(len(numlst) / 3)), 1
    if len(numlst) <=3:
       return number #if number is less than 1000, return as is
    elif len(numlst) % 3 == 0:
        for n in range(x-1):
            i = i - 4
            numlst.insert(i, ',')
    else:
        for n in range(x):
            i = i - 4
            numlst.insert(i, ',')
    return ''.join(numlst) #

#COMMAND FUNCTIONS
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
    response = session.get("https://api.helldivers2.dev/api/v1/assignments")
    try:
        if len(response.json()) == 0:
            msg = [discord.Embed(title='-Awaiting Orders from Super Earth-', type='rich')]
            return msg
    except:
        pass #if the response is empty, pass to avoid errors:
    try:
        query= f'SELECT o.title, o.briefing, o.description, o.expiration, o.tasks, o.progress FROM major_orders o ORDER BY o._ts DESC OFFSET 0 LIMIT {len(response.json())}'
    except:
        query= 'SELECT o.title, o.briefing, o.description, o.expiration, o.tasks, o.progress FROM major_orders o ORDER BY o._ts DESC OFFSET 0 LIMIT 1'
    orders = await db_query('major_orders', query)
    msg = []
    for order in orders:
        timeleft = dt.strptime(order['expiration'], '%Y-%m-%d %H:%M:%S').astimezone(timezone.utc) - dt.now(timezone.utc) #find time remaining for objective, timedelta needed for local hosting only
        if timeleft.days < 0:
            msg = [discord.Embed(title='-Awaiting Orders from Super Earth-', type='rich')]
            return msg
        hoursleft = math.floor(timeleft.seconds/3600)
        minsleft = math.floor((timeleft.seconds/3600-hoursleft)*60)
        msg.append(discord.Embed(title=f"**--{order['title']}--**", type='rich'))
        if all((order['briefing'] == None, order['description'] == None)):
            pass #add no fields since no content in either section
        elif any((order['briefing'] == order['description'], order['description'] == None)): #when sections are either the same content or description is empty
            msg[-1].add_field(name='', value=f"**{order['briefing']}**", inline = False)
        else: #add fields for both
            msg[-1].add_field(name='', value= f"**{order['briefing']}**", inline = False)
            msg[-1].add_field(name='', value= f"order{['description']}", inline = False)
        planetIDs = []
        i=0
        for task in order['tasks']: # Handles task types 2,3,7,9,11,12,13,15
            try:
                if task['type'] == 11 or task['type'] == 13: #Liberate/Defend specific planet
                    if task['values'][2] not in planetIDs:
                        planetIDs.append(str(task['values'][2]))
                    i += 1
                elif task['type'] == 2: # Sample Collections
                    if task['values'][8] == 0: #Faction-Specific
                        if task['values'][4] == 3992382197:
                            msg[-1].add_field(name=f'Common Samples collected from any planet controlled by {factions[task["values"][0]]}:',value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")
                        elif task['values'][4] == 2985106497:
                            msg[-1].add_field(name=f'Rare Samples collected from any planet controlled by {factions[task["values"][0]]}:',value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")   
                    else: #Planet-Specific
                        if task['values'][4] == 3992382197:
                            msg[-1].add_field(name=f"Common Samples collected on {planetlist[task['values'][8]]}:",value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")
                        elif task['values'][4] == 2985106497:
                            msg[-1].add_field(name=f"Rare Samples collected on {planetlist[task['values'][8]]}:",value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")
                    i += 1
                elif task['type'] == 3: #Value-Based
                    #Enemies
                    if task['values'][3] == 1379865898: #Bile Spewers
                        msg[-1].add_field(name='Bile Spewers:',value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")
                    elif task['values'][3] == 2058088313: #Warriors
                        msg[-1].add_field(name='Warriors:',value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")
                    elif task['values'][3] == 4211847317: #Illuminate
                        msg[-1].add_field(name='Illuminate:',value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")
                    elif task['values'][3] == 1405979473: #Voteless
                        msg[-1].add_field(name='Voteless :',value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")
                    elif task['values'][3] == 2664856027: #Shredder Tanks
                        msg[-1].add_field(name='Shredder Tanks:',value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")
                    elif task['values'][0] == 2 and task['values'][3] == 0: #Terminids
                        msg[-1].add_field(name='Terminids:',value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")
                    elif task['values'][0] == 3 and task['values'][3] == 0: #Automatons
                        msg[-1].add_field(name='Automatons:',value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")
                    elif task['values'][0] == 4 and task['values'][3] == 0: #Illuminate
                        msg[-1].add_field(name='Illuminate:',value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")
                    elif task['values'][3] == 2514244534: #Bile Titans
                        msg[-1].add_field(name='Bile Titans:',value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")
                    elif task['values'][3] == 793026793: #Shriekers
                        msg[-1].add_field(name='Shriekers:',value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")
                    elif task['values'][3] == 1046000873: #Impalers
                        msg[-1].add_field(name='Impalers:',value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")
                    elif task['values'][3] == 1153658728: #Factory Striders
                        msg[-1].add_field(name='Factory Striders:',value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")
                    elif task['values'][3] == 2880434041: #Fleshmobs
                        msg[-1].add_field(name='Fleshmobs:',value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")
                    elif task['values'][3] == 3097344451: #Leviathans
                        msg[-1].add_field(name='Leviathans:',value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")                                                                                
                    #Weapons
                    elif task['values'][5] == 1978117092: #Stalwart
                        msg[-1].add_field(name='Stalwart Kills:',value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")
                    elif task['values'][5] == 934703916: #Machine Gun
                        msg[-1].add_field(name='Machine Gun Kills:',value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")
                    elif task['values'][5] == 4038802832: #Machine Gun
                        msg[-1].add_field(name='Heavy Machine Gun Kills:',value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")
                    else: #Objective not yet defined
                        msg[-1].add_field(name='Progress:',value= f"{await commas(order['progress'][i])} / {await commas(task['values'][2])} - {abs(round((order['progress'][i]/task['values'][2])*100, 2))}%")
                    i += 1
                elif task['type'] == 7: #Mission Extractions
                    msg[-1].add_field(name= f'Extract from a successful mission against {factions[task["values"][0]]} {task["values"][2]} times:',
                                value= f'{str(await commas(order["progress"][i]))} / {str(await commas(task["values"][2]))} - {str(abs(round((order["progress"][i]/task["values"][2])*100, 2)))}%')
                elif task['type'] == 12: #Planet Defenses
                    if task['values'][1] == 2:
                        msg[-1].add_field(name='Defend ' + str(task['values'][0]) + ' Terminid Attack(s):',value= str(await commas(order['progress'][i])) + ' / ' + str(await commas(task['values'][0])) + ' - ' + str(abs(round((order['progress'][i]/task['values'][0])*100, 2))) + '%')
                    elif task['values'][1] == 3:
                        msg[-1].add_field(name='Defend ' + str(task['values'][0]) + ' Automaton Attack(s):',value= str(await commas(order['progress'][i])) + ' / ' + str(await commas(task['values'][0])) + ' - ' + str(abs(round((order['progress'][i]/task['values'][0])*100, 2))) + '%')
                    elif task['values'][1] == 4:
                        msg[-1].add_field(name='Defend ' + str(task['values'][0]) + ' Illuminate Attack(s):',value= str(await commas(order['progress'][i])) + ' / ' + str(await commas(task['values'][0])) + ' - ' + str(abs(round((order['progress'][i]/task['values'][0])*100, 2))) + '%')
                    else:
                        msg[-1].add_field(name='Defend ' + str(task['values'][0]) + ' Attack(s):',value= str(await commas(order['progress'][i])) + ' / ' + str(await commas(task['values'][0])) + ' - ' + str(abs(round((order['progress'][i]/task['values'][0])*100, 2))) + '%')
                    i += 1
                elif task['type'] == 9:
                    if task["values"][0] == 0:
                        msg[-1].add_field(name= f'Complete an Operation on {difficulty[task["values"][3]]} difficulty or higher:',
                                value= f'{str(await commas(order["progress"][i]))} / {str(await commas(task["values"][1]))} - {str(abs(round((order["progress"][i]/task["values"][1])*100, 2)))}%')
                    elif task["values"][0] == 3:
                        msg[-1].add_field(name= f'Complete Operations on {planetlist[task["values"][5]]}:',
                                value= f'{str(await commas(order["progress"][i]))} / {str(await commas(task["values"][1]))} - {str(abs(round((order["progress"][i]/task["values"][1])*100, 2)))}%')                        
                    else:
                        msg[-1].add_field(name= f'Complete an Operation against the {factions[task["values"][0]]} on {difficulty[task["values"][3]]} difficulty:',
                                value= f'{str(await commas(order["progress"][i]))} / {str(await commas(task["values"][1]))} - {str(abs(round((order["progress"][i]/task["values"][1])*100, 2)))}%')
                    i += 1
                elif task['type'] == 15: #
                    msg[-1].add_field(name='Liberate more planets than are lost.', value='Current Progress: ' + str(order['progress'][i]))
                    i += 1
                else: # Handling for new tasks
                    msg[-1].add_field(name='New Objective Detected',value='Collecting Information from Super Earth. Information will be available shortly.' )
                    i += 1
            except Exception as e:
                print('Error in Orders Task Parsing: ' + str(e))
                msg[-1].add_field(name= f'ERROR:', value= f'Collecting data from Super Earth')                
        if len(planetIDs) > 0: # Adds planet progress for tasks 11,13
            query = f"SELECT p.name, p.currentOwner, p.maxHealth, p.health FROM planets p WHERE p.index IN ({', '.join(planetIDs)})"
            results = await db_query('planets', query)
            for item in results:
                if item['currentOwner'] == 'Humans' and (item['health']/item['maxHealth']) == 1:
                    msg[-1].add_field(name= item['name'], value= '100% Liberated', inline=True)
                else:
                    msg[-1].add_field(name= item['name'], value= str(abs(round((item['health']/item['maxHealth'] -1)*100, 4))) + '% Liberated', inline= True)
        if i % 3 != 0: # adds blank fields to keep the embed looking nicer
            for x in range(int(round(i/3,0)), 3):
                msg[-1].add_field(name='', value='')
        msg[-1].add_field(name='Time Remaining', value= str(timeleft.days) + ' days ' + str(hoursleft) + ' hours ' + str(minsleft) + ' minutes', inline=False)
    return msg
    
async def planet(name):
    query= f'SELECT * FROM planets p WHERE p.name ="{name}"'
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
        elif item['currentOwner'] == 'Super Earth' and (item['health']/item['maxHealth']) == 1 and len(item['event']) > 0:
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
    autodef = [] #Automaton Defense campaigns
    bugdef = [] #Terminid Defense campaigns
    illudef= [] #Illuminate Defense campaigns
    autolib = [] #Automaton Liberation campaigns
    buglib = [] #Termind Liberation campaigns
    illulib = [] #Illuminate Liberation campaigns
    libcam = discord.Embed(title='**--Liberation Campaigns--**', type='rich')
    defcam = discord.Embed(title='**--Defense Campaigns--**', type='rich')
    results = await db_query('campaigns', 'SELECT * FROM campaigns c')
    for item in results:
        if item['planet']['currentOwner'] == 'Humans' and item['planet']['event'] is not None:
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
    #only add each section if it has extra content
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

 
