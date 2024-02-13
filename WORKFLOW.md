# System Workflow for Client Requests

In this document, we describe the workflow of handling client requests in the ML service management system using Nginx and Flask.

## Request Handling Workflow - Scenario 1

In this scenario, we outline the workflow for handling a client request when ML-Service 1 is not running.

1. **Client Request for ML-Service 1**:
   - A user/client submits a request for ML-Service 1.

2. **Nginx Proxy Pass Error**:
   - Nginx forwards the request via proxy_pass to the corresponding URL.
   - However, an error occurs as ML-Service 1 is not yet running.

3. **Invocation of demand_service() Function**:
   - Simultaneously, the demand_service() function of the Flask app is invoked.

4. **Establishment of SSH Tunnel**:
   - The Flask app establishes an SSH tunnel between the container and the target server for the corresponding port of ML-Service 1.

5. **Start of Slurm Job**:
   - The Flask app initiates the Slurm job on the target server, which executes ML-Service 1.

6. **Start of Timer for ML-Service 1**:
   - The Flask app starts the timer for ML-Service 1, defining how long the service will continue to run if no new requests are received.


<br/>
<p align="center">
   <img src="./imgs/WORKFLOW_01.png" alt="Client Request Flow Diagram - Scenario 1" width="600">
</p>


## Request Handling Workflow - Scenario 2

In this scenario, we outline the workflow for handling a client request when ML-Service 1 is already running.

1. **Client Request for ML-Service 1**:
   - A user/client submits a request for ML-Service 1.

2. **Nginx Proxy Pass**:
   - Nginx forwards the request via proxy_pass to the corresponding URL.

3. **Invocation of demand_service() Function**:
   - Simultaneously, the demand_service() function of the Flask app is invoked.

4. **Resetting Timer for ML-Service 1**:
   - The timer for ML-Service 1 is reset, indicating that the service is still active and handling requests.

<br/>
<p align="center">
   <img src="./imgs/WORKFLOW_02.png" alt="Client Request Flow Diagram - Scenario 2" width="600">
</p>

## Conclusion

This Git repository offers a robust solution for efficiently managing ML services on a Slurm system. By leveraging Docker containers to orchestrate Nginx and a Flask app, the platform provides a centralized environment for seamless service management.

Nginx efficiently directs incoming requests to active ML services, ensuring communication between clients and running services. In cases where a requested ML service is not yet running, the Flask app steps in, dynamically running up the service and establishing an SSH tunnel to facilitate communication.

The system implements automated timer management, assigning each ML service a predefined timeout period. Upon expiry, the service is gracefully shut down, and the associated SSH tunnel will be closed, optimizing resource utilization.

The Flask app continuously monitors requests to ML services and resetting timers upon each request to ensure uninterrupted service availability. ML services must be defined manually, the startup and shutdown procedures, is automated.

Through this solution, users can effectively manage and scale ML services, streamlining deployment, ensuring reliability, and maximizing resource efficiency on a Slurm system.


## Next Steps

Our next focus for the Git repository includes implementing load balancing between equivalent services. This enhancement will allow the system to handle peaks in incoming requests by dynamically starting multiple instances of a service on different ports. By distributing requests across these instances, we aim to improve system performance and ensure reliability, especially during periods of high demand.

