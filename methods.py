#!env/bin/python
# coding: utf-8

import json
import glob
import re
import importlib
from ast import literal_eval

from flask import current_app as app
from flask import jsonify

# такой конструкцией можно получить доступ сразу ко всем модулям по нужному пути
# после этого все импортированные таким образом модули будут лежать в models,
# пример - в pingPong
#---------------------
files = []
modelsList = []
models = {}
for file in glob.glob("./some_directory/*.py"):
    files.append(file)

for name in files:
    string = re.sub(r"\.\/some_directory\/(.{1,})\.py", r"\1", name)
    
    # ненужные модели
    if string not in ["dont_need_this"]:
        modelsList.append(string)

for model in modelsList:
    models[model] = eval("importlib.import_module(f'some_directory.{model}')")
#---------------------

# тестовый метод
def pingPong(request_id, args):
    
    result = {}
    
    # Представим, что это - сложная бизнес логика
    if args.get("marco", None) is not None\
       and args.get("marco", None) == "polo":
        result = {"polo":"marco"}
        
    if args.get("ping", None) is not None\
       and args.get("ping", None) == "pong":
        result = {"pong":"ping"}
        
    resultDict = {"jsonrpc": "2.0",
                  "result": result,
                  "id":request_id
        }    
    
    # пример доступа к файлам из указанной директории
#    print(models['some_module1'].module1_data)
#    print(models['some_module2'].module2_data)
#    print(models['some_module3'].module3_data)
    
    return resultDict

# Так же, можно представить, что здесь много методов, которые реализуют всё, что
# необходимо для работы конкретно этого сервиса, в большинстве случаев 
# это - любая комбинация нижеприведенных пунктов:
#   
#  * ввод-вывод данных в/из БД
#  * валидация этих самых данных
#  * обработка (преобразование)
#  * сбор сведений из других источников (другие микросервисы, внешние системы)

# возвращение ошибок
def returnedError(request_id, error_code, message, data = None, args = None):
    errorText = {"jsonrpc": "2.0",
              "error": {"code": error_code, "message": message, "data": data, "args":args}, "id": request_id}
    
    app.logger.error(json.dumps(errorText, ensure_ascii=False))
    return errorText

def invalidParameters(request_id, data=None, args = None):
    e_code = -12345678
    e_msg = "Неверные параметры"
    return returnedError(request_id, e_code, e_msg, data, args)

def parseError(request_id, data = None):
    e_code = -32700
    e_msg = "Parse error"
    return returnedError(request_id, e_code, e_msg, data)

# парсит текстовые (результирующие) метрики в dict, 
# добавляет в каждую метрику тэг error, который равен false если status есть и 
#   равен одному из (200, 308), или true если status есть и не равен одному из (200, 308), 
# запаковывает dict обратно "как было"
def getPrometheusMetricLabels(textMetrics):
    
    for inputToParse in textMetrics.split(b"\n"):
        inputToParse = str(inputToParse)
        match = re.search("{.+}", inputToParse)
        # отсеяли ненужные строки, оставили только метрики
        if match is not None:
            # взяли только ту часть, которая в {} таких скобках
            secondInput = match.group(0)
            
            # заменили все = на :
            match2 = re.sub("=", ":", secondInput)
            
            # название каждого тега (все что до :) заключили в "" такие кавычки
            match2 = re.sub("([a-zA-Z]+)(:)", "\"\g<1>\"\g<2>", match2)
            
            # в итоге получили python dict в string представлении, преобразуем 
            # его в dict
            dictionar = literal_eval(match2)
            
            #===============
            # меняем тэги так, как вздумается
            # если есть код статуса отличный от 200 (или 308), считаем что есть ошибка
            statusCode = dictionar.get("status", None)
            if (statusCode is not None) \
               and (statusCode in ("200", "308")):
                dictionar["error"] = "false"
            elif (statusCode is not None) \
               and (statusCode not in ("200", "308")):
                dictionar["error"] = "true"
            
            # указываем subsystem для каждого метода
            method    = dictionar.get("method", None)
            if (method == "getVocabulary"):
                dictionar["subsystem"] = "nsi"
            
            #===============
            
            # после преобразуем обратно
            strToPutBack = str(dictionar)
            
            # ' на "
            match3 = re.sub("\'", "\"", strToPutBack)
            
            # убираем " вокруг ключей и пробел после =
            match3 = re.sub("\"([a-zA-Z]+)\"(:\s)", "\g<1>=", match3)
            
            # заменяем исходную строку тэгов на получившуюся
            textMetrics = textMetrics.replace(secondInput.encode("utf-8"), match3.encode("utf-8"), 1)
            
    return textMetrics

# Правило для группировки метрик
def method(FlaskRequestObj):
    
    retStr = ''
    if ((FlaskRequestObj.method == "POST") 
        and ("method" in FlaskRequestObj.json)):
        method = FlaskRequestObj.json["method"]
        return f"{method}"
    else:
        return f"{FlaskRequestObj.path}"
