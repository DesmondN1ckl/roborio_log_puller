import os
import paramiko
import socket
import argparse
# import time

parser: argparse.ArgumentParser = argparse.ArgumentParser(
                    prog='Roborio log puller',
                    description='Helps to automate pulling logs and parsing them',
                    epilog='Bottom text')

daemon_mode: bool = False
ssh_default_user: str = "lvuser"
ssh_admin_user: str = "admin"
ssh_user: str = ssh_default_user

team_number: int = 112
fallback_roborio_ip: str = "10.1.12.2"
log_dir: str = "match_logs" # in cwd
roborio_hostname: str = f"roboRIO-{team_number}-frc.local"

def fetch_arguments() -> argparse.Namespace:
    parser.add_argument("-d", "--daemon", help="Enable daemon mode", action='store_true')
    parser.add_argument("-a", "--admin", help="Use admin account instead of lvuser during ssh", action='store_true')
    parser.add_argument("-l", "--log-dir", help="Use specified log directory", type=str, default=log_dir)
    return parser.parse_args()

def check_logs_dir() -> None:
    os.makedirs(log_dir, exist_ok=True)

def ssh_connect(address: str, username: str, password: str) -> paramiko.SSHClient:
    ssh_client: paramiko.SSHClient = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh_client.connect(address,
        username=username,
        password=password,
        timeout=3,
        look_for_keys=False,
        allow_agent=False)

    return ssh_client

def ssh_run_command(ssh_client: paramiko.SSHClient, cmd: str) -> str:
    ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command(cmd)
    output = ssh_stdout.read().decode() # wait for command to return

    return output

def ssh_disconnect(ssh_client: paramiko.SSHClient) -> None:
    ssh_client.close()

def resolve_roborio() -> str:
    try:
        response = socket.gethostbyname(roborio_hostname)
    except socket.gaierror:
        response = fallback_roborio_ip

    return response

if (__name__ == "__main__"):
    args = fetch_arguments()

    daemon_mode = args.daemon
    ssh_user = ssh_admin_user if args.admin else ssh_default_user
    log_dir = args.log_dir

    check_logs_dir()
    addr = resolve_roborio()

    ssh_client = ssh_connect(addr, ssh_user, "")

    # future logic

    ssh_disconnect(ssh_client)