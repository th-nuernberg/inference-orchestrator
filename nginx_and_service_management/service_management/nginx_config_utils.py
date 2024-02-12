import sys
import json
import time
from connectors import Standard_connector
from flask import Flask, abort, request
import os
sys.stdout.flush()



def load_connectors(json_data):
    connector_list = list()
    for el in json_data['Services']:
        conn = Standard_connector(ssh_username=el['ssh_username'],
                                  ssh_key_file=el['ssh_key_file'],
                                  remote_host=el['remote_host'],
                                  remote_port=el['remote_port'],
                                  local_host=el['local_host'],
                                  local_port=el['local_port'],
                                  bash_file=el['bash_file'],
                                  check_health_path=el['check_health_path'],
                                  timeout=el['timeout'],
                                  route_name=el['route_name'],
                                  api_paths=el['api_paths'],
                                  name=el['name'])
        connector_list.append(conn)
    return connector_list




def define_check_service_function(connector_):
    def check_service():
            status = connector_.check_connection()
            status_ = {'Name': connector_.route_name,
                       'started': status[0],
                       'running': status[1],
                       'reason': status[2]}
            return status_
    return check_service

def define_demand_service_function(connector_):
    def demand_service():
        t1 = time.time()
        resp = connector_.demand_connection()
        print(f'Demand service {connector_.route_name}')
        print(f'Running: {resp[0]} - msg: {resp[1]}', flush=True)
        print(f'Demand time: {time.time()-t1}s', flush=True)
        print(f'method: {request.method}', flush=True)
        print(f'data: {request.data}', flush=True)
        print("", flush=True)
        if resp[0]:
            return f'{connector_.route_name} is ready!', 200
        else:
            abort(503, f'{connector_.route_name} not ready - reason: {resp[1]}')
    return demand_service



def configurate_nginx_and_routes(app, connector_list, flask_port, nginx_listen_port, nginx_conf_template_fn, nginx_conf_output_fn):

    with open(nginx_conf_template_fn) as f:
        nginx_conf = f.read()
    
    nginx_locs = ""
    for connector in connector_list:
        # App routes
        route_name = connector.route_name
        check_route = f"/check_{route_name}"
        demand_route = f"/demand_{route_name}"


        # Generate app routes and functions
        func_check_service = define_check_service_function(connector)
        func_deman_service = define_demand_service_function(connector)

        # Dynamisch benannte Funktionen
        func_check_service.__name__ = check_route
        func_deman_service.__name__ = demand_route

        # Füge Routen hinzu
        app.add_url_rule(f'{check_route}', view_func=func_check_service)
        app.add_url_rule(f'{demand_route}', view_func=func_deman_service)

        print(f'Connector: {connector.name}', flush=True)
        print(f'Check service: {check_route}', flush=True)
        print(f'Demand service: {demand_route}', flush=True)
        print("", flush=True) 



        # Nginx routes
        nginx_locs += f"""

        
        ############ Paths for connector {route_name}
        """

        nginx_locs += f"""
        location = /mirror_{route_name} {{
            internal;
            proxy_set_body '';
            proxy_method GET;
            proxy_pass http://localhost:{flask_port}{demand_route};
        }}
                
        location /demand_{route_name} {{
            proxy_set_body '';
            proxy_method GET;
            proxy_pass http://localhost:{flask_port}{demand_route};
        }}

        location /check_{route_name} {{
            proxy_set_body '';
            proxy_method GET;
            proxy_pass http://localhost:{flask_port}{check_route};
        }}
            """
        
        for path in connector.api_paths:
            nginx_locs += f"""
        location /{route_name}{path} {{
            proxy_pass http://localhost:{connector.local_port}{path};
            error_page 502 = check_{route_name};
            mirror /mirror_{route_name};
        }}
            """
    nginx_prepared = nginx_conf
    nginx_prepared = nginx_prepared.replace('VAR_NGINX_LISTEN_PORT', str(nginx_listen_port))
    nginx_prepared = nginx_prepared.replace('VAR_FLASK_LISTEN_PORT', str(flask_port))
    nginx_prepared = nginx_prepared.replace('###AddNginxEntries###', nginx_locs)


    with open(nginx_conf_output_fn, 'w') as f:
        f.write(nginx_prepared)
    f.close()

    return "Nginx and flask configuration complete."











if __name__ == '__main__':

    with open('./service_management_dynamic_docker_dynNginx/services_config.json') as f:
        json_data = json.load(f)

    with open('./service_management_dynamic_docker_dynNginx/nginx.conf_template') as f:
        nginx_conf = f.read()

    from app import load_connectors

    connector_list = load_connectors(json_data)   
    
    configurate_nginx_and_routes('None', connector_list, json_data['appPort'], nginx_conf)


    a=5




