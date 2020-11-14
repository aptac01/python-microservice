#!env/bin/python
# coding: utf-8

"""
Модуль, в котором собраны служебные штуки для обеспечения работы сервиса и service_manager'a, 
будь то:
 
  * работа с консулом
  * вспомогательные функции для юнит-тестов
  * сами тесты (но это временно)
  * частоиспользуемые в разных скриптах вещи
  * сами отдельные скрипты (а это не временно)

todo: translate this docstring after service.py (aka service_manager3) is ready
"""


false_items = ('0', 0, False, 'false', 'False')
true_items = ('1', 1, True, 'true', 'True')


class MyLogger:
    """
    My approach on logging, prints messages on screen and writes them to file
    """

    def __init__(self, **kwargs):
        """
        Initializes logger, optionally setting file, to which logs are written
        """
        self.file = kwargs['file'] if 'file' in kwargs else None
        self.config = kwargs['config'] if 'config' in kwargs else None

        if self.file is not None:
            self.show_file_warning = True
        else:
            self.show_file_warning = False

        self.FOREGROUND = {
             'black':         30,
             'red':           31,
             'green':         32,
             'yellow':        33,
             'blue':          34,
             'magenta':       35,
             'cyan':          36,
             'light gray':    37,
             'dark gray':     90,
             'light red':     91,
             'light green':   92,
             'light yellow':  93,
             'light blue':    94,
             'light magenta': 95,
             'light cyan':    96,
             'white':         97,
        }
        self.BACKGROUND = {
            'black':          40,
            'red':            41,
            'green':          42,
            'yellow':         43,
            'blue':           44,
            'magenta':        45,
            'cyan':           46,
            'light gray':     47,
            'dark gray':      100,
            'light red':      101,
            'light green':    102,
            'light yellow':   103,
            'light blue':     104,
            'light magenta':  105,
            'light cyan':     106,
            'white':          107,
        }

    def set_params(self, **kwargs):
        """
        Set internal parameters
        """
        if 'file' in kwargs:
            self.file = kwargs['file']

        if 'show_file_warning' in kwargs:
            self.show_file_warning = kwargs['show_file_warning']
        elif self.file is not None:
            self.show_file_warning = True
        else:
            self.show_file_warning = False

        if 'config' in kwargs:
            self.config = kwargs['config']

    # noinspection PyPep8Naming
    def log(self, msg, options=None, **kwargs):
        """
        Print msg on screen and write it to file. Optionally, you can paint your text.

        Args:
            msg (str): message
            options (dict): array of options to customize message
                newline (bool): when writing to file, do not add '\n' in the end of msg, default - false
                color_pieces (list): array of colored rows
                        If color not from allowed list - it will not be applied
                        If colored_text is not found in msg - do nothing
                    color_front (str): text color (look self.FOREGROUND)
                    color_back (str): background color (look self.BACKGROUND)
                    colored_text (str): piece of text, that needs to be painted, regex
            **kwargs:
                color_front(str): color of text, if present - will be applied to whole msg
                color_back(str): color of background, if present - will be applied to whole msg
        """
        # todo: refactor this monstrosity
        import os

        COLOR_LOGS_SCREEN = self.config['COLOR_LOGS_SCREEN'] if self.config is not None else os.environ.get('COLOR_LOGS_SCREEN')
        if COLOR_LOGS_SCREEN in false_items:
            COLOR_LOGS_SCREEN = False
        else:
            COLOR_LOGS_SCREEN = True

        COLOR_LOGS_FILES = self.config['COLOR_LOGS_FILES'] if self.config is not None else os.environ.get('COLOR_LOGS_FILES')
        if COLOR_LOGS_FILES in true_items:
            COLOR_LOGS_FILES = True
        else:
            COLOR_LOGS_FILES = False

        options_default = {
            'newline': False,
            'color_pieces': [],
        }
        color_piece_default = {
            'color_front': False,
            'color_back': False,
            'colored_text': '',
            'color_specific_group': False,
        }
        if options is None:
            options = options_default
        else:
            options = {**options_default, **options}

        if 'color_front' in kwargs:
            options['color_pieces'].append({
                'color_front': kwargs['color_front'],
                'color_back': False,
                'colored_text': r'.+',
            })
        if 'color_back' in kwargs:
            options['color_pieces'].append({
                'color_front': False,
                'color_back': kwargs['color_back'],
                'colored_text': r'.+',
            })

        colored_msg = None

        if COLOR_LOGS_SCREEN:
            import re

            color_pieces_local = []

            if options.get('color_pieces', []):
                allowed_colors = list(self.FOREGROUND.keys()) + [False]
                for color_piece in options['color_pieces']:
                    merged_color_piece = {**color_piece_default, **color_piece}

                    if merged_color_piece['color_front'] not in allowed_colors:
                        merged_color_piece['color_front'] = False

                    if merged_color_piece['color_back'] not in allowed_colors:
                        merged_color_piece['color_back'] = False

                    color_pieces_local.append(merged_color_piece)

            colored_msg = msg

            for piece in color_pieces_local:

                if piece['colored_text'] == '':
                    continue

                # noinspection PyTypeChecker
                resolved_string = re.findall(piece['colored_text'], colored_msg)

                if len(resolved_string) < 0:
                    continue

                elif len(resolved_string) > 1:
                    # gluing multirows all together as separate rows
                    for row in resolved_string:
                        if row not in ('', ' ', None, resolved_string[0]):
                            resolved_string[0] += '\n' + row

                resolved_string = resolved_string[0]

                # when printing stuff from stderr and stdout you can encounter some weird shit
                # like bytes strings placed into regular string
                resolved_string = re.sub(r'b[\"\'](.*)[\"\']', '\\1', resolved_string)

                if piece["color_back"]:
                    # noinspection PyTypeChecker
                    colored_msg = re.sub(piece['colored_text'],
                                         '\033[' + str(self.BACKGROUND[piece["color_back"]]) + 'm'
                                         + resolved_string
                                         + '\033[49m',
                                         colored_msg,
                                         1,
                                         re.DOTALL)
                else:
                    colored_msg = colored_msg

                if piece["color_front"]:

                    # noinspection PyTypeChecker
                    colored_msg = re.sub(piece['colored_text'],
                                         '\033[' + str(self.FOREGROUND[piece["color_front"]]) + 'm'
                                         + resolved_string
                                         + '\033[39m',
                                         colored_msg,
                                         1,
                                         re.DOTALL)
                else:
                    colored_msg = colored_msg

        if COLOR_LOGS_SCREEN and colored_msg:
            print(colored_msg)
        else:
            print(msg)

        # printing to file only if it exists
        if 'name' in dir(self.file) and os.path.isfile(self.file.name):

            msg_ending = ''
            if not options['newline']:
                msg_ending = '\n'

            if COLOR_LOGS_FILES and colored_msg:
                self.file.write(colored_msg + msg_ending)
            else:
                self.file.write(msg + msg_ending)
        elif self.show_file_warning:
            print(f'No nohup file was found ({self.file}), make sure that it exists')


