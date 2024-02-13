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

**Configuration**

To configure the environment, follow these steps:

1. Rename the `.env_templates` file to `.env`.
2. Adjust the environment variables in the `.env` file according to your requirements:

   ```bash
   NGINX_PORT=8090
   NGINX_LISTEN_PORT=80

   ML_SERVICE_FLASK_PORT=5001
   ML_SERVICE_SSH_BIND_MOUNT="./ssh_bind_mnt"



    git clone https://github.com/th-nuernberg/inference-orchestrator.git
    cd inference-orchestrator

    Start Docker Containers:

    docker-compose up -d
    docker exec ml_service_management service nginx reload

    or 

    ./start.cmd


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
