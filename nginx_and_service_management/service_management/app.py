from flask import Flask, abort, request, jsonify
import json
from nginx_config_utils import configurate_nginx_and_routes, load_connectors
# import docker
import os
import sys
sys.stdout.flush()




# List of available Services
app = Flask(__name__)
CONNECTOR_LIST = list()

@app.route('/')
def ml_service_management():
    """
    Endpoint for managing ML services.
    Starts ML services such as LLM models upon request and shuts them down after a defined period of inactivity.
    """
    # Your code for managing ML services goes here

    return "ML service management endpoint"

@app.route('/get_service_info', methods=['GET'])
def get_service_info():
    print('get_service_info', flush=True)
    # app.logger.info('Processing default request')
    service_info = {'All available services': []}
    
    for connector in CONNECTOR_LIST:
        status = connector.check_connection()
        status_service_management_enabled = connector.service_startup_enabled
        status_dict = {
            'started': status[0],
            'running': status[1],
            'reason': status[2],
            'management_enabled': status_service_management_enabled
        }
        service_data = {
            'service_name': connector.name,
            'service_status': status_dict
        }
        service_info['All available services'].append(service_data)
    
    return jsonify(service_info)



@app.route('/enable_service_management', methods=['GET'])
def enable_service_management():
    for conn in CONNECTOR_LIST:
        conn.enable_service_startup()
    return jsonify(message="Service management enabled"), 200

@app.route('/disable_service_management', methods=['GET'])
def disable_service_management():
    for conn in CONNECTOR_LIST:
        conn.disable_service_startup()
    return jsonify(message="Service management disabled"), 200

@app.route('/kill_disable_service_management', methods=['GET'])
def kill_disable_service_management():
    for conn in CONNECTOR_LIST:
        conn.kill_and_disable_service_startup()
    return jsonify(message="Service management disabled and all services killed"), 200




if __name__ == '__main__':

    # Get Ports from global env
    flask_port = os.getenv("ML_SERVICE_FLASK_PORT")
    nginx_listen_port = os.getenv("NGINX_LISTEN_PORT")

    # Load json_data
    with open('./services_config.json') as f:
        json_data = json.load(f)
    
    # Generate connectors from services_config.json content
    CONNECTOR_LIST = load_connectors(json_data)

    # Nginx and app configuration
    nginx_conf_template_fn = '/app/nginx.conf_template'
    nginx_conf_output_fn = '/etc/nginx/nginx.conf'
    resp = configurate_nginx_and_routes(app, CONNECTOR_LIST, flask_port, nginx_listen_port, nginx_conf_template_fn, nginx_conf_output_fn)
    print(resp, flush=True)

    print("", flush=True)
    
    app.run(host='0.0.0.0', port=os.getenv("ML_SERVICE_FLASK_PORT"))
