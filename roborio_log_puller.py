import os
import paramiko
import socket

daemon_mode = False
current_dir = os.getcwd()
ssh = paramiko.SSHClient()

team_number = 112
log_dir = "match_logs"
roborio_mdns = f"roboRIO-{team_number}-frc.local"
fallback_roborio_ip = "10.1.12.2"


def check_logs_dir():
    os.makedirs(log_dir, exist_ok=True)

def connect():
    ssh.connect(fallback_roborio_ip, username="lvuser", password="")

def run_command(cmd):
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
    output = ssh_stdout.read().decode() # wait for command to return

    return output

def disconnect():
    ssh.close()

def resolve_dns():
    try:
        response = socket.gethostbyname(roborio_mdns)
    except socket.gaierror as e:
        response = fallback_roborio_ip

    return response

if (__name__ == "__main__"):
    check_logs_dir()
    