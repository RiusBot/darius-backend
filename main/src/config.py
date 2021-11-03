from typing import Type
import os
import yaml


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
    DARIUSDB_DB = 'dariusdb'
    DARIUSDB_PORT = 3306
    PORT = 8080


ENV = os.environ.get('ENV', 'development')

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
    yaml_file_path = 'main/config/config.yaml'
    try:
        new_config = _read_yaml(new_config, yaml_file_path)
    except (IOError, OSError):
        pass
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
        dict_conf[key] = getattr(obj_conf, key)
    return dict_conf


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
