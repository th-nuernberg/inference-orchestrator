#!/bin/bash

docker-compose -f docker-compose.yaml up --build -d
docker exec ml_service_management service nginx reload
docker exec ml_service_management nginx
