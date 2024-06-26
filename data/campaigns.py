import requests
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

client = CosmosClient(url=db_uri, credential=db_key)
database_name = 'democracy_bot'
database = client.get_database_client(database_name)
container_name = 'campaigns'
container = database.get_container_client(container_name)

session = requests.Session()
session.headers.update(headers)
response = session.get("https://api.helldivers2.dev//api/v1/campaigns")
data = response.json()

count = 0
for item in data: #inserts new items into db
    item['id'] = str(item['id'])
    item['name'] = item['planet']['name']
    count += 1 
    container.upsert_item(item)
print(str(count) + ' Active Campaigns Updated')
        
#data = {}
#gets only the highest ID for db key since the data doesnt have one itself
'''for item in container.query_items(
        query='SELECT c.id as id FROM war_status c ORDER BY c.id DESC OFFSET 0 LIMIT 1',
        enable_cross_partition_query=True):
    data.update(item)'''

#test dumping to file
'''with open('campaigns.txt', 'w') as file:
    json_string = json.dumps(data, default=lambda o: o.__dict__, sort_keys=True, indent=2)
    file.write(json_string)
    file.close()'''


