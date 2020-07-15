#!env/bin/python
# coding: utf-8

"""
Исполняемый файл для управления сервисом
Черновик, будет переделываться
"""

import subprocess
from service_manager_lib import MyLogger

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
        }
    ]
}

nohup_logger.log('----------------- Service managing operation start -----------------')
nohup_logger.log('123 test', color_scheme_service)

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