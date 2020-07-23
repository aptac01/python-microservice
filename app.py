#!env/bin/python
# coding: utf-8

"""
Модуль основного приложения, который паралелится через uwsgi
Теоретически, можно запустить его напрямую (в dev-окружении), но иногда это неэффективно,
или (как в случае с экспортом метрик в prometheus) работает некорректно (смотри отличия
prometheus_flask_exporter.multiprocess от prometheus_flask_exporter)
"""

import os
import datetime
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, abort, Request
from flask import make_response
from flask import request
# noinspection PyProtectedMember
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from prometheus_flask_exporter.multiprocess import UWsgiPrometheusMetrics 
from methods import ping_pong, invalid_parameters
from methods import parse_error, convert_currency
from service_manager_lib import get_prometheus_metric_labels, method

# --------------- flask      ---------------
app = Flask(__name__)

# --------------- app config ---------------
app.config.from_object(os.environ['APP_SETTINGS'])
CONSUL_NAME = app.config['CONSUL_NAME']

# --------------- prometheus ---------------
metrics = UWsgiPrometheusMetrics(app,  
                                 group_by=method,
                                 defaults_prefix='example_python_service',
                                 static_labels={'service': CONSUL_NAME,
                                                'subsystem': 'example'}
                                 )

# --------------- logs       ---------------
LOG_PATH = os.getcwd() + '/log/'
LOG_FILENAME = f'{LOG_PATH}example.log'
handler = RotatingFileHandler(LOG_FILENAME, backupCount=2, maxBytes=250000)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

now = datetime.datetime.now()
app.logger.info(f'Startup timestamp: {now}')

# --------------- app        ---------------


# noinspection PyUnusedLocal
@app.errorhandler(400)
def incorrect_request(error):
    """
    Обработать ошибку с кодом 400
    """
    return make_response(jsonify({'error': 'An incorrect request format'}), 400)


# noinspection PyUnusedLocal
@app.errorhandler(404)
def not_found(error):
    """
    Обработать ошибку с кодом 404
    """
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/ping/')
@UWsgiPrometheusMetrics.do_not_track()
def ping():
    """
    Подтвердить, что сервис "жив", ответить на проверку consul'а
    """
    return 'pong'


@app.route('/metrics', methods=['GET'])
@UWsgiPrometheusMetrics.do_not_track()
def prometheus_metrics():
    """
    Отдать метрики для prometheus'а
    """
    
    # noinspection PyProtectedMember
    from prometheus_client import multiprocess, CollectorRegistry

    registry = CollectorRegistry()
    
    if 'name[]' in request.args:
        registry = registry.restricted_registry(request.args.getlist('name[]'))
        
    multiprocess.MultiProcessCollector(registry)

    headers = {'Content-Type': CONTENT_TYPE_LATEST}
    
    metrics_response = generate_latest(registry)
    metrics_response = get_prometheus_metric_labels(metrics_response)
    
    return metrics_response, 200, headers


# noinspection PyUnusedLocal
def on_json_loading_failed(self, e):
    """
    Вернуть специальную метку и описание возникшей ошибки в объекте запроса
    в случае, если не удалось спарсить json из запроса клиента
    """
    if e is not None:
        return {
            'e': e,
            'on_json_loading_failed': 1
                }


Request.on_json_loading_failed = on_json_loading_failed


@app.route('/', methods=['POST'])
def another_handler():
    """
    Вызвать main_packet_handler без параметра
    """
    return main_packet_handler(None)


# noinspection PyUnusedLocal
@app.route('/<var_route>', methods=['POST'])
def main_packet_handler(var_route):
    """
    Обработать запрос(ы) к сервису.
    Обработает как единственный запрос ({....data...}), так и batch запрос ([{}, {}, {}])
    """
    
    request_json = request.json
    result_batch = []

    # оборачиваем одиночный запрос в []
    if (not isinstance(request_json, list)) \
            and isinstance(request_json, dict):
        
        request_json = [request_json]

    for batch_elem in request_json:

        # если при парсинге json из запроса произошла ошибка - пытаемся помочь пользователю понять где она
        if 'e' in batch_elem\
           and 'on_json_loading_failed' in batch_elem:
            result_batch.append(parse_error(None, str(batch_elem['e'])))
            continue
        
        if ('jsonrpc' not in batch_elem
                or batch_elem['jsonrpc'] != '2.0'
                or 'id' not in batch_elem
                or 'method' not in batch_elem):
    
            abort(400)
    
        request_id = batch_elem['id']
        method_from_client = batch_elem['method']
        params = batch_elem.get('params', {})
        datetime_now = datetime.datetime.now()
        # адрес приложения
        ip0 = request.remote_addr
        # адрес пользователя
        ip1 = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        
        app.logger.info(f'{datetime_now.strftime("%Y-%m-%dT%H:%M:%S")}: remote address: {ip0} real IP: {ip1} method: {method_from_client}')
        
        if method_from_client == 'pingpong':
            
            result = ping_pong(request_id, params)
            
            result_batch.append(result)

        elif method_from_client == 'convert':

            result = convert_currency(params)

            result_batch.append(result)
        
        else:
            result_batch.append(invalid_parameters(request_id))
    
    return jsonify(result_batch)


if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=1234,
        debug=False
    )
