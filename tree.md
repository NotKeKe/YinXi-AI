.
├── .dockerignore
├── Dockerfile
├── LICENSE
├── README.md
├── main.py
├── pyproject.toml
├── requirements.txt
├── setting.json.example
├── think.md
├── think2.md
├── uv.lock
├── assets
│   └── botself.png
├── cmds
│   ├── ai_channel_two.py
│   ├── ai_three.py
│   ├── bot_info_help.py
│   ├── error.py
│   ├── load.py
│   ├── system_prompt.py
│   ├── total_stats.py
│   ├── translator.py
│   ├── vector_data.py
│   ├── yinxi.py
│   ├── ai_chat
│   │   ├── chat
│   │   │   ├── __init__.py
│   │   │   ├── chat.py
│   │   │   ├── gener_title.py
│   │   │   └── translate.py
│   │   ├── data
│   │   │   └── prompts
│   │   │       ├── base_system_prompt.md
│   │   │       ├── chat_human_prompt_1.md
│   │   │       ├── chat_human_prompt_2.md
│   │   │       ├── chat_human_prompt_own_products.md
│   │   │       ├── emoji_translator.md
│   │   │       ├── idea_clarifier.md
│   │   │       ├── long_term_memory.md
│   │   │       ├── self_growth_chatting.md
│   │   │       ├── self_growth_learning.md
│   │   │       ├── self_growth_resting.md
│   │   │       ├── story_teller.md
│   │   │       └── summarize_history_system_prompt.md
│   │   ├── on_msg
│   │   │   ├── __init__.py
│   │   │   ├── ai_channel.py
│   │   │   ├── chat_human.py
│   │   │   ├── yinxi.py
│   │   │   └── self_growth
│   │   │       ├── __init__.py
│   │   │       ├── main.py
│   │   │       └── datacls
│   │   │           ├── __init__.py
│   │   │           ├── main.py
│   │   │           ├── mood.py
│   │   │           └── types.py
│   │   ├── tools
│   │   │   ├── __init__.py
│   │   │   ├── description.json
│   │   │   ├── map.py
│   │   │   ├── ai_func
│   │   │   │   ├── __init__.py
│   │   │   │   ├── image_gen.py
│   │   │   │   └── video_gen.py
│   │   │   ├── chat_human_tools
│   │   │   │   ├── __init__.py
│   │   │   │   ├── description.json
│   │   │   │   ├── map.py
│   │   │   │   ├── browser
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── close_page.py
│   │   │   │   │   ├── get_web_elements.py
│   │   │   │   │   └── goto_page.py
│   │   │   │   ├── file
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── read.py
│   │   │   │   │   └── write.py
│   │   │   │   ├── history_edit
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── add_prompt.py
│   │   │   │   │   ├── self_database.py
│   │   │   │   │   └── switch_mode.py
│   │   │   │   ├── mood
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── change_mood.py
│   │   │   │   │   └── get_mood.py
│   │   │   │   └── to_user
│   │   │   │       ├── __init__.py
│   │   │   │       ├── call_keke.py
│   │   │   │       ├── get_havent_reply_msgs.py
│   │   │   │       ├── ignore_msg.py
│   │   │   │       ├── reply_message.py
│   │   │   │       └── send_to_channel.py
│   │   │   └── func
│   │   │       ├── __init__.py
│   │   │       ├── calculate.py
│   │   │       ├── list_available_commands.py
│   │   │       ├── long_term_memory.py
│   │   │       ├── web_fetcher.py
│   │   │       ├── web_search.py
│   │   │       └── wiki_search.py
│   │   └── utils
│   │       ├── __init__.py
│   │       ├── auto_complete.py
│   │       ├── button.py
│   │       ├── client.py
│   │       ├── config.py
│   │       ├── model.py
│   │       ├── model_select.py
│   │       ├── process_tag.py
│   │       └── prompt.py
│   └── vector
│       ├── call
│       │   ├── __init__.py
│       │   ├── call.py
│       │   └── user_long_term_memory.py
│       ├── database
│       └── utils
│           ├── __init__.py
│           ├── autocomplete.py
│           ├── check_alive.py
│           ├── client.py
│           ├── config.py
│           └── split_str.py
├── core
│   ├── classes.py
│   ├── functions.py
│   ├── mock_interaction.py
│   ├── mongodb_clients.py
│   ├── qdrant.py
│   ├── setup_log.py
│   ├── sqlite.py
│   ├── translator.py
│   ├── chat_human
│   │   ├── manage_browser.py
│   │   └── prompt.py
│   └── locales
│       ├── en-US.json
│       ├── help_doc.md
│       ├── prompt1_chat_history.md
│       ├── prompt1.md
│       ├── prompt2_chat_history.md
│       ├── prompt2.md
│       ├── prompt3_chat_history.md
│       ├── prompt3.md
│       ├── zh-CN.json
│       └── zh-TW.json
└── data
    └── mongodb
        └── backup.sh