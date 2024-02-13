from abc import ABC, abstractmethod
import time
import requests
import threading
from typing import Tuple, Union
import sys
sys.stdout.flush()

from connector_utils import get_info_ml_service_slurm, start_ml_service_slurm, cancel_ml_service_slurm, create_ssh_tunnel



class ML_service_connector(ABC):
    def __init__(self,
                 ssh_username: str,
                 ssh_key_file: str,
                 remote_host: str,
                 remote_port: str,
                 local_host: str,
                 local_port: str,
                 bash_file: str,
                 check_health_path: str,
                 timeout: int,
                 route_name: str,
                 api_paths: str,
                 name: str = 'ml-service'):
        self.ssh_username = ssh_username
        self.ssh_key_file = ssh_key_file
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.local_host = local_host
        self.local_port = local_port
        self.bash_file = bash_file
        self.check_health_path = check_health_path
        self.route_name = route_name
        self.api_paths = api_paths
        self.name = name
        self.timeout = timeout

        self.ssh_tunnel = None
        self.jobID = None
        self.timer = None
        self.start_time = time.time()
        self.service_startup_enabled = True

    def greet(self) -> None:
        """
        Greets the connector.
        """
        print(f"Connector {self.name}!", flush=True)
    
    @abstractmethod
    def check_connection(self) -> Tuple[bool, bool, Union[None, str]]:
        """
        Checks the connection status.
        Returns a tuple:
        - First element: Indicates if the job exists.
        - Second element: Indicates if the job is running.
        - Third element: Reason for the job not running.
        """
        raise NotImplementedError("Method 'check_connection' must be defined!")
    
    @abstractmethod
    def demand_connection(self) -> Tuple[bool, str]:
        """
        Demands a connection.
        Returns a tuple:
        - First element: Indicates if the connection attempt was successful.
        - Second element: Message indicating the status of the connection attempt.
        """
        raise NotImplementedError("Method 'demand_connection' must be defined!")
    
    @abstractmethod
    def kill_connection(self) -> Union[str, bool]:
        """
        Kills the connection.
        Returns a message indicating the status of the kill attempt.
        """
        raise NotImplementedError("Method 'kill_connection' must be defined!")
    
    @abstractmethod
    def get_service_health(self) -> Union[requests.Response, bool]:
        """
        Retrieves the health status of the service.
        Returns a requests.Response object or False if unable to retrieve.
        """
        raise NotImplementedError("Method 'get_service_health' must be defined!")


    def check_connection_default(self) -> Tuple[bool, bool, Union[None, str]]:
        """
        Default implementation to check connection.
        """
        if self.jobID:
            exist_flag, run_flag, reason = get_info_ml_service_slurm(self.ssh_username, self.ssh_key_file, self.remote_host, self.jobID)
            if exist_flag and run_flag:
                h_check = self.get_service_health()
                print(f'h_check: {h_check}', flush=True)
                if h_check and h_check.status_code==200:
                    return True, True, None
                else:
                    return exist_flag, False, 'Service not yet ready'
            return exist_flag, run_flag, reason
        else:
            return False, False, None

    def demand_connection_default(self) -> Tuple[bool, str]:
        """
        Default implementation to demand a connection.
        """
        if not self.service_startup_enabled:
            return False, 'Service startup disabled!'

        # Check tunnel - if tunnel is not set, open a tunnel
        if not self.ssh_tunnel:
            self.ssh_tunnel = create_ssh_tunnel(self.ssh_username, self.ssh_key_file, self.remote_host, self.local_port, self.remote_port)
        
        # Check service
        exist_flag, run_flag, reason = self.check_connection()
        if not exist_flag:
            self.jobID = None
            res, self.jobID = start_ml_service_slurm(self.ssh_username, self.ssh_key_file, self.remote_host, self.remote_port, self.bash_file)
            if res:
                self.reset_timer()
                self.start_time = time.time()
                return False, 'started'
            else:
                return False, 'error'
        else:
            self.reset_timer()
            if run_flag:
                h_check = self.get_service_health()
                if h_check and h_check.status_code==200:
                    return True, 'running'
                else:
                    return False, 'Service not yet ready'
            else:
                return False, reason

    def kill_connection_default(self) -> Union[str, bool]:
        """
        Default implementation to kill connection.
        """
        # Cancel job
        res = cancel_ml_service_slurm(self.ssh_username, self.ssh_key_file, self.remote_host, self.jobID)
        if res:
            self.jobID = None
            # Close SSH-Tunnel
            self.close_ssh_tunnel()
            # Cancel timer
            self.cancel_timer()
            print('Connection killed!', flush=True)
            print(f'Service ran for {time.time()-self.start_time}', flush=True)
            print("", flush=True)
            return 'kill_connection'
        else:
            print('Connection not killed!', flush=True)
            print("", flush=True)
            return False

    def get_service_health_default(self) -> Union[requests.Response, bool]:
        """
        Default implementation to get service health.
        """
        try:
            x = requests.get(f'http://{self.local_host}:{self.local_port}/{self.check_health_path}')
            return x
        except:
            return False
        
    def set_timer(self, timeout: int = 60) -> None:
        """
        Sets the timer for slurm job life span.
        """
        self.timer = threading.Timer(timeout, self.kill_connection)
        self.timer.start()
    
    def cancel_timer(self) -> None:
        """
        Cancels the timer.
        """
        self.timer.cancel()
        self.timer = None
    
    def reset_timer(self) -> None:
        """
        Resets the timer.
        """
        if self.timer:
            self.cancel_timer()
            self.set_timer(timeout=self.timeout)
            print(f'Reset timer to {self.timeout} seconds.', flush=True)
        else:
            self.set_timer(timeout=self.timeout)
            print(f'Set timer to {self.timeout} seconds.', flush=True)
    
    def close_ssh_tunnel(self) -> None:
        """
        Closes the SSH tunnel.
        """
        if self.ssh_tunnel:
            self.ssh_tunnel.kill()
            self.ssh_tunnel = None
    
    def enable_service_startup(self):
        self.service_startup_enabled = True
    
    def disable_service_startup(self):
        self.service_startup_enabled = False
    
    def kill_and_disable_service_startup(self) -> Union[str, bool]:
        self.service_startup_enabled = False
        resp = self.kill_connection()
        return resp




class Standard_connector(ML_service_connector):
    def __init__(self, ssh_username, ssh_key_file, remote_host, remote_port, local_host, local_port, bash_file, check_health_path, timeout, route_name, api_paths, name='ml-service standard connector'):
        super().__init__(ssh_username, ssh_key_file, remote_host, remote_port, local_host, local_port, bash_file, check_health_path, timeout, route_name, api_paths, name)
 
    def check_connection(self) -> Tuple[bool, bool, Union[None, str]]:
        """
        Checks the connection status.
        """
        return self.check_connection_default()
    
    def demand_connection(self) -> Tuple[bool, str]:
        """
        Demands a connection.
        """
        return self.demand_connection_default()

    def kill_connection(self) -> Union[str, bool]:
        """
        Kills the connection.
        """
        return self.kill_connection_default()

    def get_service_health(self) -> Union[requests.Response, bool]:
        """
        Retrieves the health status of the service.
        """
        return self.get_service_health_default()
    