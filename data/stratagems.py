import requests
import json
from datetime import datetime
import os
import ast
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

#https://helldivers-2.github.io/api/docs/openapi/swagger-ui.html

load_dotenv()
db_uri = os.getenv('account_uri')
db_key = os.getenv('account_key')

client = CosmosClient(url=db_uri, credential=db_key)
database = client.get_database_client('democracy_bot')
container = database.get_container_client('stratagems')

url = "https://api-hellhub-collective.koyeb.app/api/stratagems"
payload={}
headers={}
response =  requests.request("GET", url, headers=headers).json()
stratcount = response['pagination']['total']
     
count = 0
for i in range(1, stratcount+1): #inserts new items into db
    stratagem = requests.request("GET", url+'/'+str(i), headers=headers).json()
    stratagem['data']['id'] = str(stratagem['data']['id'])
    container.upsert_item(stratagem['data'])
    count += 1      
print(str(count) + ' Records Updated')
