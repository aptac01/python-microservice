#!env/bin/python
# coding: utf-8

import json
import glob
import re
import importlib  # он используется, чуть пониже
from ast import literal_eval

from flask import current_app as app

# такой конструкцией можно получить доступ сразу ко всем модулям по нужному пути
# после этого все импортированные таким образом модули будут лежать в models,
# пример - в pingPong
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


def get_prometheus_metric_labels(text_metrics):
    """
    Спарсить текстовые (результирующие) метрики в dict,
    добавить в каждую метрику тэг error, который равен false если status есть и
        равен одному из (200, 308), или true если status есть и не равен одному из (200, 308),
    запаковывать dict обратно "как было"
    """
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
    Сгруппировать метрики по названию поля method из запроса
    """

    if ((flask_request_obj.method == "POST")
            and ("method" in flask_request_obj.json)):
        method_str = flask_request_obj.json["method"]
        return f"{method_str}"
    else:
        return f"{flask_request_obj.path}"
