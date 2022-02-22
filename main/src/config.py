from typing import Type
import os
import yaml
import logging


class BaseConfig:
    DEBUG = True
    LOGGING_LEVEL = 'DEBUG'
    LOG_FILENAME = 'darius_backend.log'
    EVENT_LOG_FILENAME = 'darius_backend.event.log'
    DARIUSDB_HOST = ""
    DARIUSDB_USER = 'root'
    DARIUSDB_DB = 'dariusdb'
    DARIUSDB_PORT = 3306
    DARIUSDB_PASSWD = ''
    PORT = 8080
    RECAPTCHA_VALID_ACTIONS = ['LOGIN', 'REGISTER']

class ProdConfig(BaseConfig):
    ENV = 'prod'
    LOGGING_LEVEL = 'INFO'
    CORS_ALLOW_ORIGIN = ['*']
    RECAPTCHA_SITE_KEY = '6Ldlk7UdAAAAAGIchxvhR5nUajO6aPE0xlZ7h-dg'  # TODO, need updated after register new key
    G_CLOUD_PROJECT_ID = 'darius-332003'  # TODO, need updated

class DevConfig(BaseConfig):
    ENV = 'dev'
    LOGGING_LEVEL = 'DEBUG'
    CORS_ALLOW_ORIGIN = ['*']
    RECAPTCHA_SITE_KEY = '6Ldlk7UdAAAAAGIchxvhR5nUajO6aPE0xlZ7h-dg'
    G_CLOUD_PROJECT_ID = 'darius-332003'


usingProjectId = os.getenv('project_id', 'local')

ENV_CONFIGS = {
    'dev': DevConfig,
    'prod': ProdConfig
}

def get_config_from_yaml() -> Type[BaseConfig]:
    yaml_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config/config.yaml')
    try:
        yaml_conf = _read_yaml(yaml_file_path)
    except (IOError, OSError):
        logging.exception("")
    return yaml_conf


def _read_yaml(yaml_file_path: str) -> Type[BaseConfig]:
    yaml_conf = {}
    with open(yaml_file_path) as yaml_file:
        data = yaml.safe_load(yaml_file)
        for key in data:
            if key.isupper():
                yaml_conf[key] = data[key]
    return yaml_conf


def get_app_config() -> dict:
    if usingProjectId == "local":
        secret_conf = get_config_from_yaml()
    else:
        secret_conf = get_config_from_firestore()
    env = secret_conf.get('ENV', 'dev')
    env_conf = ENV_CONFIGS[env]
    dict_conf = {}
    for key in dir(env_conf):
        dict_conf[key] = getattr(env_conf, key)
    dict_conf.update(secret_conf)
    return dict_conf


def get_config_from_firestore():
    from firebase_admin import firestore
    db = firestore.Client()
    sql_config = db.collection("config").document("darius-backend").get().to_dict()
    return sql_config


app_config = get_app_config()


def generate_db_config(app_config, models_path="main.src.models") -> dict:
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

    return {
        "connections": connect_config,
        "apps": model_config
    }


db_config = generate_db_config(app_config)


def get_logging_level():
    return os.getenv("LOGGING_LEVEL", "INFO")


def configure_logging():
    logging_level = get_logging_level().upper()
    numeric_level = getattr(logging, logging_level, None)

    if not isinstance(numeric_level, int):
        raise Exception(f"Invalid log level: {numeric_level}")

    logging.basicConfig(
        level=numeric_level,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="[%(asctime)s] [%(levelname)s] [%(module)s]: #%(funcName)s @%(lineno)d: %(message)s",
        # format="[%(asctime)s] [%(process)s] [%(levelname)s] [%(module)s]: #%(funcName)s @%(lineno)d: %(message)s",
    )
    logging.info(f"Logging level: {logging_level}")
