#!env/bin/python
# coding: utf-8

"""
Модуль с реализацией методов сервиса.
Большая часть сервиса обычно здесь.
Также, обычно здесь же и методы для ошибок, т.к. нигде кроме как здесь и в app они не нужны.
"""

import json
import glob
import re
# noinspection PyUnresolvedReferences
import importlib

from flask import current_app as app

# такой конструкцией можно получить доступ сразу ко всем модулям по нужному пути
# после этого все импортированные таким образом модули будут лежать в models,
# пример - в ping_pong
# ---------------------
files = []
modelsList = []
models = {}
for file in glob.glob("./some_directory/*.py"):
    files.append(file)

for name in files:
    string = re.sub(r"\./some_directory/(.+)\.py", r"\1", name)
    
    # ненужные модели
    if string not in ["dont_need_this"]:
        modelsList.append(string)

for model in modelsList:
    models[model] = eval("importlib.import_module(f'some_directory.{model}')")
# ---------------------


def ping_pong(request_id, args):
    """
    Выдать тестовые данные
    """
    
    result = {}
    
    # Представим, что это - сложная бизнес логика
    if args.get("marco", None) is not None\
       and args.get("marco", None) == "polo":
        result = {"polo": "marco"}
        
    if args.get("ping", None) is not None\
       and args.get("ping", None) == "pong":
        result = {"pong": "ping"}
        
    result_dict = {"jsonrpc": "2.0",
                   "result": result,
                   "id": request_id
                   }
    
    # пример доступа к файлам из указанной директории
#    print(models['some_module1'].module1_data)
#    print(models['some_module2'].module2_data)
#    print(models['some_module3'].module3_data)
    
    return result_dict

# Так же, можно представить, что здесь много методов, которые реализуют всё, что
# необходимо для работы конкретно этого сервиса, в большинстве случаев 
# это - любая комбинация нижеприведенных пунктов:
#   
#  * ввод-вывод данных в/из БД
#  * валидация этих самых данных
#  * обработка (преобразование)
#  * сбор сведений из других источников (другие микросервисы, внешние системы)


CURRENCY_CODES = ('RUB', 'USD', 'EUR', 'GBP', 'JPY', 'CNY', 'UAH')
MINIMAL_AMOUNTS = {
    'RUB': 1,
    'USD': 2,
    'EUR': 3,
    'GBP': 4,
    'JPY': 5,
    'CNY': 6,
    'UAH': 7
}


def convert_currency(args):
    """
    Конвертировать одну валюту в другую
    """

    import requests

    from_arg = args.get('from', None)
    to_arg = args.get('to', None)
    amount = args.get('amount', None)

    if from_arg is None \
            or to_arg is None \
            or amount is None:
        return {}

    if from_arg not in CURRENCY_CODES \
            or to_arg not in CURRENCY_CODES:
        return {'error': f'Unknown currency, try one of {CURRENCY_CODES}'}

    if amount < MINIMAL_AMOUNTS[from_arg]:
        return {'error': f'Minimal amount for {from_arg} is {MINIMAL_AMOUNTS[from_arg]}, no less than that'}

    if from_arg == to_arg:
        return {'result': amount}

    # курсы валют якобы от ЦБ РФ
    request = requests.get('https://www.cbr-xml-daily.ru/daily_json.js')
    if request.ok:
        r_result = request.json()
    else:
        return {'error': 'Error connecting to data provider'}

    # чтобы посчитать курс делим value на nominal

    # чтобы пересчитать из рублей во что-то другое - amount/(курс)
    if from_arg == 'RUB':

        course = r_result['Valute'][to_arg]['Value']/r_result['Valute'][to_arg]['Nominal']
        result_amount = amount/course

    # чтобы из нерублей пересчитать в рубли - умножаем amount на курс
    elif to_arg == 'RUB':

        course = r_result['Valute'][from_arg]['Value'] / r_result['Valute'][from_arg]['Nominal']
        result_amount = amount * course

    # в любом другом случае - пересчитываем из чего-то в рубли, а из них - в другие нерубли
    else:

        course_from = r_result['Valute'][from_arg]['Value'] / r_result['Valute'][from_arg]['Nominal']
        course_to = r_result['Valute'][to_arg]['Value']/r_result['Valute'][to_arg]['Nominal']
        result_amount = (amount * course_from)/course_to

    if result_amount < MINIMAL_AMOUNTS[to_arg]:
        return {'error': f'Resulting amount less than minimal. Minimal amount for {to_arg} is {MINIMAL_AMOUNTS[to_arg]}, no less than that'}

    result = {'result': result_amount}

    return result


def returned_error(request_id, error_code, message, data=None, args=None):
    """
    Общая ошибка, для однообразности
    """
    error_text = {"jsonrpc": "2.0",
                  "error": {"code": error_code, "message": message, "data": data, "args": args}, "id": request_id
                  }
    
    app.logger.error(json.dumps(error_text, ensure_ascii=False))
    return error_text


def invalid_parameters(request_id, data=None, args=None):
    """
    Ошибка входных параметров, возникает когда в запросе неверные параметры
    """
    e_code = -12345678
    e_msg = "Неверные параметры"
    return returned_error(request_id, e_code, e_msg, data, args)


def parse_error(request_id, data=None):
    """
    Ошибка с кодом -32700, возникает когда во входном json ошибка
    """
    e_code = -32700
    e_msg = "Parse error"
    return returned_error(request_id, e_code, e_msg, data)
