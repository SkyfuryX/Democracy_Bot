import requests, json
from datetime import datetime
import os
import ast
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

#https://helldivers-2.github.io/api/docs/openapi/swagger-ui.html

load_dotenv()
headers = ast.literal_eval(os.getenv('header1'))

session = requests.Session()
session.headers.update(headers)
response = session.get("https://api.helldivers2.dev/api/v1/planets")
data = response.json()

planet_list=[] 
sector_list=[]
strat_list=[]   
for item in data:
    planet_list.append(item['name'])
    if item['sector'] not in sector_list:
        sector_list.append(item['sector'])
        
url = "https://api-hellhub-collective.koyeb.app/api/stratagems"
payload={}
headers={}
response =  requests.request("GET", url, headers=headers).json()
stratcount = response['pagination']['total']
     
count = 0
for i in range(1, stratcount+1): 
    stratagem = requests.request("GET", url+'/'+str(i), headers=headers).json()
    strat_list.append(stratagem['data']['name'])
        
sector_list = ', '.join(sector_list)
planet_list = ', '.join(planet_list)
strat_list = ', '.join(strat_list)
    
with open('planetlist.txt', 'w') as file:
    file.write(planet_list)
    file.close()
    
with open('sectorlist.txt', 'w') as file:
    file.write(sector_list)
    file.close()
    
with open('stratlist.txt', 'w') as file:
    file.write(strat_list)
    file.close()