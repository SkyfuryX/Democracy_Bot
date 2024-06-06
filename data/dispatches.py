import requests
import json
from datetime import datetime
import os
import ast
from dotenv import load_dotenv
from azure.cosmos import CosmosClient
import re

load_dotenv() #load keys
db_uri = os.getenv('account_uri')
db_key = os.getenv('account_key')
headers = ast.literal_eval(os.getenv('header1'))

#create db connection
client = CosmosClient(url=db_uri, credential=db_key)
database_name = 'democracy_bot'
database = client.get_database_client(database_name)
container_name = 'dispatch'
container = database.get_container_client(container_name)

session = requests.Session() #connect to api
session.headers.update(headers)
response = session.get("https://api.helldivers2.dev//api/v1/dispatches")
data = response.json()

for item in data: #format for the database
    item['id'] = str(item['id'])
    item['message'] = re.sub('<i=[0-9]>|</i>', '**', item['message'])

for item in container.query_items( #queries for last uploaded id
        query='SELECT d.id as id FROM dispatch d ORDER BY d.id DESC OFFSET 0 LIMIT 1',
        enable_cross_partition_query=True):
    id = int(item['id'])

count = 0
for item in data: #inserts new items into db
    if int(item['id']) > id:
        container.upsert_item(item)
        count += 1      
print(str(count) + ' Records Updated')
