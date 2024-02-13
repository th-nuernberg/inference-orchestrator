# ML Service Management with Nginx and Flask

This repository contains a Docker setup for managing Machine Learning (ML) services using Nginx and Flask. The setup orchestrates ML services on a Slurm system, ensuring they are started, stopped, and managed efficiently.

## Overview

The system comprises a Docker container running Nginx and Flask. Nginx acts as a reverse proxy, routing incoming ML service requests to Flask. Flask, in turn, manages the ML services on the Slurm system. In case the corresponding ML service is already running, the user requests are forwarded. Flask is informed about every request via mirroring in order to reset the timeouts.

## Features

- **Dynamic ML Service Management**: Flask dynamically starts, stops, and monitors ML services based on incoming requests.
- **Timeout Handling**: Each ML service is assigned a predefined timeout. Requests to the service reset the timeout timer, ensuring services remain active as long as they're in use.
- **Slurm Integration**: ML services are managed on a Slurm system, leveraging SSH tunnels for communication and control.
- **Scalability**: The setup can handle multiple concurrent ML service requests efficiently. (To-Do: Implement load balancing)

## Setup Instructions

**Download**
```bash
git clone https://github.com/th-nuernberg/inference-orchestrator.git
cd inference-orchestrator
```

**Configuration**

To configure the environment, follow these steps:

1. Rename the `.env_templates` file to `.env`.
2. Adjust the environment variables in the `.env` file according to your requirements:

```bash
NGINX_PORT=8090
NGINX_LISTEN_PORT=80

ML_SERVICE_FLASK_PORT=5001
ML_SERVICE_SSH_BIND_MOUNT="./ssh_bind_mnt"
```

Configure available ML-Service in ./nginx_and_service_management/service_management/services_config.json:

- name: Name of Service
- ssh_username: Username for remote ssh connection
- ssh_key_file: path to ssh keyfile (each service can use differenz credentials)
- remote_host: hostname or ip of remote server
- remote_port: Port of Service on remote server
- local_host: usually localhost
- local_port: Port of service on localhost (usually equal to remote_port)
- bash_file: ML-Service bash file that should be executed to start the service
- check_health_path: api endpoint to check service health status
- timeout: timeout duration in seconds
- route_name: Route name for nginx proxy_pass forwarding
- api_paths: list of api endpoints provided by ML-Service


```bash
{
    "Services":
    [
        {
            "name": "LLM-Vicuna-13b",
            "ssh_username": "simicch",
            "ssh_key_file": "/app/ssh/ssh_20221208_cs",
            "remote_host": "ml1.informatik.fh-nuernberg.de",
            "remote_port": 8083,
            "local_host": "localhost",
            "local_port": 8083,
            "bash_file": "/nfs/scratch/staff/simicch/03_LLM/01_TGI/text-generation-inference/run_vicuna_portx.sh",
            "check_health_path": "health",
            "timeout": 120,
            "route_name": "llm_service",
            "api_paths": [
                "/",
                "/generate",
                "/generate_stream",
                "/health",
                "/info",
                "/metrics",
                "/tokenize",
                "/chat_completions"
            ]
        }
    ]
}

```


**Execute**

Build and Start Docker Container:

```bash
docker-compose -f docker-compose.yaml up --build -d
docker exec ml_service_management service nginx reload
```

or 

```bash
./start.cmd
```



## Access Services

- **Nginx**: Access Nginx server at http://localhost:8090 (default configuration).
- **Flask**: Flask app is available within the Docker container.

## Usage

- Send ML service requests to Nginx, which forwards them to the ML-Service URL and Flask for handling.
- Flask manages the ML services, starting or stopping them as needed.
- To receive information about all available ML services - http:localhost:8090/info

## Configuration

- docker-compose.yaml: Contains the Docker configuration for Nginx and Flask containers.
- .env_template: Name should be changed to .env. Contains some environmental  variables.
- Flask App: Implement ML service management logic within the Flask application.
