#!env/bin/python
# coding: utf-8

import os
import time, datetime
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, Response, jsonify, abort
from flask import make_response
from flask import request
from prometheus_client import generate_latest, REGISTRY, CONTENT_TYPE_LATEST
from prometheus_flask_exporter.multiprocess import UWsgiPrometheusMetrics 
from methods import pingPong, invalidParameters
from methods import getPrometheusMetricLabels, method

#--------------- flask      ---------------
app = Flask(__name__)

#--------------- app config ---------------
app.config.from_object(os.environ['APP_SETTINGS'])
CONSUL_NAME = app.config['CONSUL_NAME']

#--------------- prometheus ---------------
metrics = UWsgiPrometheusMetrics(app,  
                            group_by = method,
                            defaults_prefix = 'example_python_service',
                            static_labels = {'service':CONSUL_NAME,
                                             'subsystem':'example'}
                            )

#metrics.register_endpoint("/metrics", app)

#--------------- logs       ---------------
LOG_PATH = os.getcwd() + '/log/'
#if not os.path.exists(LOG_PATH):
#    os.makedirs(LOG_PATH)
LOG_FILENAME = f'{LOG_PATH}example.log'
handler = RotatingFileHandler(LOG_FILENAME, backupCount=2, maxBytes=250000)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

now = datetime.datetime.now()
app.logger.info(f'Startup timestamp: {now}')

#--------------- app        ---------------

@app.errorhandler(400)
def incorrect_request(error):
    return make_response(jsonify({'error': 'An incorrect request format'}), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route('/ping/')
@UWsgiPrometheusMetrics.do_not_track()
def ping():
    return 'pong'

@app.route('/metrics', methods=['GET'])
@UWsgiPrometheusMetrics.do_not_track()
def prometheus_metrics():
    
    from prometheus_client import multiprocess, CollectorRegistry

    registry = CollectorRegistry()
    
    if 'name[]' in request.args:
        registry = registry.restricted_registry(request.args.getlist('name[]'))
        
    multiprocess.MultiProcessCollector(registry)

    headers = {'Content-Type': CONTENT_TYPE_LATEST}
    
    metricsResponse = generate_latest(registry)
    metricsResponse = getPrometheusMetricLabels(metricsResponse)
    
    return metricsResponse, 200, headers

@app.route('/', methods=['POST'])
def mainPacketHandler():
    
    request_json = request.json
    result_batch = []
    
    if type(request_json) != type([]) and type(request_json) == type({}):
        
        request_json = [request_json]

    for batch_elem in request_json:
        if (not 'jsonrpc' in batch_elem 
            or batch_elem['jsonrpc'] != '2.0' 
            or not 'id' in batch_elem 
            or not 'method' in batch_elem
            ):
    
            abort(400)
    
        request_id = batch_elem['id']
        method = batch_elem['method']
        params = batch_elem.get('params', {})
        now = datetime.datetime.now()
        # адрес приложения
        ip0 = request.remote_addr
        # адрес пользователя
        ip1 = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        
        app.logger.info(f'{now.strftime("%Y-%m-%dT%H:%M:%S")}: remote address: {ip0} real IP: {ip1} method: {method}')
        
        if (method == 'pingpong'):
            
            result = pingPong(request_id, params)
            
            result_batch.append(result)
        
        else:
            result_batch.append(invalidParameters(request_id))    
    
    return jsonify(result_batch)

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=1234,
        debug=False
    )
    
    