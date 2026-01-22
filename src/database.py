from azure.cosmos.aio import CosmosClient
from dotenv import dotenv_values

config = dotenv_values('./.env')
#load_dotenv(encoding="latin-1") #loads environment variables from .env file
db_uri = config['ACCOUNT_URI']
db_key = config['ACCOUNT_KEY']
db_client = config['DB_CLIENT']

# DATABASE FUNCTIONS
async def db_query(cont_name, db_query):
    async with CosmosClient(url=db_uri, credential=db_key) as qclient:
        database =  qclient.get_database_client(db_client)
        container = database.get_container_client(cont_name)
        results = [item async for item in container.query_items(query=db_query)]
        return results

async def db_upload(cont_name, data, type: int):
    async with CosmosClient(url=db_uri, credential=db_key) as upclient:
        await upclient.__aenter__()
        database =  upclient.get_database_client(db_client)
        container = database.get_container_client(cont_name)
        if cont_name == 'war_status':
            await container.upsert_item(data)
        else:
            for item in data:
                if type == 0:
                    await container.upsert_item(item)
                elif type == 1:
                    await container.upsert_item(item['planet'])

async def db_delete(cont_name, query):
    async with CosmosClient(url=db_uri, credential=db_key) as dbclient:
        database =  dbclient.get_database_client(db_client)
        container = database.get_container_client(cont_name)
        results = [item async for item in container.query_items(query=query)]
        count = 0
        for item in results:
            await container.delete_item(item, partition_key=item['name'])
            count += 1
        return count