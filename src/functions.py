import math, discord, copy, json, asyncio
from datetime import datetime as dt, timezone
from dotenv import dotenv_values
from classes import Planet, Stats
from database import db_query


config = dotenv_values('./.env')

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
def add_commas(number) -> str: 
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
async def war() -> discord.Embed:
    query='SELECT * FROM war_status w ORDER BY w._ts DESC OFFSET 0 LIMIT 1'
    results = await db_query('war_status', query)
    
    war = Stats.model_validate(results[0])
    msg = discord.Embed(title='**--Galactic War--**', type='rich')
    msg.add_field(name='Helldivers Active:', value=add_commas(war.player_count))
    msg.add_field(name='Successful Missions:', value=add_commas(war.missions_won))
    msg.add_field(name='Failed Missions:', value=add_commas(war.missions_lost))
    msg.add_field(name='Bullets Fired:', value=add_commas(war.bullets_fired))
    msg.add_field(name='Helldivers KIA:', value=add_commas(war.deaths))
    msg.add_field(name='Accidentals:', value=add_commas(war.friendlies))
    msg.add_field(name='', value='', inline=False)
    msg.add_field(name='-Enemies Liberated-', value='',inline=False)
    msg.add_field(name='Automatons:', value=add_commas(war.automaton_kills))
    msg.add_field(name='Terminids:', value=add_commas(war.terminid_kills))
    msg.add_field(name='Illuminate:', value=add_commas(war.illuminate_kills))
    return msg