def join(loader, node):
    """
    Define custom yaml construction named join
    needed in parse_config
    more info: https://stackoverflow.com/a/57327330/8700211
    """
    seq = loader.construct_sequence(node)
    return ''.join([str(i) for i in seq])


def parse_config(config_file, logger=False):
    """
    Parse config with specified path. Returns dict with resulting params.

    config_file(string): path of the config file
    logger(MyLogger): logger object, in case something goes wrong
    """
    import os
    import sys
    import yaml

    # registering the custom tag handler
    yaml.add_constructor('!join', join)

    if not logger:
        # default logger, that will write errors to screen
        logger = MyLogger()

    # no config file - no bueno
    try:
        opened_config_file = open(config_file, 'r')
    except FileNotFoundError:
        logger.log(f'Couldn\'t find config file! Make sure {config_file} exists; Exiting...',
                   color_front='red')
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
            logger.log(str(exc))
            sys.exit(1)

    # sometimes env-variables are needed, so, we set them up from a list, dedicated to storing names of such vars
    if 'env_vars' in config:
        for var in config['env_vars']:
            os.environ[var] = config[var]

    # at this point config should be dictionary

    return config


def cycle_with_limit(callback_func, callback_args, seconds_between_tries=0.3, seconds_limit=7):
    """
    Call callback_func (with callback_args) every seconds_between_tries seconds, until seconds_limit passed.
    Sleeps between tries.
    callback_func should return list, in which first value must be bool, and if it's true
     - cycle will be over before limit.
    """

    import sched
    import time

    counter = time.time()
    callback_func_result = [True, ]

    def do_stuff(sch):
        """
        execute users function
        """

        nonlocal callback_func_result

        callback_func_result = callback_func(callback_args)

        if (not callback_func_result[0]) \
                and ((time.time() - counter) <= seconds_limit):
            sch.enter(seconds_between_tries, 1, do_stuff, (sch, ))
        else:
            return

    s = sched.scheduler(time.time, time.sleep)
    s.enter(seconds_between_tries, 1, do_stuff, (s, ))
    s.run()

    return callback_func_result


