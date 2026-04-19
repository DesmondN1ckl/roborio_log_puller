import os
import paramiko
import socket

daemon_mode: bool = False
current_dir: str = os.getcwd()
ssh_default_user: str = "lvuser"
ssh_admin_user: str = "admin"
use_admin: bool = False

team_number: int = 112
fallback_roborio_ip: str = "10.1.12.2"
log_dir: str = "match_logs" # in cwd
roborio_mdns: str = f"roboRIO-{team_number}-frc.local"

def check_logs_dir() -> None:
    os.makedirs(log_dir, exist_ok=True)

def ssh_connect(address: str, username: str, password: str) -> paramiko.SSHClient:
    ssh_client: paramiko.SSHClient = paramiko.SSHClient()
    ssh_client.connect(address, username=username, password=password, timeout=3)
    return ssh_client

def ssh_run_command(ssh_client: paramiko.SSHClient, cmd: str) -> str:
    ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(cmd)
    output = ssh_stdout.read().decode() # wait for command to return

    return output

def ssh_disconnect(ssh_client: paramiko.SSHClient) -> None:
    ssh_client.close()

def resolve_roborio() -> str:
    try:
        response = socket.gethostbyname(roborio_mdns)
    except socket.gaierror:
        response = fallback_roborio_ip

    return response

if (__name__ == "__main__"):
    check_logs_dir()
    addr = resolve_roborio()
    user: str = ssh_default_user

    if use_admin:
        user = ssh_admin_user

    ssh_client = ssh_connect(addr, user, "")

    # future logic

    ssh_disconnect(ssh_client)