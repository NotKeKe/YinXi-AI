from core.functions import mongo_db_client

class MongoDBNames:
    aichat_available_models = 'aichat_available_models'
    aichat_chat_history = 'aichat_chat_history'
    bot_collect_stats = 'bot_collect_stats'
    user_custom_data = 'user_custom_data'
    system_prompt = 'system_prompt'

class MongoDB_DB:
    aichat_available_models = mongo_db_client['aichat_available_models']
    aichat_chat_history = mongo_db_client['aichat_chat_history']
    bot_collect_stats = mongo_db_client['bot_collect_stats']
    chat_human_setting = mongo_db_client['chat_human_setting']
    user_custom_data = mongo_db_client['user_custom_data']
    system_prompt = mongo_db_client['system_prompt']
    user_long_term_memory = mongo_db_client['user_long_term_memory']
    aichannel_chat_history = mongo_db_client['aichannel_chat_history']

    self_growth_history = mongo_db_client['self_growth_history']