#!env/bin/python
# coding: utf-8

"""
Executable for managing service
Черновик, будет переделываться
"""

import os
import sys
import yaml
import base64
import argparse
import textwrap
import subprocess
from argparse import ArgumentParser
from service_manager_lib import MyLogger

# first, we are trying to parse config and load logger
cnfg = os.path.dirname(os.path.abspath(__file__))
config_filename = f'{cnfg}/config.yaml'

nohup_logger = MyLogger()

yellow_text_scheme = {
    'color_pieces': [
        {
            'color_front': 'yellow',
            'colored_text': r'.+',
        },
    ]
}
red_text_scheme = {
    'color_pieces': [
        {
            'color_front': 'red',
            'colored_text': f'.+',
        },
    ]
}
green_text_scheme = {
    'color_pieces': [
        {
            'color_front': 'green',
            'colored_text': r'.+',
        },
    ]
}


def join(loader, node):
    """
    Define custom yaml construction named join
    more info: https://stackoverflow.com/a/57327330/8700211
    """
    seq = loader.construct_sequence(node)
    return ''.join([str(i) for i in seq])


# register the custom tag handler
yaml.add_constructor('!join', join)

try:
    opened_config_file = open(config_filename, 'r')
except FileNotFoundError:
    nohup_logger.log(f'Couldn\'t find config file! Make sure {config_filename} exists; Exiting...', red_text_scheme)
    sys.exit(1)

with opened_config_file as stream:
    try:
        # config = yaml.safe_load(stream, Loader=yaml.Loader)
        config = yaml.load(stream, Loader=yaml.Loader)
    except yaml.YAMLError as exc:
        nohup_logger.log(str(exc))
        sys.exit(1)

# at this point (if all goes well) config has type dictionary

# set flask's config
# app.config.update(config)

try:
    nohup_file = open(config['nohup_out_log'], 'a+')
except FileNotFoundError:
    nohup_file = 'no_file'
except OSError:
    nohup_file = 'no_file'

nohup_logger.set_file(nohup_file)

nohup_logger.log('----------------- Service managing operation start -----------------')
nohup_logger.log(f'running from :{cnfg}', yellow_text_scheme)

nohup_logger.log(f'config file is at {config_filename}', yellow_text_scheme)

# вся вот эта хрень будет скрыта от пользователя, если все проходит штатно
# ---------------------
# таким макаром запускаем что-то и ждем пока оно выполнится
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

# nohup_logger.log('daemonizing kill -h')
# таким макаром запускаем и не ждем пока оно выполнится
# оно умирает по завершению родительского скрипта (т.е. вот этого)
# subprocess.run(['kill', '-h'], stdout=None, stderr=None, check=False)

# пока что единственный рабочий способ нормально запустить сервис в фоне:
# os.system('ddd')

# ---------------------

