import os
import socket
import errno
import argparse
# import stat

import paramiko
from paramiko import sftp

parser: argparse.ArgumentParser = argparse.ArgumentParser(
                    prog='Roborio log puller',
                    description='Helps to automate pulling logs and parsing them',
                    epilog='Bottom text')

ssh_default_user: str = "lvuser"
ssh_admin_user: str = "admin"
ssh_user: str = ssh_default_user

team_number: int = 112
fallback_roborio_ip: str = "10.1.12.2"
roborio_hostname: str = f"roboRIO-{team_number}-frc.local"

local_log_dir: str = "match_logs" # in cwd
remote_default_log_dir: str = "/home/lvuser/logs"
remote_usb_log_dirs: tuple[str, str] = ("/run/media/lvuser/logs", "/u/logs")


def fetch_arguments() -> argparse.Namespace:
    parser.add_argument("-d", "--daemon", help="Enable daemon mode", action='store_true')
    parser.add_argument("-a", "--admin", help="Use admin account instead of lvuser during ssh", action='store_true')
    parser.add_argument("-l", "--log-dir", help="Use specified log directory to check for and store downloaded logs", type=str, default=local_log_dir)
    return parser.parse_args()

def check_logs_dir() -> None:
    os.makedirs(local_log_dir, exist_ok=True)

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

def ssh_exec(ssh_client: paramiko.SSHClient, cmd: str, use_sudo: bool = False) -> tuple[str, str, int]:
    if use_sudo:
        cmd = "sudo " + cmd

    _, ssh_stdout, ssh_stderr = ssh_start_cmd(ssh_client=ssh_client, cmd=cmd)
    out = ssh_stdout.read().decode("utf-8", "replace")
    err = ssh_stderr.read().decode("utf-8", "replace")
    exit_code = ssh_stdout.channel.recv_exit_status()

    return (out, err, exit_code)

def ssh_start_cmd(ssh_client: paramiko.SSHClient, cmd: str) -> tuple[paramiko.ChannelFile, paramiko.ChannelFile, paramiko.ChannelFile]:
    return ssh_client.exec_command(cmd) # (in, out, err)

def ssh_disconnect(ssh_client: paramiko.SSHClient) -> None:
    ssh_client.close()

def sftp_connect(ssh_client: paramiko.SSHClient) -> paramiko.SFTPClient:
    return ssh_client.open_sftp()

def sftp_path_exists(sftp_client: paramiko.SFTPClient, path: str) -> bool:
    try:
        sftp_client.stat(path=path) # doesn't use return, parses errors instead
    except IOError as e:
        if e.errno in (errno.ENOENT, errno.ENOTDIR):
            return False
        raise
    else:
        return True # (should) return true for any filetype

def sftp_find_log_dir(sftp_client: paramiko.SFTPClient) -> set[str]:
    valid_dirs: set[str] = set()

    if sftp_path_exists(sftp_client=sftp_client, path=remote_default_log_dir):
        valid_dirs.add(remote_default_log_dir)

    for path in remote_usb_log_dirs:
        if sftp_path_exists(sftp_client=sftp_client, path=path):
            valid_dirs.add(path)

    return valid_dirs

if __name__ == "__main__":
    # Set up vars
    args = fetch_arguments()

    daemon_mode = args.daemon
    ssh_user = ssh_admin_user if args.admin else ssh_default_user
    local_log_dir = args.log_dir

    check_logs_dir()
    addr = resolve_roborio()

    # Connect over ssh then open sftp
    ssh_client = ssh_connect(address=addr, username=ssh_user, password="")
    sftp_client = sftp_connect(ssh_client=ssh_client)

    remote_log_dir: set[str] = sftp_find_log_dir(sftp_client=sftp_client)





    # Disconnect
    sftp_client.close()
    ssh_disconnect(ssh_client)