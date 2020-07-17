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
