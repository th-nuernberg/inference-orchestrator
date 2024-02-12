import paramiko
import subprocess
import re
import requests
from subprocess import Popen
from typing import Tuple, Union
import sys
sys.stdout.flush()


def create_ssh_tunnel(ssh_username: str, 
                      ssh_key_file: str, 
                      remote_host: str, 
                      local_port: int, 
                      remote_port: int) -> Union[Popen, None]:
    """
    Establishes an SSH tunnel from localhost to a remote host.
    
    Parameters:
        ssh_username (str): The username for SSH connection.
        ssh_key_file (str): The path to the SSH private key file.
        remote_host (str): The remote host to establish the tunnel with.
        local_port (int): The local port to bind the tunnel to.
        remote_port (int): The remote port to tunnel to on the remote host.
        
    Returns:
        Popen or None: The subprocess Popen object representing the SSH tunnel process if successful, None otherwise.
    """
    tunnel_process = None
    # SSH command for tunnel
    ssh_command = [
        'ssh',
        '-4',
        '-o StrictHostKeyChecking=no',
        '-i', ssh_key_file,
        '-N',
        '-L', f'localhost:{local_port}:localhost:{remote_port}',
        f'{ssh_username}@{remote_host}'
    ]
    # Start SSH tunnel
    try:
        tunnel_process = subprocess.Popen(ssh_command)
        x = requests.get(f'http://localhost:{local_port}')
        print(f'Check tunnel: {x}', flush=True)
        print(f"Tunnel process: {tunnel_process}", flush=True)
        print("SSH tunnel established.", flush=True)
    except Exception as e:
        print(f"Error establishing tunnel: {e}", flush=True)
    return tunnel_process


def start_ml_service_slurm(ssh_username: str, 
                           ssh_key_file: str, 
                           remote_host: str, 
                           remote_port: int, 
                           bash_file: str) -> Tuple[bool, Union[str, None]]:
    """
    Starts an ML service on a remote host using SLURM job submission.
    
    Parameters:
        ssh_username (str): The username for SSH connection.
        ssh_key_file (str): The path to the SSH private key file.
        remote_host (str): The remote host where SLURM job is to be executed.
        remote_port (int): The port on the remote host to be used.
        bash_file (str): The path to the bash script file to be executed.
        
    Returns:
        Tuple[bool, Union[str, None]]: A tuple indicating success (True or False) and the job ID (if successful, else None).
    """
    # SSH connection
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(remote_host, username=ssh_username, key_filename=ssh_key_file)
    
    # sbatch job command
    sbatch_command: str = f"sbatch {bash_file} {remote_port}"
    
    # Execute sbatch command
    stdin, stdout, stderr = ssh.exec_command(sbatch_command)
    output: str = stdout.read().decode().strip()
    errors: str = stderr.read().decode().strip()
    jobID: Union[str, None] = output.strip('Submitted batch job ')
    
    # Logging and return
    if output:
        print("SLURM job started ...", flush=True)
        print(f"Job ID: {output}", flush=True)
        # Close SSH connection
        ssh.close()
        return True, jobID
    else:
        print(f"SLURM job could not be started: {errors}", flush=True)
        return False, None


def cancel_ml_service_slurm(ssh_username: str, ssh_key_file: str, remote_host: str, jobID: str) -> bool:
    """
    Function to cancel a SLURM job running on a remote host via SSH.

    Args:
        ssh_username (str): Username for SSH connection.
        ssh_key_file (str): File path to SSH private key.
        remote_host (str): Hostname or IP address of the remote machine.
        jobID (str): ID of the SLURM job to be canceled.

    Returns:
        bool: True if the SLURM job is canceled successfully, False otherwise.
    """
    # SSH-Connection
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(remote_host, username=ssh_username, key_filename=ssh_key_file)
    
    # sbatch-Job command
    sbatch_command = f"scancel {jobID}"
    
    # Execute sbatch command
    stdin, stdout, stderr = ssh.exec_command(sbatch_command)
    output = stdout.read().decode().strip()
    errors = stderr.read().decode().strip()
    
    # Logging and return
    if not errors:
        print("SLURM-Job canceled ...", flush=True)
        print(f"Job-ID: {jobID}", flush=True)
        # Close SSH-Connection
        ssh.close()
        return True
    else:
        print(f"SLURM-Jobs could not be canceled: {errors}", flush=True)
        return False


def get_info_ml_service_slurm(ssh_username: str, ssh_key_file: str, remote_host: str, jobID: str) -> Tuple[bool, bool, Union[None, str]]:
    """
    Checks if a SLURM job with jobID is running. If it's pending, return the reason.
    If it's not running, return False.    
    
    Args:
        ssh_username (str): Username for SSH connection.
        ssh_key_file (str): File path to SSH private key.
        remote_host (str): Hostname or IP address of the remote machine.
        jobID (str): ID of the SLURM job to check.
    
    Returns:
        Tuple[bool, bool, Union[None, str]]: 
            - (True, True, None) if the job is running and there is no problem.
            - (True, True, str) if the job is pending with a reason (str).
            - (False, False, None) if there's no job with jobID.
    """
    # SSH-Connection
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(remote_host, username=ssh_username, key_filename=ssh_key_file)
    
    # sbatch-Job command
    sbatch_command = f"scontrol show jobid -dd {jobID}"
    
    # Execute sbatch command
    stdin, stdout, stderr = ssh.exec_command(sbatch_command)
    output = stdout.read().decode().strip()
    errors = stderr.read().decode().strip()
    
    pairs = re.split(r'[ \n,]', output)
    pairs = list(filter(None, pairs))
    data = {}
    
    for pair in pairs:
        try:
            key, value = pair.split('=', maxsplit=1)
            data[key] = value
        except ValueError:
            pass
    
    # Logging and return
    if len(data) > 0:
        if data.get('JobState') == 'RUNNING':
            print("SLURM-Job is running ...", flush=True)
            print("Job-ID:", jobID, flush=True)
            # Close SSH-Connection
            ssh.close()
            return True, True, None
        else:
            reason = data.get('Reason', None)
            print(f"SLURM-Job {jobID} not running - reason: {reason}", flush=True)
            return True, False, reason
    else:
        print(f"SLURM-Job {jobID} does not exist!", flush=True)
        return False, False, None

