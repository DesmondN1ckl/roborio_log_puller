import argparse
import errno
import os

# import stat
import socket
import pathlib

import paramiko

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

script_dir: pathlib.Path = pathlib.Path(__file__).resolve().parent
local_default_log_dir: pathlib.Path = script_dir / "match_logs"
remote_default_log_dir: pathlib.PurePosixPath = pathlib.PurePosixPath("/home/lvuser/logs")
remote_default_usb_log_dirs: tuple[pathlib.PurePosixPath, pathlib.PurePosixPath] = (pathlib.PurePosixPath("/run/media/lvuser/logs"), pathlib.PurePosixPath("/u/logs"))


def fetch_arguments() -> argparse.Namespace:
    parser.add_argument("-d", "--daemon", help="Enable daemon mode", action='store_true')
    parser.add_argument("-a", "--admin", help="Use admin account instead of lvuser during ssh", action='store_true')
    parser.add_argument(
        "-l", "--log-dir",
        help="Use specified log directory to check for and store downloaded logs",
        type=pathlib.Path,
        default=None)

    return parser.parse_args()

def check_local_logs_dir(path: pathlib.Path = local_default_log_dir) -> None:
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as e:
        print(f"Error creating/checking for logs dir: {e}")

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
    if use_sudo and ssh_user == ssh_admin_user:
        cmd = "sudo -n " + cmd

    _, ssh_stdout, ssh_stderr = ssh_start_cmd(ssh_client=ssh_client, cmd=cmd)
    out = ssh_stdout.read().decode("utf-8", "replace")
    err = ssh_stderr.read().decode("utf-8", "replace")
    exit_code = ssh_stdout.channel.recv_exit_status()

    return (out, err, exit_code)

def ssh_start_cmd(ssh_client: paramiko.SSHClient, cmd: str) -> tuple[paramiko.ChannelFile, paramiko.ChannelFile, paramiko.ChannelFile]:
    return ssh_client.exec_command(cmd) # (in, out, err)

def sftp_connect(ssh_client: paramiko.SSHClient) -> paramiko.SFTPClient:
    return ssh_client.open_sftp()

def sftp_path_exists(sftp_client: paramiko.SFTPClient, path: pathlib.PurePosixPath) -> bool:
    try:
        sftp_client.stat(path=str(path)) # doesn't use return, parses errors instead
    except OSError as e:
        if e.errno in (errno.ENOENT, errno.ENOTDIR):
            return False
        raise
    else:
        return True # (should) return true for any filetype

def sftp_find_log_dirs(sftp_client: paramiko.SFTPClient) -> list[pathlib.PurePosixPath]:
    valid_dirs: list[pathlib.PurePosixPath] = list()

    if sftp_path_exists(sftp_client=sftp_client, path=remote_default_log_dir):
        valid_dirs.append(remote_default_log_dir)

    for path in remote_default_usb_log_dirs:
        if sftp_path_exists(sftp_client=sftp_client, path=path):
            valid_dirs.append(path)

    return valid_dirs

def sftp_listdir(sftp_client: paramiko.SFTPClient, dir: pathlib.PurePosixPath, ignore_errors: bool = True) -> list[pathlib.PurePosixPath]:
    files: list[pathlib.PurePosixPath] = list()

    try:
        _ = (sftp_client.listdir(str(dir)))
        for file in _:
            files.append(pathlib.PurePosixPath(file))
    except OSError:
        if not ignore_errors:
            raise

    return files


def sftp_grab_latest_logs(sftp_client: paramiko.SFTPClient, dirs: list[pathlib.PurePosixPath]) -> list[pathlib.PurePosixPath]:
    logs: list[pathlib.PurePosixPath] = list()
    
    for dir in dirs:

        files: list[pathlib.PurePosixPath] = sftp_listdir(sftp_client=sftp_client, dir=dir)
        for file in files:
            if str(file).endswith(".wpilog"):
                logs.append(dir / file)

    return sorted(logs, reverse=True) # FRC logs are lexigraphically sortable (I'm pretty sure)

def sftp_pull_logs(sftp_client: paramiko.SFTPClient, logs: list[pathlib.PurePosixPath], local_log_dir: pathlib.Path) -> None:
    for file in logs:
        try:
            sftp_client.get(str(file), str(local_log_dir / file.name) )
        except OSError as e:
            print(f"Error pulling {file}: {e}")


if __name__ == "__main__":
    # Set up vars
    args = fetch_arguments()

    daemon_mode = args.daemon
    ssh_user = ssh_admin_user if args.admin else ssh_default_user

    if args.log_dir is None:
        local_log_dir: pathlib.Path = local_default_log_dir
    else:
        local_log_dir: pathlib.Path = args.log_dir.resolve()

    check_local_logs_dir(local_log_dir)
    addr = resolve_roborio()

    # Connect over ssh then open sftp
    ssh_client = ssh_connect(address=addr, username=ssh_user, password="")
    sftp_client = sftp_connect(ssh_client=ssh_client)

    # Find log files
    remote_log_dirs: list[pathlib.PurePosixPath] = sftp_find_log_dirs(sftp_client=sftp_client)
    print(remote_log_dirs) # Debug

    remote_logs: list[pathlib.PurePosixPath] = sftp_grab_latest_logs(sftp_client=sftp_client, dirs=remote_log_dirs)
    print(remote_logs) # Debug

    sftp_pull_logs(sftp_client=sftp_client, logs=remote_logs, local_log_dir=local_log_dir)


    # Disconnect
    sftp_client.close()
    ssh_client.close()