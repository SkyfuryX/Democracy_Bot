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
headers = ast.literal_eval(os.getenv('header1'))

session = requests.Session()
session.headers.update(headers)
response = session.get("https://api.helldivers2.dev/api/v1/assignments")
data = response.json()

client = CosmosClient(url=db_uri, credential=db_key)
database = client.get_database_client('democracy_bot')
container = database.get_container_client('major_orders')

for item in data: #inserts new items into db
    item['id'] = str(item['id'])
    item['expiration'] = item['expiration'][0:10] + ' ' + item['expiration'][11:19] 
    container.upsert_item(item)
    
    
           
'''with open('assignments.txt', 'w') as file:
    json_string = json.dumps(data, default=lambda o: o.__dict__, sort_keys=True, indent=2)
    file.write(json_string)
    file.close()'''