from typing import Type
import os
import yaml
import logging


ENVIRON_KEYS = [
    'DARIUSDB_HOST',
    'DARIUSDB_USER',
    'DARIUSDB_PASSWD',
    'DARIUSDB_DB',
    'DARIUSDB_PORT',
]


class BaseConfig:
    ENV = 'development'
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    LOG_FILENAME = 'darius_backend.log'
    EVENT_LOG_FILENAME = 'darius_backend.event.log'
    DARIUSDB_HOST = ""
    DARIUSDB_USER = 'root'
    DARIUSDB_DB = 'dariusdb'
    DARIUSDB_PORT = 3306
    DARIUSDB_PASSWD = ''
    PORT = 8080
    CORS_ALLOW_ORIGIN = ['*']


ENV = os.environ.get('ENV', 'development')
usingProjectId = os.getenv('project_id', 'local')

ENV_CONFIGS = {
    'development': BaseConfig,
}


def get_config_from_environ(env=None) -> Type[BaseConfig]:
    env = env or os.environ.get('ENV', 'development')
    env_config = ENV_CONFIGS[env]

    for environ_key in ENVIRON_KEYS:
        if environ_key in os.environ:
            setattr(env_config, environ_key, os.environ[environ_key])

    return env_config


def overwrite_config_from_yaml(env_config: Type[BaseConfig]) -> Type[BaseConfig]:
    new_config = env_config
    yaml_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config/config.yaml')
    try:
        new_config = _read_yaml(new_config, yaml_file_path)
    except (IOError, OSError):
        logging.exception("")
    return new_config


def _read_yaml(new_config: Type[BaseConfig], yaml_file_path: str) -> Type[BaseConfig]:
    with open(yaml_file_path) as yaml_file:
        data = yaml.safe_load(yaml_file)
        for key in data:
            if key == 'ENV':
                os.environ[key] = data[key]
                new_config = get_config_from_environ(data[key])
            elif key.isupper():
                setattr(new_config, key, data[key])
    return new_config


def get_app_config() -> dict:
    env_config = get_config_from_environ()
    obj_conf = overwrite_config_from_yaml(env_config)
    dict_conf = {}

    for key in dir(obj_conf):
        if not key.startswith("_"):
            dict_conf[key] = getattr(obj_conf, key)

    if usingProjectId != "local":
        firestore_conf = get_config_from_firestore()
        dict_conf.update(firestore_conf)
    return dict_conf


def get_config_from_firestore():
    from firebase_admin import firestore
    db = firestore.Client()
    sql_config = db.collection("config").document("sql").get().to_dict()
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
