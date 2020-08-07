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
import datetime
import textwrap
import subprocess
from time import sleep
from argparse import ArgumentParser
from service_manager_lib import MyLogger, proc_status


def join(loader, node):
    """
    Define custom yaml construction named join
    more info: https://stackoverflow.com/a/57327330/8700211
    """
    seq = loader.construct_sequence(node)
    return ''.join([str(i) for i in seq])


# todo все эти комменты надо будет удалить
# вся вот эта хрень будет скрыта от пользователя, если все проходит штатно
# ---------------------
# таким макаром запускаем что-то и ждем пока оно выполнится
# если cd задать неправильный путь для перехода - subprocess.run выкидывает exception (т.е. его надо ловить)
# если подпроцесс завершился сам - exception (если он был) не выкидывается.
# про другие такие команды не знаю, надо тестить
#   возможно, выкидываются исключения от операционной системы или интерпретатора (bash и т.п.)
# result = subprocess.run(['kill', '-h'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
#
# # nohup_logger.log(f'{result.stdout.decode("utf8")}')
# if result.returncode != 0:
#     nohup_logger.log(f'The exit code is {result.returncode}')
# if result.stderr not in (None, '', 0, b''):
#     nohup_logger.log(f'This is what happened: {result.stderr.decode("utf8")}')

# nohup_logger.log('daemonizing kill -h')
# таким макаром запускаем и не ждем пока оно выполнится
# оно умирает по завершению родительского скрипта (т.е. вот этого)
# subprocess.run(['kill', '-h'], stdout=None, stderr=None, check=False)

# пока что единственный рабочий способ нормально запустить сервис в фоне:
# os.system('ddd')

# я - дятел, можно было вот так - subprocess.Popen(['a', 'r', 'g', 's']) и немного подождать

# ---------------------

# ----------------------------------------------------
# https://docs.python.org/3.8/library/argparse.html#action - argparse documentation

# first, we are trying to parse config and initialize logger to only print messages on screen

cnfg = os.path.dirname(os.path.abspath(__file__))
config_filename = f'{cnfg}/config.yaml'

nohup_logger = MyLogger()

# registering the custom tag handler
yaml.add_constructor('!join', join)

# no config file - no bueno
try:
    opened_config_file = open(config_filename, 'r')
except FileNotFoundError:
    nohup_logger.log(f'Couldn\'t find config file! Make sure {config_filename} exists; Exiting...', color_front='red')
    sys.exit(1)

# parsing config
with opened_config_file as stream:
    try:
        # that's the intended ("proper") way of parsing yaml from untrusted source, but since we are expecting our
        # user to be somewhat experienced and trustworthy, we can afford luxury of not giving a fuck
        # config = yaml.safe_load(stream, Loader=yaml.Loader)
        config = yaml.load(stream, Loader=yaml.Loader)
    except yaml.YAMLError as exc:
        # but still, if something goes wrong - no bueno
        nohup_logger.log(str(exc))
        sys.exit(1)

# at this point config should be dictionary

# trying to open nohup.out file and additionally write logs to it
# in that case, no file - no big deal
try:
    nohup_file = open(config['nohup_out_log'], 'a+')
except FileNotFoundError:
    nohup_file = 'no_file'
except OSError:
    nohup_file = 'no_file'

nohup_logger.set_file(nohup_file)

# nohup_logger.log(f'running from :{cnfg}', color_front='yellow')
# nohup_logger.log(f'config file is at {config_filename}', color_front='yellow')
# nohup_logger.log(f'{config["uwsgi"]}', color_front='green')

# then, we validate users input and decide what does he want
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
# this will be the help message
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

# defining possible cli arguments
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
# help message is generated by argparse, no need to add -h/--help argument

args = parser.parse_args()

# how to access arguments:
# nohup_logger.log(f'action argument is:{args.action}')
# nohup_logger.log(f'consul argument is:{args.consul}')
# nohup_logger.log(f'relog argument is:{args.relog}')
# if args.trap is True:
#     nohup_logger.log(f'IT\'S A TRAP!!')

nohup_logger.log('----------------- Service managing operation start -----------------')

args_from_user = sys.argv
del args_from_user[0]
args_from_user_text = ''
for arg_from_user in args_from_user:
    args_from_user_text += arg_from_user + ' '

nohup_logger.log(f'Got these args: {args_from_user_text}', color_front='yellow')
nohup_logger.log(f'Timestamp: {str(datetime.datetime.now())}', color_front='light blue')
result = subprocess.run(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
if result.returncode == 0:
    nohup_logger.log(f'Current hash in GIT: {result.stdout.decode("utf8")}', color_front='light blue')  # todo после этого сообщения в консоли пустая строка, надо разобраться что за дела
else:
    nohup_logger.log(f'something went wrong with git, check it out:\n---\n{result.stderr.decode("utf8")}\n==='
                     f'\n---\n{result.stdout.decode("utf8")}\n===', color_front='red')  # todo FIX разобраться почему не работает


def start_service(consul_reg):
    """
    Start service in background (as a daemon)
    todo: %in progress%
    """

    os.chdir(config['api_directory'])
    str(consul_reg)

    # res = os.system(
    #     f'nohup {config["uwsgi_exec"]} --ini {config["uwsgi"]["config_file"]} >> {config["nohup_out_log"]} 2>> {config["nohup_out_log"]} &')
    res = subprocess.Popen(['nohup',
                            config["uwsgi_exec"],
                            '--ini',
                            config["uwsgi"]["config_file"],
                            ],
                           stdout=nohup_file,
                           stderr=nohup_file)

    nohup_logger.log('waiting a bit to see if service is working or not...', color_front='dark gray')
    sleep(3)
    res.poll()
    nohup_logger.log(f'res: {res.returncode}')

    if res.returncode == 0:
        nohup_logger.log('Looks like the app is running.', color_front='green')
    else:
        nohup_logger.log(f'Something went wrong, uwsgi master pid: {res.pid}, it exited with code: {res.returncode}, '
                         f'check {config["nohup_out_log"]} and {config["uwsgi"]["logto"]}', color_front='red')


def stop_service(consul_reg):
    """
    Stop running service
    todo: %in progress%
    """
    str(consul_reg)

    # res = subprocess.run([config['lsof_command'], '-t', '-i', f'tcp:{config["SERVER_PORT"]}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # # if result.returncode == 0:
    #
    # if res.stdout == b'':
    #     nohup_logger.log(f'No service found on tcp:{config["SERVER_PORT"]}!', color_front='red')
    # else:
    #     pids = res.stdout.split(b'\n')
    #     res = subprocess.run(['kill', '-9', pids], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #     nohup_logger.log(f'{res.returncode}, {res.stdout}, {res.stderr}')

    if os.path.exists(config['pid_file']):
        res = subprocess.Popen([config["uwsgi_exec"], '--stop', config['pid_file']],
                               stdout=nohup_file, stderr=nohup_file)
        # надо немного подождать, процесс умирает не мгновенно
        nohup_logger.log(f'{res.returncode}, {res.stdout}, {res.stderr}', color_front='yellow')
        if res.returncode == 0:
            nohup_logger.log('service stopped successfully', color_front='green')
        else:
            nohup_logger.log('something went wrong while stopping service', color_front='red')
    else:
        nohup_logger.log('service is not running, no need to stop it', color_front='yellow')


if args.action == 'start':
    start_service(args.consul)
elif args.action == 'stop':
    stop_service(args.consul)

nohup_logger.log('================= Service managing operation finish ================')

if not isinstance(nohup_file, str):
    nohup_file.close()
