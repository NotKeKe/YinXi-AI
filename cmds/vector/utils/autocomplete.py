from discord import Interaction
from discord.app_commands import Choice
from typing import List
from core.functions import mongo_db_client

user_custom_data_db = mongo_db_client['user_custom_data']

async def custom_database_titles(inter: Interaction, current: str) -> List[Choice[str]]:
    collection = user_custom_data_db[str(inter.user.id)]

    async for item in collection.find():
        item.get('title', '')

    titles = [item.get('title') async for item in collection.find() if item.get('title')]

    if current:
        titles = [t for t in titles if t.lower().strip() in current.strip().lower()]

    return [Choice(name=t, value=t) for t in titles]