#ValueTypes - 1:Faction, 3:Amount, 4:Enemy Type,  12: Planet
async def orders(session) -> list[discord.Embed]:
    async with session.get("https://api.helldivers2.dev/api/v1/assignments") as response:
        data = await response.json()
    if len(data) == 0:
        msg = [discord.Embed(title='-Awaiting Orders from Super Earth-', type='rich')]
        return msg

    query= f'SELECT o.title, o.briefing, o.description, o.expiration, o.tasks, o.progress FROM major_orders o ORDER BY o._ts DESC OFFSET 0 LIMIT {len(data)}'
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
        for i, task in enumerate(order['tasks']): # Handles task types 2,3,7,9,11,12,13,15
            try:
                values, types = task['values'], task['valueTypes']
                match task['type']:
                    case 2: # Sample Collections
                        match values[8]: 
                            case 0: # Faction-Specific
                                match values[4]:
                                    case 3992382197:
                                        msg[-1].add_field(name=f'Common Samples collected from any planet controlled by {factions[values[0]]}:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%") 
                                    case 2985106497:
                                        msg[-1].add_field(name=f'Rare Samples collected from any planet controlled by {factions[values[0]]}:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")   
                            case _:
                                match values[4]:
                                    case 3992382197:
                                        msg[-1].add_field(name=f"Common Samples collected on {planetlist[values[8]]}:",value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")                                        
                                    case 2985106497:
                                        msg[-1].add_field(name=f"Rare Samples collected on {planetlist[values[8]]}:",value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")
                    case 3: #Value-Based
                        match values[3]: #Defeat Specific Enemies
                            case 0 if values[0] in (2,3,4):
                                match values[0]:
                                    case 2: #Terminids
                                        msg[-1].add_field(name='Terminids:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")        
                                    case 3: #Automatons
                                        msg[-1].add_field(name='Automatons:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")                                        
                                    case 4: #Illuminate
                                        msg[-1].add_field(name='Illuminate:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")
                            case 1379865898: #Bile Spewers
                                msg[-1].add_field(name='Bile Spewers:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")
                            case 2058088313: #Warriors
                                msg[-1].add_field(name='Warriors:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")
                            case 4211847317: #Illuminate
                                msg[-1].add_field(name='Illuminate:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")
                            case 1405979473: #Voteless
                                msg[-1].add_field(name='Voteless :',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")
                            case 2664856027: #Shredder Tanks
                                msg[-1].add_field(name='Shredder Tanks:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")
                            case 2514244534: #Bile Titans
                                msg[-1].add_field(name='Bile Titans:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")
                            case 793026793: #Shriekers
                                msg[-1].add_field(name='Shriekers:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")
                            case 1046000873: #Impalers
                                msg[-1].add_field(name='Impalers:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")
                            case 1153658728: #Factory Striders
                                msg[-1].add_field(name='Factory Striders:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")
                            case 2880434041: #Fleshmobs
                                msg[-1].add_field(name='Fleshmobs:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")
                            case 3097344451: #Leviathans
                                msg[-1].add_field(name='Leviathans:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")                                                                                
                            case 2651633799: #Chargers
                                msg[-1].add_field(name='Chargers:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")                                                                                                    
                            case 23741406: #Radicals
                                msg[-1].add_field(name='Radicals:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")
                            case 1371180916: #Agitators
                                msg[-1].add_field(name='Agitators:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")
                            case _:
                                match values[5]: #Kills using specific weapons
                                    case 1978117092: #Stalwart
                                        msg[-1].add_field(name='Stalwart Kills:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")
                                    case 934703916: #Machine Gun
                                        msg[-1].add_field(name='Machine Gun Kills:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")
                                    case 4038802832: #Heavy Machine Gun
                                        msg[-1].add_field(name='Heavy Machine Gun Kills:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")
                                    case _: #Objective not yet defined
                                        msg[-1].add_field(name='Progress:',value= f"{add_commas(order['progress'][i])} / {add_commas(values[2])} - {abs(round((order['progress'][i]/values[2])*100, 2))}%")
                    case 7: #Mission Extractions
                        msg[-1].add_field(name= f'Extract from a successful mission against {factions[values[0]]} {values[2]} times:',
                            value= f'{add_commas(order["progress"][i])} / {add_commas(values[2])} - {abs(round((order["progress"][i]/values[2])*100, 2))}%')
                    case 9:
                        match values[-1]:
                            case 0:
                                msg[-1].add_field(name= f'Complete an Operation against the {factions[values[0]]} {add_commas(values[types.index(3)])} times.',
                                    value= f"{add_commas(order['progress'][i])} / {add_commas(values[1])} - {abs(round((order['progress'][i]/values[1])*100, 2))}%")                                 
                            case _:
                                msg[-1].add_field(name= f'Complete Operations against the {factions[values[0]]} on {planetlist[values[-1]]} {add_commas(values[types.index(3)])} times.',
                                    value= f"{add_commas(order['progress'][i])} / {add_commas(values[types.index(3)])} - {abs(round((order['progress'][i]/values[types.index(3)])*100, 2))}%") 
                    case 11 | 13: #Liberate/Defend specific planet
                        if values[2] not in planetIDs:
                            planetIDs.append(f"{values[2]}")
                    case 12: #Planet Defenses
                        match values[1]:
                            case 2:
                                msg[-1].add_field(name='Defend ' + str(values[0]) + ' Terminid Attack(s):',value= str(add_commas(order['progress'][i])) + ' / ' + str(add_commas(values[0])) + ' - ' + str(abs(round((order['progress'][i]/values[0])*100, 2))) + '%')
                            case 3:
                                msg[-1].add_field(name='Defend ' + str(values[0]) + ' Automaton Attack(s):',value= str(add_commas(order['progress'][i])) + ' / ' + str(add_commas(values[0])) + ' - ' + str(abs(round((order['progress'][i]/values[0])*100, 2))) + '%')
                            case 4:
                                msg[-1].add_field(name='Defend ' + str(values[0]) + ' Illuminate Attack(s):',value= str(add_commas(order['progress'][i])) + ' / ' + str(add_commas(values[0])) + ' - ' + str(abs(round((order['progress'][i]/values[0])*100, 2))) + '%')
                            case _:
                                msg[-1].add_field(name='Defend ' + str(values[0]) + ' Attack(s):',value= str(add_commas(order['progress'][i])) + ' / ' + str(add_commas(values[0])) + ' - ' + str(abs(round((order['progress'][i]/values[0])*100, 2))) + '%')
                    case 15: 
                        msg[-1].add_field(name='Liberate more planets than are lost.', value='Current Progress: ' + str(order['progress'][i])) 
                    case _: #Handling for new tasks
                        msg[-1].add_field(name='New Objective Detected',value='Collecting Information from Super Earth. Information will be available shortly.' ) 
            except Exception as e:
                print('Error in Orders Task Parsing: ' + str(e))
                msg[-1].add_field(name= f'ERROR:', value= f'Collecting data from Super Earth') 
                               
        # TODO - Make into get_planets function
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
        msg[-1].add_field(name='Time Remaining:', value= f"{timeleft.days} days {hoursleft} hours {minsleft} minutes", inline=False)
    return msg
    
async def planet(name) -> discord.Embed:
    try:
        query= f'SELECT * FROM planets p WHERE p.name ="{name}"'
        results = await db_query('planets', query)
        if not results:
            msg = discord.Embed(title='-Planet Not Found-', type='rich')
            return msg 
        
        planet = Planet.model_validate(results[0])
        if planet.current_owner == 'Humans':
            planet.current_owner = 'Super Earth'
        
        if planet.current_owner == 'Super Earth' and planet.event is None:
            msg = discord.Embed(title=f'**--{planet.name}--**', description= f'{planet.current_owner} Control\n100% Liberated', type='rich')
        elif planet.current_owner == 'Super Earth' and planet.event:
            event = planet.event
            msg = discord.Embed(title=f'**--{planet.name}--**', description= f'{planet.current_owner} Control\n{abs(round((event.currentHealth() -1)*100, 4))}% Defended', type='rich')
        else:
            msg = discord.Embed(title=f'**--{planet.name}--**', description= f'{planet.current_owner} Control\n{abs(round((planet.currentHealth() -1)*100, 4))}% Liberated', type='rich')
        
        msg.add_field(name='Sector:', value=planet.sector)
        msg.add_field(name='Biome and Hazards:', value= f'{planet.biome.name} - {', '.join(hazard.name for hazard in planet.hazards)}')

        if len(planet.waypoints) > 0:
            msg.add_field(name='Supply Lines:', value=', '.join(planetlist[x] for x in planet.waypoints))
        else:
            msg.add_field(name ='', value='')
            
        stats = planet.statistics
        msg.add_field(name='----------------------------------', value='', inline= False)
        msg.add_field(name='Helldivers Active:', value=add_commas(stats.player_count))
        msg.add_field(name='Bullets Fired:', value=add_commas(stats.bullets_fired))
        msg.add_field(name='', value='')
        msg.add_field(name='Helldivers KIA:', value=add_commas(stats.deaths))
        msg.add_field(name='Enemies Liberated:', value=add_commas( stats.killsCombined()))
        msg.add_field(name='', value='')
        return msg

    except Exception as e:
        print(f"Error processing Planet lookup: {e}")
        msg = discord.Embed(title='-Planet Not Found-', type='rich')
        return msg 
    

async def campaigns() -> tuple[discord.Embed, discord.Embed]:
    defenses: dict[str,list[str]] = { # Defense Campaigns by faction
        "Automaton": [],
        "Terminids": [],
        "Illuminate": [],
    }
    offenses = copy.deepcopy(defenses) # Offense Campaigns by faction

    libcampaigns = discord.Embed(title='**--Liberation Campaigns--**', type='rich')
    defcampaigns = discord.Embed(title='**--Defense Campaigns--**', type='rich')

    raw_results = await db_query('campaigns', 'SELECT * FROM campaigns c')
    results = list(raw_results)

    for campaign in results:
        try:
            planet = Planet.model_validate(campaign['planet'])
                        
            if planet.current_owner == 'Humans' and planet.event is not None:
                health = abs(round((planet.event.currentHealth() - 1) * 100, 4))
                defenses[planet.event.faction].append(f'{planet.name} {health}%')
            elif planet.current_owner != 'Humans':
                health = abs(round((planet.currentHealth() - 1) * 100, 4))
                offenses[planet.current_owner].append(f'{planet.name} {health}%')
        except Exception as e:
            print(f"Error processing campaigns: {e}")
            continue
            
    for key, val in offenses.items():
        if val:
            libcampaigns.add_field(name= f'{key} Front:', value = ', '.join(val),inline=False)
        
    for key, val in defenses.items():
        if val:
            defcampaigns.add_field(name= f'{key} Front:', value = ', '.join(val),inline=False)

    return libcampaigns, defcampaigns

async def stratagems(name) -> discord.Embed:
    emojikeys = {'up': ':arrow_up:','down':':arrow_down:','left':':arrow_left:','right':':arrow_right:'}
    query = f'SELECT * FROM stratagems s WHERE CONTAINS(s.name, "{name}", true) OFFSET 0 LIMIT 1'
    results = await db_query('stratagems', query)
    if not results:
        msg = discord.Embed(title='-Stratagem Not Found-', type='rich')
        return msg
    
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