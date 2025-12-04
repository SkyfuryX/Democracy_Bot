import requests, json
from datetime import datetime
import os
import ast
from azure.cosmos import CosmosClient
from dotenv import dotenv_values

#https://helldivers-2.github.io/api/docs/openapi/swagger-ui.html

config = dotenv_values('../.env')
data = {}
session = requests.Session()
header = ast.literal_eval(config['HEADER'])
session.headers.update(header)



config = dotenv_values('../.env')
#load_dotenv(encoding="latin-1") #loads environment variables from .env file
data = {}
session = requests.Session()
header = ast.literal_eval(config['HEADER'])
session.headers.update(header)

response = session.get("https://api.helldivers2.dev/api/v1/planets")
data = response.json()

planet_list=[] 
sector_list=[]
strat_list=[]   
for item in data:
    planet_list.append(item['name'].upper())
    if item['sector'] not in sector_list:
        sector_list.append(item['sector'])

# OLD
# url = "https://api-hellhub-collective.koyeb.app/api/stratagems"
# payload={}
# headers={}
# response =  requests.request("GET", url, headers=headers).json()

# response = session.get("https://api-hellhub-collective.koyeb.app/api/stratagems")
# stratcount = response['pagination']['total']
     
# count = 0
# for i in range(1, stratcount+1): 
#     stratagem = requests.request("GET", f"https://api-hellhub-collective.koyeb.app/api/stratagems/{i}")
#     strat_list.append(stratagem['data']['name'])
        
sector_list = ', '.join(sector_list)
planet_list = ', '.join(planet_list)
# strat_list = ', '.join(strat_list)
    
with open('../auto/planetlist.txt', 'w') as file:
    file.write(planet_list)
    file.close()
    
with open('../auto/sectorlist.txt', 'w') as file:
    file.write(sector_list)
    file.close()
    
# with open('../stratlist.txt', 'w') as file:
#     file.write(strat_list)
#     file.close()