def proc_status(pid):
    """
    Get process state by pid
        R  running or runnable (on run queue)
        D  uninterruptible sleep (usually IO)
        S  interruptible sleep (waiting for an event to complete)
        Z  defunct/zombie, terminated but not reaped by its parent
        T  stopped, either by a job control signal or because
           it is being traced
    """
    # TODO можно попытаться заменить эту штуку на такое:
    # import psutil
    # p = psutil.Proccess(MyPid)
    # p.status
    # ошибка только при рестарте:
    # FileNotFoundError: [Errno 2] No such file or directory: '/proc/%d/status'
    for line in open("/proc/%d/status" % pid).readlines():
        if line.startswith("State:"):
            return line.split(":", 1)[1].strip().split(' ')[0]
    return None


def is_proc_status_fine(status):
    """
    Return true, if a proccess with given status is working and not stopped or killed
    Return false otherwise
    """
    if status in ('R', 'D', 'S'):
        return True
    else:
        return False


def is_iterable(obj):
    """
    Return true if obj is iterable, false otherwise
    """
    # noinspection PyBroadException
    try:
        iter(obj)
    except Exception:
        return False
    else:
        return True


def is_port_open(ip, port, timeout=3):
    """
    Check, if given address and port are available.
   
    timeout (int): Max time to connect, seconds. If there is no answer in that time - we presume that port is closed.
    """

    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    # noinspection PyBroadException
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        return True
    except Exception:
        return False
    finally:
        s.close()

