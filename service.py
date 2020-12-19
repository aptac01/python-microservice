#!env/bin/python
# coding: utf-8

"""
Executable for managing service
Черновик, будет переделываться
"""

import os
import sys
import copy
import base64
import requests
import argparse
import datetime
import textwrap
import subprocess
from argparse import ArgumentParser
from service_manager_lib import MyLogger, proc_status, is_proc_status_fine, parse_config, cycle_with_limit, is_local_port_available


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
config = parse_config(config_filename, nohup_logger)

# trying to open nohup.out file and if it opens - write logs to it
# in that case, no file - no big deal
try:
    nohup_file = open(config['nohup_out_log'], 'a+')
except FileNotFoundError:
    nohup_file = config['nohup_out_log']
except OSError:
    nohup_file = config['nohup_out_log']

nohup_logger.set_params(file=nohup_file, config=config)

# nohup_logger.log(f'running from :{cnfg}', color_front='yellow')
# nohup_logger.log(f'config file is at {config_filename}', color_front='yellow')
# nohup_logger.log(f'{config["uwsgi"]}', color_front='green')

# todo: вынести этот параметр в конфиг
neat_script_name = 'service'

# then, we validate user's input and decide what does he want
actions = [
    ['start', '           starts the service via uwsgi'],
    ['start_docker', '    used to start a service via uwsgi in a docker container. NOT TO BE USED BY ITSELF'],
    ['stop', '            stops the service by the pid file, which is in the tmp folder'],
    ['hardstop', '        kills the service on the port specified in the config'],
    ['restart', '         performs stop, waits for the port to become free, and then start'],
    ['status', '''          checks the current status of the service assuming the config did not change  
                                           after launch, displays the current hash from the git'''],
    ['tests', '           runs tests described in service_manager_lib.test_api'],
    ['relog', '''           processes logs named in RELOG_FILES (as a regular expression).
                                           Performs actions described in  service_manager_lib.relog function
                                           Puts results in */relogs/:
                                                exceptions.log      - uncaught exceptions
                                                internal_errors.log - caught and are shown to the client as a result'''],
    ['generate_ruffles', f'''generates neat shell script for usage instead of running this thing 
                                           in python's virtual environment, a lot easier to remember.
                                           Filename is:
                                               {neat_script_name}''']
]
actions_output = '\n'
actions_keys = []
for action in actions:
    actions_output += '                        ' + action[0] + ' - ' + action[1] + '\n'
    actions_keys.append(action[0])

