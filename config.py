# coding: utf-8

"""
Конфиг для flask, скорее всего, без него совсем не получится
"""

import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    """
    Конфиг
    """
    DEBUG = True
    TESTING = True
    CSRF_ENABLED = True
    # https://stackoverflow.com/questions/14853694/python-jsonify-dictionary-in-utf-8
    JSON_AS_ASCII = False
    # python3.x binascii.hexlify(os.urandom(24))
    SECRET_KEY = 'd17c571102250cec991fb6393e417d767cdee3ca537cf43a'
    DATE_FROM = '1900-01-01'
    DATE_TO = '2050-12-31'
    TMP_DIR = 'tmp/'
    CACHE_MAXSIZE = os.environ.get("CACHE_MAXSIZE")
    CACHE_TTL = os.environ.get("CACHE_TTL")    
    USING_AUTH = os.environ.get("USING_AUTH")
    CONSUL_NAME = os.environ.get("SERVICE_NAME")
    DB_NAME = os.environ.get("DB_NAME")


class ProductionConfig(Config):
    """
    Конфиг для продакшена
    """
    DEBUG = False


class StagingConfig(Config):
    """
    Конфиг для "предпремьерного показа"
    """
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    """
    Конфиг для разработки
    """
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    """
    Конфиг для теста
    """
    TESTING = True
