#!env/bin/python
# coding: utf-8

"""
Исполняемый файл для управления сервисом
Черновик, будет переделываться
"""


import os
import sys
import json
import yaml
import subprocess
from service_manager_lib import MyLogger

cnfg = os.path.dirname(os.path.abspath(__file__))
#print(__file__)
config_filename = f'{cnfg}/config.yaml'


with open(config_filename, 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

        # вот тут config имеет тип dict

if config is None:
    # todo: заменить на MyLogger
    print('couldnt find config file! exiting')
    sys.exit(1)

# todo заменить вот это на то, что описано по ссылке https://circleci.com/docs/2.0/writing-yaml/#anchors-and-aliases
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
#print(config)
# sys.exit(0)

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
            'colored_text': r'config file is at [a-zA-Zа-яА-Я\.\\\/_0-1]+',
        },
        {
            'color_front': 'yellow',
            'colored_text': r'running from :[a-zA-Zа-яА-Я\.\\\/_0-1]+',
        }
    ]
}

nohup_logger.log('----------------- Service managing operation start -----------------')
nohup_logger.log(f'running from :{cnfg}', color_scheme_service)

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

# ----------------------------------------------------
# WARNING!!! GOVNOKOD-FREE TERRITORY
# ниже этого сообщения может быть только тот код, который попадет в финальную(т.е. релизную) версию файла
# всякую белиберду сюда не пихать
# ----------------------------------------------------
# https://docs.python.org/3.3/library/argparse.html#action - документация по argparse
from argparse import ArgumentParser
import argparse
import textwrap

# noinspection PyTypeChecker
parser = ArgumentParser(prog=f'{__file__}',
                        usage=f'<your_python_exec> {__file__}  -a <action> [-c (1|0)] [-r (1|0)] [-v]',
                        formatter_class=argparse.RawDescriptionHelpFormatter,
                        description=textwrap.dedent('''
                        The idea behind using this script is to keep it as simple as possible deploying and 
                            administrating python microservices written using Flask and launched through uwsgi by 
                            reducing all control manipulations to one file, and all settings in one config. 
                            
                        If --action is not specified or if any unknown argument is caught - nothing will be done. 
                        '''),
                        epilog=textwrap.dedent(f'''
                        If the -c or -r flags were not passed, the default values will be used instead.
                        Default values of flags - in the config:
                            -c - CONSUL_REG
                            -r - DELETE_RELOG_FILES
                            
                        --action:

                        start        - starts the service via uwsgi
                        start_docker - used to start a service via uwsgi in a docker container. NOT TO BE USED BY ITSELF
                        stop         - stops the service by the pid file, which is in the tmp folder
                        hardstop     - kills the service on the port specified in the config
                        restart      - performs stop, waits for the port to become free, and then start
                        status       - checks the current status of the service assuming the config did not change after
                            launch, displays the current hash from the git
                        tests        - runs tests described in service_manager_lib.test_api
                        relog        - processes logs named in RELOG_FILES (as a regular expression).
                            Performs actions described in  service_manager_lib.relog function
                            Puts results in */relogs/:
                                exceptions.log      - uncaught exceptions
                                internal_errors.log - exceptions caught and errors shown to the client as a result
                        
                        config file
                            {__file__} accepts parameters as config file, which is named config.yaml, present in
                            same folder as {__file__}, and meets yaml specification 1.1, for more details about 
                            that read https://yaml.org/spec/1.1/.
                            You can find sample config at sample.config.yaml

                        Why pyyaml(yaml 1.1) and not ruamel.yaml(yaml 1.2)? 
                            I found question on SO with example of a library that only supports 1.1 and I'm too lazy to 
                            change lib after i parsed config. But some day I will update it.
                        '''))

parser.add_argument('-a', '--action', action='store', help='action, complete list is below', default=None, metavar='<action>', required=True)
parser.add_argument('-c', '--consul', action='store_true', help='bool flag, register/deregister in consul at start/stop', default=False)
parser.add_argument('-r', '--relog', action='store_true', help='bool flag, delete existing secondary logs when --action is relog', default=False)
parser.add_argument('-t', '--trap', action='store_true', help=argparse.SUPPRESS, default=False)
parser.add_argument('-v', '--version', action='version', help='show version and exit', version='service_manager 3.0')
# help argument generated by argparse

args = parser.parse_args()
nohup_logger.log(f'action argument is:{args.action}')
nohup_logger.log(f'consul argument is:{args.consul}')
nohup_logger.log(f'relog argument is:{args.relog}')
if args.trap is True:
    nohup_logger.log(f'IT\'S A TRAP!!')

