from tortoise import Tortoise


async def start_db_connection(app_config, models_path="main.src.models"):
    connect_config = {
        "default": {
            "engine": "tortoise.backends.mysql",
            "credentials": {
                "host": app_config['DARIUSDB_HOST'],
                "user": app_config['DARIUSDB_USER'],
                "password": app_config['DARIUSDB_PASSWD'],
                "database": app_config['DARIUSDB_DB'],
                "port": app_config['DARIUSDB_PORT']
            }
        },
    }
    model_config = {"darius": {"models": [models_path], "default_connection": "default"}}

    await Tortoise.init(
        {
            "connections": connect_config,
            "apps": model_config
        }
    )


async def close_db_connection():
    await Tortoise.close_connections()