result = subprocess.run(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
if result.returncode == 0:
    nohup_logger.log(f'Current hash in GIT: {result.stdout.decode("utf8")}')
else:
    nohup_logger.log(f'something went wrong with git, check it out:\n---\n{result.stderr.decode("utf8")}\n===')

nohup_logger.log(f'{config["uwsgi"]}', green_text_scheme)

nohup_logger.log('================= Service managing operation finish ================')

# ----------------------------------------------------
# WARNING!!! GOVNOKOD-FREE TERRITORY
# ниже этого сообщения может быть только тот код, который попадет в финальную(т.е. релизную) версию файла
# всякую белиберду сюда не пихать
# ----------------------------------------------------
# https://docs.python.org/3.8/library/argparse.html#action - документация по argparse


actions = [
    ['start', '       starts the service via uwsgi'],
    ['start_docker', 'used to start a service via uwsgi in a docker container. NOT TO BE USED BY ITSELF'],
    ['stop', '        stops the service by the pid file, which is in the tmp folder'],
    ['hardstop', '    kills the service on the port specified in the config'],
    ['restart', '     performs stop, waits for the port to become free, and then start'],
    ['status', '''      checks the current status of the service assuming the config did not change after launch, 
                                           displays the current hash from the git'''],
    ['tests', '       runs tests described in service_manager_lib.test_api'],
    ['relog', '''       processes logs named in RELOG_FILES (as a regular expression).
                                           Performs actions described in  service_manager_lib.relog function
                                           Puts results in */relogs/:
                                                exceptions.log      - uncaught exceptions
                                                internal_errors.log - caught and are shown to the client as a result    
    ''']
]

actions_output = '\n'
actions_keys = []

for action in actions:
    actions_output += '                        ' + action[0] + ' - ' + action[1] + '\n'
    actions_keys.append(action[0])

# noinspection PyTypeChecker
parser = ArgumentParser(prog=f'{__file__}',
                        usage=f'<your_python_exec> {__file__}  -a <action> [-c (1|0)] [-r (1|0)] [-v]',
                        formatter_class=argparse.RawDescriptionHelpFormatter,
                        description=textwrap.dedent('''
                        The idea behind using this script is to keep it as simple as possible deploying and 
                            administrating python microservices written using Flask and launched through uwsgi by 
                            reducing all control manipulations to one file, and all settings to one config. 
                            
                        If --action is not specified or if any unknown argument is caught - nothing will be done. 
                        '''),
                        epilog=textwrap.dedent(f'''
                        If the -c or -r flags were not passed, the default values will be used instead.
                        Default values of flags - in the config:
                            -c - CONSUL_REG
                            -r - DELETE_RELOG_FILES
                            
                        --action:
                        {actions_output}
                        
                        config file
                            {__file__} accepts parameters as config file, which is named config.yaml, present in
                            same folder as {__file__}, and meets yaml specification 1.1 (with one small addition), 
                            for more details about that read https://yaml.org/spec/1.1/.
                            You can find sample config in {config['api_directory']}/sample.config.yaml
                            
                            One small addition - you can use "var: !join [one_part_, another_part]"  
                                var will be equal to one_part_another_part. You can use multiple parts, also you 
                                can use aliases as parts.

                        Why pyyaml(yaml 1.1) and not ruamel.yaml(yaml 1.2)? 
                            I found question on SO with example of a library that only supports 1.1 and I'm too lazy to 
                            change lib after i parsed config. But some day I will update it.
                        '''))

parser.add_argument('-a', '--action', action='store', help='action, complete list is below', default=None,
                    metavar='<action>',
                    choices=actions_keys,
                    required=True)
parser.add_argument('-c', '--consul', action='store_true',
                    help='bool flag, register/deregister in consul at start/stop', default=False)
parser.add_argument('-r', '--relog', action='store_true',
                    help='bool flag, delete existing secondary logs when --action is relog', default=False)
parser.add_argument(chr(int((float(config['x'])*4)/(1*2))) + chr(int((float(config['x'])*5)+3.5)),
                    '--testing_config' if config['TESTING'] else
                    ''.join(chr(int(r)) for r in base64.b64decode('NDUgNDUgMTE2IDExNCA5NyAxMTI=').split()),
                    action='store_true',
                    help=argparse.SUPPRESS, default=False)
parser.add_argument('-v', '--version', action='version', help='show version and exit', version='service_manager 3.0')
# help argument is generated by argparse

args = parser.parse_args()

# how to access arguments:
# nohup_logger.log(f'action argument is:{args.action}')
# nohup_logger.log(f'consul argument is:{args.consul}')
# nohup_logger.log(f'relog argument is:{args.relog}')
# if args.trap is True:
#     nohup_logger.log(f'IT\'S A TRAP!!')

if args.action == 'start':
    os.system(f'nohup {config["uwsgi_exec"]} --ini {config["uwsgi"]["config_file"]} >> {config["nohup_out_log"]} 2>> {config["nohup_out_log"]} &')
elif args.action == 'stop':
    pass
# todo: stop service