def is_local_port_available(command, port):
    """
    Determine if local port is available for taking by process
    Does so by executing "lsof -ti:%port", which is considered to be almost momentary
    """
    import subprocess
    #TODO: refactor, handle errors.

    lsof = subprocess.Popen([command, f'-ti:{port}'],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    lsof_out = ''
    for line in lsof.stdout:
        lsof_out += line.decode("utf-8")
    if lsof_out != '':
        return False
    else:
        return True

def connect_to_consul(consul_address, consul_port, logger):
    """
    Connect to given consul instance or log an error
    """

    import consul

    if (consul_address is None) or (consul_port is None):
        logger.log(f"No address or port, exiting doing nothing")
        return None

    if not (is_port_open(consul_address, consul_port)):
        logger.log(f"Error connecting consul on {consul_address}:{consul_port}: address is not responding")
        return None
    try:
        c = consul.Consul(host=consul_address, port=consul_port)
    except Exception as e:
        logger.log(f"Error connecting consul on {consul_address}:{consul_port} : {e}")
        return None

    return c


def check_service(service_id, consul_address, consul_port, logger):
    """
    Check if service with given id registered in consul
    """

    c = connect_to_consul(consul_address, consul_port, logger)
    if c is None:
        return None

    index, services = c.catalog.services()

    s_dict = {}
    for service in services:

        index, data = c.catalog.service(service)

        for s_data in data:
            # s_data['ServiceName'],
            # s_data['ServiceID'],
            # s_data['ServiceAddress'],
            # s_data['ServicePort'],
            # s_data['ServiceTags']

            s_dict[s_data['ServiceID']] = s_data

    if s_dict is None:
        return False

    if service_id in s_dict:
        return True
    else:
        return False


def register_service(service, consul_address, consul_port, logger):
    """
    Register given service in consul
    """

    from consul.base import Check

    c = connect_to_consul(consul_address, consul_port, logger)
    if c is None:
        return None

    if check_service(service['id'], consul_address, consul_port, logger):
        logger.log(f"Service <{service['id']}> already registered")
        return True

    result = c.agent.service.register(
        service['name'],
        service_id=service['id'],
        address=service['ip'],
        port=service['port'],
        tags=service['tags'],
        check=Check.http((service['checkAddress']), service['checkInterval'])
    )

    return result


def deregister_service(service_id, consul_address, consul_port, logger):
    """
    Deregister service with given id from consul
    """

    c = connect_to_consul(consul_address, consul_port, logger)
    if c is None:
        return

    c.agent.service.deregister(service_id)


def send_request(method_name, params, url, logger, request_id=None):
    """
    Send request with given params and return response (or an error)
    """

    import requests
    import uuid

    if request_id is None:
        request_id = str(uuid.uuid4())

    try:
        # noinspection PyUnresolvedReferences
        requests.packages.urllib3.disable_warnings()
        request = requests.post(url,
                                headers={"Content-Type": "application/json"},
                                json={"jsonrpc": "2.0",
                                      "id": request_id,
                                      "method": method_name,
                                      "params": params},
                                verify=False)
        if request.ok:
            r_result = request.json()
        else:
            r_result = [{"error": {
                "code": request.status_code,
                "message": request.text
            }}]

    except Exception as e:

        logger.log(f"Request error: {e}")
        return [{"error": {
            "code": 123,
            "message": f"Request error: {e}",
            "data": None
        }}]

    return r_result


def get_prometheus_metric_labels(text_metrics):
    """
    Обработать метрики для prometheus.
    Спарсить текстовые (результирующие) метрики в dict,
    добавить в каждую метрику тэг error, который равен false если status есть и
        равен одному из (200, 308), или true если status есть и не равен одному из (200, 308),
    запаковывать dict обратно "как было"
    todo: refactor prometheus metrics export and translate doctring if needed
    """
    from ast import literal_eval
    import re

    for input_to_parse in text_metrics.split(b'\n'):
        input_to_parse = str(input_to_parse)
        match = re.search(r'{.+}', input_to_parse)
        # отсеяли ненужные строки, оставили только метрики
        if match is not None:
            # взяли только ту часть, которая в {} таких скобках
            second_input = match.group(0)

            # заменили все = на :
            match2 = re.sub(r'=', r':', second_input)

            # название каждого тега (все что до :) заключили в "" такие кавычки
            match2 = re.sub(r'([a-zA-Z]+)(:)', r'"\1"\2', match2)

            # в итоге получили python dict в string представлении, преобразуем
            # его в dict
            dictionar = literal_eval(match2)

            # ===============
            # меняем тэги так, как вздумается
            # если есть код статуса отличный от 200 (или 308), считаем что есть ошибка
            status_code = dictionar.get('status', None)
            if (status_code is not None) \
                    and (status_code in ('200', '308')):
                dictionar['error'] = 'false'
            elif (status_code is not None) \
                    and (status_code not in ('200', '308')):
                dictionar['error'] = 'true'

            # указываем subsystem для каждого метода
            client_method = dictionar.get('method', None)
            if client_method == 'getVocabulary':
                dictionar['subsystem'] = 'nsi'

            # ===============

            # после преобразуем обратно
            str_to_put_back = str(dictionar)

            # ' на "
            match3 = re.sub(r'\'', r'"', str_to_put_back)

            # убираем " вокруг ключей и пробел после =
            match3 = re.sub(r'"([a-zA-Z]+)"(:\s)', r'\g<1>=', match3)

            # заменяем исходную строку тэгов на получившуюся
            text_metrics = text_metrics.replace(second_input.encode("utf-8"), match3.encode("utf-8"), 1)

    return text_metrics


def method(flask_request_obj):
    """
    Сгруппировать метрики для prometheus по названию поля method из запроса.
    Непонятно как группировать вызовы нескольких разных методов batch-запросами,
    поэтому берем название метода из первого объекта - в большинстве случаев он будет единственный.
    todo: refactor prometheus metrics export and translate doctring if needed
    """

    if isinstance(flask_request_obj.json, list):
        request_body = flask_request_obj.json[0]
    else:
        request_body = flask_request_obj.json

    if ((flask_request_obj.method == "POST")
            and (is_iterable(request_body))
            and ("method" in request_body)):
        method_str = request_body["method"]
        return f"{method_str}"
    else:
        return f"{flask_request_obj.path}"


# Всё что ниже - функции-скрипты, "api" для service_manager2.sh, те штуки, которые нужны в оболочке сервиса, но мне
# лениво их реализовывать на shell-script
# комментарий из будущего: очень хорошо что я так сделал, теперь легче будет перевести service_manager на python


# noinspection PyPep8Naming
def execute_relog(relog_fl):
    """
    Minimize and sort service logs (files from uwsgi) and show report with details.
    Script-function, service-manager2.sh specific
    """

    import os
    import re
    import datetime
    from pathlib import Path

    # константы

    nohupFile = os.environ.get('nohup_out_log')
    nFile = open(nohupFile, 'a+')
    logger_for_relog = MyLogger(file=nFile)

    REFLOG_FILES_ENV = os.environ.get('RELOG_FILES')

    DELETE_LOGS_ENV = float(os.environ.get('DELETE_LOGS_DAYS'))

    DELETE_RELOG_FILES = relog_fl
    DELETE_RELOG_FILES_ENV = os.environ.get('DELETE_RELOG_FILES')
    if DELETE_RELOG_FILES in [2, '2']:
        DELETE_RELOG_FILES = bool(DELETE_RELOG_FILES_ENV)
        logger_for_relog.log(f'relog flag was not given - using value from config:{DELETE_RELOG_FILES}')

    INFO_ROWS = [
        r'(\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}\]) INFO in app: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}: (user:-*\d{1,} ){0,}remote address: \d{1,3}.\d{1,3}.\d{1,3}.\d{1,3} real IP: \d{1,3}.\d{1,3}.\d{1,3}.\d{1,3} method: [\w.]{1,}',
        r'(\[\d{4}:\d{2}:\d{2}\d{2}:\d{2}:\d{2}\]) - .{5,}',
        r'(\w{3}\s{1,}\w{3}\s{1,}\d{1,3}\s{1,}\d{2}:\d{2}:\d{2} \d{4}) - logsize: \d{1,10}, triggering rotation to [\w\/.]{1,}',
        r'(\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}\]) INFO in app: Start app at [-\d\s:.]{1,}',
        r'(\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}\]) INFO in app: Startup timestamp: [-\d\s:.]{1,}',
        r'\[uWSGI\]() getting INI configuration from [/a-zA-Zа-яА-Я0-9_\.]{1,}',
    ]
    ERROR_WARNING_ROWS = [
        r'\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}\] ERROR in (methods|app):.{1,}'
    ]

    # файлы отсортированные по дате модификации
    logs = sorted(Path('log').iterdir(), key=os.path.getmtime)
    logs_to_proccess = []

    for _log in logs:
        if re.search(REFLOG_FILES_ENV, str(_log)):
            logs_to_proccess.append(str(_log))

    # открываем или создаем файлы с вторичными логами
    # если вторичные логи старше чем RELOG_MULTIPLIER*DELETE_LOGS_ENV - сначала очищаем их
    if not os.path.exists('relog'):
        os.makedirs('relog')
    exceptions_log = open('relog/exceptions.log', 'a+')
    exc_deleted = False
    if DELETE_RELOG_FILES:
        exc_deleted = True
        exceptions_log.close()
        os.remove(exceptions_log.name)
        exceptions_log = open('relog/exceptions.log', 'a+')

    internal_errors_log = open('relog/internal_errors.log', 'a+')
    int_deleted = False
    if DELETE_RELOG_FILES:
        int_deleted = True
        internal_errors_log.close()
        os.remove(internal_errors_log.name)
        internal_errors_log = open('relog/internal_errors.log', 'a+')

    logger_for_relog.log(f'logs_to_proccess = {logs_to_proccess}')

    timestamp_for_file = datetime.datetime.now().strftime(
        '[{[%d-%m-%Y %H:%M:%S]}] - Performing relog'
    )
    internal_errors_log.write(
        timestamp_for_file + '. Those are internal errors, they are caught and returned to clients, usually - no big deal.\n')
    exceptions_log.write(timestamp_for_file + '. Those are uncaught exceptions, you don\'t want these.\n')
    exceptions_log.write(
        'WARNING!!11!1 Timestamp before each line here - isn\'t exact time of exception, it is a previous INFO message\'s timestamp, so DO NOT believe in that time, it\'s just for convenience!!\n')

    exc_updated = False
    int_updated = False
    logfiles_deleted = []
    except_dicts = []
    string_counter = 0
    string_deleted_counter = 0

    for _log in logs_to_proccess:

        file = open(_log, 'r')

        # если поймали эксепшон - выводим инфу об этом и продолжаем.
        try:

            last_info_timestamp = '[[[sorry, no timestamp on this one]]]'

            # определяем, нужна ли каждая строка в этом файле
            for line in file:

                # прокручиваем счётчик
                string_counter += 1

                info = False
                warning = False

                for regex in INFO_ROWS:
                    match = re.match(regex, line)

                    if match:
                        info = True
                        # каждый раз пересохраняем таймштамп 
                        # для записи в exceptions_log
                        last_info_timestamp = '[[' + match.group(1) + ']]'

                for regex in ERROR_WARNING_ROWS:
                    match = re.match(regex, line)

                    if match:
                        warning = True

                if info and not warning:
                    # сообщение - информационное, пропускаем его
                    string_deleted_counter += 1
                    continue
                elif not info and warning:
                    # пишем в internal_errors.log - отданные клиентам ошибки
                    int_updated = True
                    internal_errors_log.write(line)
                elif not info and not warning:
                    # пишем в exceptions.log - эксепшоны
                    exc_updated = True
                    exceptions_log.write(last_info_timestamp + ' - ' + line)

        except Exception as e:
            except_dicts.append(
                {
                    'name': _log,
                    'exception': str(type(e).__name__ + ':' + str(e))
                }
            )

        # удаляем каждый лог старше заданного количества дней
        file_m_time = os.path.getmtime(_log)
        file_m_date = datetime.datetime.fromtimestamp(file_m_time)
        now_date = datetime.datetime.now()
        delta = ((now_date - file_m_date).total_seconds()) / 60 / 60 / 24
        if delta > DELETE_LOGS_ENV:
            logfiles_deleted.append(file.name)
            os.remove(file.name)

        file.close()

    logger_for_relog.log(f'Relog report:')
    logger_for_relog.log(f'---- log strings processed (x): {string_counter}')
    logger_for_relog.log(f'---- log strings ignored (y): {string_deleted_counter}')
    logger_for_relog.log(f'---- log strings written (x-y): {string_counter - string_deleted_counter}')

    if len(logfiles_deleted) > 0:
        logger_for_relog.log(f'---- files older than {DELETE_LOGS_ENV} days were deleted after processing')
        logger_for_relog.log(f'---- files deleted: {len(logfiles_deleted)}:')
        for filename in logfiles_deleted:
            logger_for_relog.log(f'-------- {filename}')

    if len(except_dicts) > 0:
        logger_for_relog.log(f'---- exceptions were observed {len(except_dicts)} times:')
        for logdict in except_dicts:
            logger_for_relog.log(f'-------- {logdict["name"]}:{logdict["exception"]}')

    if exc_deleted:
        logger_for_relog.log(f'---- file {exceptions_log.name} was deleted')

    if int_deleted:
        logger_for_relog.log(f'---- file {internal_errors_log.name} was deleted')

    if exc_updated:
        logger_for_relog.log(f'---- file {exceptions_log.name} was updated')

    if int_updated:
        logger_for_relog.log(f'---- file {internal_errors_log.name} was updated')

    exceptions_log.close()
    internal_errors_log.close()
    nFile.close()


# noinspection PyPep8Naming,DuplicatedCode
def test_api():
    """
    Проводит заданные тесты, выводит результаты на экран и в лог-файл
    Script-function, service-manager2.sh specific
    todo: translate doctring when done with refactoring this function
    todo: формализовать выполнение тестов, а ввод самих тестов вынести в часть, относящуюся к сервису
    """

    import os

    # переменные из конфига
    SERVICE_NAME_ENV = os.environ.get('SERVICE_NAME')
    SERVICE_ID_ENV = os.environ.get('SERVICE_ID')
    CONSUL_ADDRESS_ENV = os.environ.get('CONSUL_ADDRESS')
    CONSUL_PORT_ENV = int(os.environ.get('CONSUL_PORT'))
    SERVER_ADDRESS_ENV = os.environ.get('SERVER_ADDRESS')
    SERVER_PORT_ENV = int(os.environ.get('SERVER_PORT'))

    SERVICE_ADDR_CONF = f'http://{SERVER_ADDRESS_ENV}:{SERVER_PORT_ENV}/'

    nohupFile = os.environ.get('nohup_out_log')
    nFile = open(nohupFile, "a+")
    logger_for_tests = MyLogger(file=nFile)
    color_scheme_green = {'color_pieces': [{'color_back': 'light green', 'colored_text': r'was it successful.:.{1,}'}]}
    color_scheme_red = {'color_pieces': [{'color_back': 'light red', 'colored_text': r'was it successful.:.{1,}'}]}
    # configFile = os.environ.get('config_filename')

    # проверка в консуле, определение окружения
    # noinspection PyDictCreation
    service = {}
    service['name'] = SERVICE_NAME_ENV
    service['id'] = SERVICE_ID_ENV
    service['ip'] = SERVER_ADDRESS_ENV
    service['port'] = SERVER_PORT_ENV
    service['tags'] = ['jsonrpc', 'rest']
    service['checkAddress'] = f'http://{service["ip"]}:{service["port"]}/ping'
    service['checkInterval'] = '10s'

    res_consul = check_service(SERVICE_ID_ENV, CONSUL_ADDRESS_ENV, CONSUL_PORT_ENV, logger_for_tests)
    if res_consul:
        res_consul = 'true'
        service_url = f'http://{service["ip"]}:{service["port"]}/'
    else:
        res_consul = 'false'
        service_url = SERVICE_ADDR_CONF

    logger_for_tests.log(
        f'Checking registration in consul: {SERVICE_NAME_ENV} on {CONSUL_ADDRESS_ENV}:{CONSUL_PORT_ENV} as {SERVER_ADDRESS_ENV}:{SERVER_PORT_ENV} \n\
    result - {res_consul}, must be true on prod.')

    logger_for_tests.log(f'Testing {service_url}.')

    # тестирование методов
    # -----
    method_name = 'pingpong'
    params = {'marco': 'polo'}
    result = send_request(method_name, params, service_url, logger_for_tests)
    exp_res = {'polo': 'marco'}
    testResult = result[0]['result'] == exp_res
    if testResult:
        color_scheme = color_scheme_green
    else:
        color_scheme = color_scheme_red

    logger_for_tests.log(f'+++++\n\
    {method_name} \n\
    request :{params}\n\
    result  :{result[0]["result"]}\n\
    expected:{exp_res}\n\
    was it successful?: {testResult}', color_scheme)

    # =====

    # -----
    method_name = 'pingpong'
    params = {'ping': 'pong'}
    result = send_request(method_name, params, service_url, logger_for_tests)
    exp_res = {'pong': 'ping'}

    logger_for_tests.log(f'+++++\n\
    {method_name} \n\
    request :{params}\n\
    result  :{result[0]["result"]}\n\
    expected:{exp_res}\n\
    was it successful?: {testResult}', color_scheme)
    # =====

    # -----
    method_name = 'pingpong'
    params = {'marco': 'polo'}
    result = send_request(method_name, params, service_url, logger_for_tests)
    exp_res = {'polo': 'marco'}
    testResult = result[0]['result'] != exp_res
    if testResult:
        color_scheme = color_scheme_green
    else:
        color_scheme = color_scheme_red

    logger_for_tests.log(f'+++++\n\
    {method_name} \n\
    request :{params}\n\
    result  :{result[0]["result"]}\n\
    expected:{exp_res}\n\
    this test is not successful intentionally\n\
    was it successful?: {testResult}', color_scheme)

    # =====

    nFile.close()


# noinspection PyPep8Naming,DuplicatedCode
def register_in_consul():
    """
    Registers service in consul or shows error
    Script-function, service-manager2.sh specific
    """

    import os

    # достаём и открываем всё, что нужно

    SERVICE_NAME_ENV = os.environ.get('SERVICE_NAME')
    SERVICE_ID_ENV = os.environ.get('SERVICE_ID')
    CONSUL_ADDRESS_ENV = os.environ.get('CONSUL_ADDRESS')
    CONSUL_PORT_ENV = int(os.environ.get('CONSUL_PORT'))
    SERVER_ADDRESS_ENV = os.environ.get('SERVER_ADDRESS')
    SERVER_PORT_ENV = int(os.environ.get('SERVER_PORT'))

    nohupFile = os.environ.get('nohup_out_log')
    nFile = open(nohupFile, "a+")
    log_for_consulreg = MyLogger(file=nFile)
    configFile = os.environ.get('config_filename')

    # noinspection PyDictCreation
    service = {}
    service['name'] = SERVICE_NAME_ENV
    service['id'] = SERVICE_ID_ENV
    service['ip'] = SERVER_ADDRESS_ENV
    service['port'] = SERVER_PORT_ENV
    service['tags'] = ['jsonrpc', 'rest']
    service['checkAddress'] = f'http://{service["ip"]}:{service["port"]}/ping'
    service['checkInterval'] = '10s'

    # начинаем регистрацию

    log_for_consulreg.log(f'Trying to register {SERVICE_NAME_ENV} on \
{CONSUL_ADDRESS_ENV}:{CONSUL_PORT_ENV} as \
{SERVER_ADDRESS_ENV}:{SERVER_PORT_ENV}.')

    if not (check_service(SERVICE_ID_ENV, CONSUL_ADDRESS_ENV, CONSUL_PORT_ENV, log_for_consulreg)):

        log_for_consulreg.log(f'{SERVICE_NAME_ENV} is not registered on \
{CONSUL_ADDRESS_ENV}:{CONSUL_PORT_ENV} as \
{SERVER_ADDRESS_ENV}:{SERVER_PORT_ENV}, trying to register it.')

        register_service(service, CONSUL_ADDRESS_ENV, CONSUL_PORT_ENV, log_for_consulreg)

        if check_service(SERVICE_ID_ENV, CONSUL_ADDRESS_ENV, CONSUL_PORT_ENV, log_for_consulreg):

            # всё ок, регистрация успешна
            log_for_consulreg.log(f'{SERVICE_NAME_ENV} registered on \
{CONSUL_ADDRESS_ENV}:{CONSUL_PORT_ENV} as \
{SERVER_ADDRESS_ENV}:{SERVER_PORT_ENV} succesfully.')

        else:

            log_for_consulreg.log(f'Something went wrong registering {SERVICE_NAME_ENV} on \
{CONSUL_ADDRESS_ENV}:{CONSUL_PORT_ENV} as \
{SERVER_ADDRESS_ENV}:{SERVER_PORT_ENV}.')

    else:

        # сервис с таким id уже зарегистрирован, что то не так с настройками/конфигом
        log_for_consulreg.log(f'WARNING:{SERVICE_NAME_ENV} is already registered on \
{CONSUL_ADDRESS_ENV}:{CONSUL_PORT_ENV} as \
{SERVER_ADDRESS_ENV}:{SERVER_PORT_ENV}, exiting without register attempt, check your config({configFile}).')

    nFile.close()


# noinspection PyPep8Naming,DuplicatedCode
def deregister_in_consul():
    """
    Deregisters service from consul or shows error
    Script-function, service-manager2.sh specific
    """

    import os

    # достаём и открываем всё, что нужно

    SERVICE_NAME_ENV = os.environ.get('SERVICE_NAME')
    SERVICE_ID_ENV = os.environ.get('SERVICE_ID')
    CONSUL_ADDRESS_ENV = os.environ.get('CONSUL_ADDRESS')
    CONSUL_PORT_ENV = int(os.environ.get('CONSUL_PORT'))
    SERVER_ADDRESS_ENV = os.environ.get('SERVER_ADDRESS')
    SERVER_PORT_ENV = int(os.environ.get('SERVER_PORT'))

    nohupFile = os.environ.get('nohup_out_log')
    nFile = open(nohupFile, "a+")
    log_for_consuldereg = MyLogger(file=nFile)

    # начинаем дерегистрацию
    if check_service(SERVICE_ID_ENV, CONSUL_ADDRESS_ENV, CONSUL_PORT_ENV, log_for_consuldereg):

        log_for_consuldereg.log(f'{SERVICE_NAME_ENV} registered on \
{CONSUL_ADDRESS_ENV}:{CONSUL_PORT_ENV} as \
{SERVER_ADDRESS_ENV}:{SERVER_PORT_ENV}, trying to deregister it.')

        deregister_service(SERVICE_ID_ENV, CONSUL_ADDRESS_ENV, CONSUL_PORT_ENV, log_for_consuldereg)

        if not (check_service(SERVICE_ID_ENV, CONSUL_ADDRESS_ENV, CONSUL_PORT_ENV, log_for_consuldereg)):

            # дерегистрировали, всё ок
            log_for_consuldereg.log(f'{SERVICE_NAME_ENV} deregistered on \
{CONSUL_ADDRESS_ENV}:{CONSUL_PORT_ENV} as \
{SERVER_ADDRESS_ENV}:{SERVER_PORT_ENV} succesfully.')

        else:

            log_for_consuldereg.log(f'WARNING:{SERVICE_NAME_ENV} still registered on \
{CONSUL_ADDRESS_ENV}:{CONSUL_PORT_ENV} as \
{SERVER_ADDRESS_ENV}:{SERVER_PORT_ENV}.')

    else:

        # нет сервиса с таким id
        log_for_consuldereg.log(f'{SERVICE_NAME_ENV} is not registered on \
{CONSUL_ADDRESS_ENV}:{CONSUL_PORT_ENV} as \
{SERVER_ADDRESS_ENV}:{SERVER_PORT_ENV}, no need to deregister it.')

    nFile.close()


# noinspection PyPep8Naming
def check_consul_reg():
    """
    Checks if service specified in config is registered in consul
    Script-function, service-manager2.sh specific
    """

    import os
    import sys

    # SERVICE_NAME_ENV = os.environ.get('SERVICE_NAME')
    SERVICE_ID_ENV = os.environ.get('SERVICE_ID')
    CONSUL_ADDRESS_ENV = os.environ.get('CONSUL_ADDRESS')
    CONSUL_PORT_ENV = int(os.environ.get('CONSUL_PORT'))
    # SERVER_ADDRESS_ENV = os.environ.get('SERVER_ADDRESS')
    # SERVER_PORT_ENV = int(os.environ.get('SERVER_PORT'))

    nohupFile = os.environ.get('nohup_out_log')
    nFile = open(nohupFile, "a+")
    log_for_consulcheck = MyLogger(file=nFile)

    # noinspection PyBroadException
    try:
        check = check_service(SERVICE_ID_ENV, CONSUL_ADDRESS_ENV, CONSUL_PORT_ENV, log_for_consulcheck)
    except Exception:
        check = False

    if check:

        sys.exit(0)

    else:

        sys.exit(1)


def create_temp_dirs():
    """
    Creates temporary folders needed by service
    Script-function, service-manager2.sh specific
    """
    import os
    from pathlib import Path

    # создаем папки для временных файлов
    Path(os.environ['api_directory'] + '/pfe_multiprocess_tmp').mkdir(parents=True, exist_ok=True)
    Path(os.environ['api_directory'] + '/log').mkdir(parents=True, exist_ok=True)
    Path(os.environ['api_directory'] + '/tmp').mkdir(parents=True, exist_ok=True)
