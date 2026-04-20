import os
import paramiko
import socket
import argparse
# import stat

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

def resolve_roborio() -> str:
    try:
        response = socket.gethostbyname(roborio_hostname)
    except socket.gaierror:
        response = fallback_roborio_ip

    return response


def ssh_connect(address: str, username: str, password: str) -> paramiko.SSHClient:
    ssh_client: paramiko.SSHClient = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh_client.connect(address,
        username=username,
        password=password,
        timeout=3,
        banner_timeout=3,
        auth_timeout=3,
        channel_timeout=3,
        look_for_keys=False,
        allow_agent=False)

    return ssh_client

def ssh_exec(ssh_client: paramiko.SSHClient, cmd: str) -> tuple[str, str, int]:
    _, ssh_stdout, ssh_stderr = ssh_start_cmd(ssh_client=ssh_client, cmd=cmd)
    out = ssh_stdout.read().decode()
    err = ssh_stderr.read().decode()
    exit_code = ssh_stdout.channel.recv_exit_status()

    return (out, err, exit_code)

def ssh_start_cmd(ssh_client: paramiko.SSHClient, cmd: str) -> tuple[paramiko.ChannelFile, paramiko.ChannelFile, paramiko.ChannelFile]:
    return ssh_client.exec_command(cmd) # (in, out, err)

def ssh_disconnect(ssh_client: paramiko.SSHClient) -> None:
    ssh_client.close()

def sftp_connect(ssh_client: paramiko.SSHClient) -> paramiko.SFTPClient:
    return ssh_client.open_sftp()

def sftp_dir_exists(sftp_client: paramiko.SFTPClient, path: str) -> bool:
    try:
        sftp_client.stat(path=path)
    except Exception:
        return False
    else:
        return True

if __name__ == "__main__":
    args = fetch_arguments()

    daemon_mode = args.daemon
    ssh_user = ssh_admin_user if args.admin else ssh_default_user
    log_dir = args.log_dir

    check_logs_dir()
    addr = resolve_roborio()

    ssh_client = ssh_connect(address=addr, username=ssh_user, password="")
    sftp_client = sftp_connect(ssh_client=ssh_client)

    

    # Disconnect
    ssh_disconnect(ssh_client)