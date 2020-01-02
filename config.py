
downstreams = {
    "idiom_qa": "http://172.18.32.23:8100/idiom_qa",
    "idiom_check": "http://172.18.32.23:8100/idiom",
    "idiom_chat": "http://172.18.32.88:8870/proverb",
    "poetry_chat": "http://172.18.32.88:5819/shici_chat_v1",
    "poetry_qa": "http://172.18.32.23:8300/poetry_qa",
}

context_redis = {
    "host": "localhost",
    "port": 8379,
    "db": 1,
    "decode_responses": True,
}

context_prefix = "d-ctx-"