# noinspection PyTypeChecker
# this will be the help message
parser = ArgumentParser(prog=f'{neat_script_name}',
                        usage=f'./{neat_script_name}  -a <action> [-c (1|0)] [-r (1|0)] [-v]',
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

# memorizing current directory to return to it later
current_working_directory = os.getcwd()
os.chdir(config['api_directory'])

args_from_user = sys.argv
del args_from_user[0]
args_from_user_text = ''
for arg_from_user in args_from_user:
    args_from_user_text += arg_from_user + ' '

nohup_logger.log(f'Got these args: {args_from_user_text}', color_front='yellow')
nohup_logger.log(f'Timestamp: {str(datetime.datetime.now())}', color_front='light blue')
result = subprocess.run(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
if result.returncode == 0:
    git_hash = result.stdout.decode("utf8").replace('\n', '')
    nohup_logger.log(f'Current hash in GIT: {git_hash}', color_front='light blue')
else:
    nohup_logger.log(f'something went wrong with git, check it out:\n---\n{result.stderr}\n==='
                     f'\n---\n{result.stdout}\n===', color_front='red')

# todo:
#  не забудь перенести весь остальной функционал из service_manager2.sh


def generate_uwsgi_yaml(config_section):
    """
    Generate yaml config file for uwsgi from service config
    :param config_section - dict with all uwsgi vars
    """
    filename = config_section['config_file']
    config_copy = copy.deepcopy(config_section)
    del config_copy['config_file']
    config_contents = 'uwsgi:\n'

    for key, val in config_copy.items():
        config_contents += f'    {key}: {val}\n'

    if os.path.isfile(filename):
        os.remove(filename)

    actual_file = open(filename, 'w+', encoding='utf-8')
    actual_file.write(config_contents)
    nohup_logger.log('Re-generated uwsgi.yaml file...', color_front='dark gray')


def start_service(consul_reg):
    """
    Start service in background (as a daemon)
    todo: %in progress%
        make protection from starting 2 master-uwsgi instances
        register in consul
    """

    # to get rid of warning that param value is not used, gonna be fixed later
    str(consul_reg)

    generate_uwsgi_yaml(config['uwsgi'])

    # starting uwsgi proccess
    res = subprocess.Popen(['nohup',
                            config["uwsgi_exec"],
                            '--yaml',
                            config["uwsgi"]["config_file"],
                            # '--disable-logging',
                            ],
                           stdout=nohup_file,
                           stderr=nohup_file)

    nohup_logger.log('waiting a bit to see if service is working or not...', color_front='dark gray')

    def check_service_started(res_loc):
        """
        Callback function to check if service has started
        """
        res_loc.poll()

        # getting service status, if it's working as intended or not
        uwsgi_master_proc_int = is_proc_status_fine(proc_status(res_loc.pid))
        request = requests.post('http://localhost:' + str(config['SERVER_PORT']) + '/ping', verify=False)
        ping_endpoint_int = request.ok

        if uwsgi_master_proc_int and ping_endpoint_int:
            return [True, uwsgi_master_proc_int, ping_endpoint_int]
        else:
            return [False, uwsgi_master_proc_int, ping_endpoint_int]

    flags_after_action = cycle_with_limit(check_service_started, res, 0.3, 3)
    uwsgi_master_proc = flags_after_action[1]
    ping_endpoint = flags_after_action[2]

    if uwsgi_master_proc:
        nohup_logger.log(f'uWSGI master process is running, pid: {res.pid}', color_front='green')
        nohup_logger.log(f'{config["local_ip"]}:{config["local_port"]}', color_front='green')
    else:
        nohup_logger.log(f'Something went wrong while running uWSGI master pid: {res.pid}, '
                         f'check {config["nohup_out_log"]} and {config["uwsgi"]["logto"]}', color_front='red')
    if ping_endpoint:
        nohup_logger.log(f'/ping endpoint is ok, service should be alive', color_front='green')
    else:
        nohup_logger.log(f'/ping endpoint is dead, something went wrong, '
                         f'check {config["nohup_out_log"]} and {config["uwsgi"]["logto"]}', color_front='red')


def clean_up():
    """
    Cleans all garbage files after service has been stopped
    """
    nohup_logger.log('Cleaning up...', color_front='dark gray')

    for path in config['paths_to_delete']:
        if os.path.isfile(path):
            try:
                os.remove(path)
                nohup_logger.log(f'           ...{path}', color_front='dark gray')
            except Exception as e:
                nohup_logger.log(f'           error: {e} when deleting {path}', color_front='red')
        elif os.path.isdir(path):
            try:
                # deleting directory contents
                os.system(f'rm -rf {path}/*')
                nohup_logger.log(f'           ...{path}', color_front='dark gray')
            except Exception as e:
                nohup_logger.log(f'           error: {e} when deleting {path}', color_front='red')


def kill_proccess_by_port():
    """
    Kill process by port from config using lsof utility
    """

    nohup_logger.log(f'trying to kill proccess by port', color_front='light blue')

    res = subprocess.run([config['lsof_command'], '-t', '-i', f'tcp:{config["SERVER_PORT"]}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if res.stdout == b'':
        nohup_logger.log(f'No service found on tcp:{config["SERVER_PORT"]}!', color_front='red')
    else:
        pids = res.stdout.split(b'\n')
        subprocess.run(['kill', '-9', pids[0]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        nohup_logger.log(f'killed proccess with pid {pids[0].decode("utf8")} '
                         f'which was working on port {config["SERVER_PORT"]}', color_front='green')


def stop_service(consul_reg):
    """
    Stop running service
    todo: %in progress% разрегистрация из консула
    """
    str(consul_reg)

    if os.path.exists(config['pid_file']):
        res = subprocess.Popen([config["uwsgi_exec"], '--stop', config['pid_file']],
                               stdout=nohup_file, stderr=nohup_file)

        nohup_logger.log('waiting for service to be killed...', color_front='dark gray')

        def check_service_killed(res_loc):
            """
            Callback function to check if service has really been killed
            """
            res_loc.poll()
            port_open = is_local_port_available(config['lsof_command'], config['local_port'])

            if (res_loc.returncode == 0) and port_open:
                return [True, res_loc.returncode]
            else:
                return [False, res_loc.returncode]

        flags_after_action = cycle_with_limit(check_service_killed, res, 0.2, 5)
        res_returncode = flags_after_action[1]

        if res_returncode == 0:
            nohup_logger.log('service stopped successfully', color_front='green')
        else:
            nohup_logger.log(f'something went wrong while stopping service, check {config["nohup_out_log"]}', color_front='red')
            kill_proccess_by_port()
    else:
        nohup_logger.log('did not find pid file', color_front='yellow')
        kill_proccess_by_port()

    clean_up()


if args.action == 'start':
    start_service(args.consul)

elif args.action == 'stop':
    stop_service(args.consul)

elif args.action == 'restart':
    stop_service(args.consul)
    start_service(args.consul)

elif args.action == 'generate_ruffles':
    shell_script_file = open(neat_script_name, 'w+')
    shell_script_file.write(f"""#!/bin/bash
python_executable="{config["env_python_exec"]}"
$python_executable service.py "$@"
    """)
    shell_script_file.close()
    nohup_logger.log('Replaced service file...', color_front='dark gray')

# changing current directory back
os.chdir(current_working_directory)
nohup_logger.log('================= Service managing operation finish ================')

if not isinstance(nohup_file, str):
    nohup_file.close()
