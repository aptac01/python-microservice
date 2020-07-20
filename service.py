#!env/bin/python
# coding: utf-8

"""
Исполняемый файл для управления сервисом
Черновик, будет переделываться
"""


import os
import sys
import json
import subprocess
from service_manager_lib import MyLogger

cnfg = os.path.dirname(os.path.abspath(__file__))
print(__file__)
print(cnfg)
config_filename = f'{cnfg}/config.json'

with open(config_filename) as f:
    config = json.load(f)

if config is None:
    # todo: заменить на MyLogger
    print('couldnt find config file! exiting')
    sys.exit(1)

# используем значения из конфига повторно, чтобы не писать сочинение при каждом деплое
config_parts = {
    'uwsgi_exec':               config['env_directory'] + '/bin/uwsgi',
    'env_python_exec':          config['env_directory'] + '/bin/python',
    'pid_file':                 config['api_directory'] + '/tmp/example_api-master.pid',
    'prometheus_multiproc_dir': config['api_directory'] + '/pfe_multiprocess_tmp',
    'TMP_DIR':                  config['api_directory'] + '/tmp/',

    # путь до nohup.out
    'nohup_out_log':            config['api_directory'] + '/log/nohup.out'
}
config = {**config, **config_parts}
print(config)
#sys.exit(0)

# вот так обновляем конфиг flask'a
# app.config.update(config)

config_file = open(config_filename, 'r')

# contents = env_vars_w.read()
# nohup_logger.log(contents)

nohup_file = open('/home/aptac01/python_microservice/log/nohup.out', 'a+')

nohup_logger = MyLogger(nohup_file)

color_scheme_service = {
    'color_pieces': [
        {
            'color_front': 'red',
            'color_back': 'green',
            'colored_text': '123',
        },
        {
            'color_front': 'magenta',
            'color_back': 'white',
            'colored_text': '321',
        },
        {
            'color_front': 'cyan',
            'color_back': 'black',
            'colored_text': '000',
        },
        {
            'color_front': 'yellow',
            'colored_text': r'config file is at [a-zA-Zа-яА-Я\.\\\/_]+',
        }
    ]
}

nohup_logger.log('----------------- Service managing operation start -----------------')
nohup_logger.log(f'running from {os.path.dirname(__file__)}', color_scheme_service)

nohup_logger.log(f'config file is at {config_filename}', color_scheme_service)

# вся вот эта хрень будет скрыта от пользователя, если все проходит штатно
# ---------------------
# если cd задать неправильный путь для перехода - subprocess.run выкидывает exception (т.е. его надо ловить)
# если подпроцесс завершился сам - exception (если он был) не выкидывается.
# про другие такие команды не знаю, надо тестить
#   возможно, выкидываются исключения от операционной системы или интерпретатора (bash и т.п.)
result = subprocess.run(['kill', '-h'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

# nohup_logger.log(f'{result.stdout.decode("utf8")}')
if result.returncode != 0:
    nohup_logger.log(f'The exit code is {result.returncode}')
if result.stderr not in (None, '', 0, b''):
    nohup_logger.log(f'This is what happened: {result.stderr.decode("utf8")}')
# ---------------------

result = subprocess.run(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
if result.returncode == 0:
    nohup_logger.log(f'Current hash in GIT: {result.stdout.decode("utf8")}')
else:
    nohup_logger.log(f'something went wrong with git, check it out:\n---\n{result.stderr.decode("utf8")}\n===')

nohup_logger.log('321   dffddf ', color_scheme_service)
nohup_logger.log('000 fgfd', color_scheme_service)
nohup_logger.log('================= Service managing operation finish ================')
