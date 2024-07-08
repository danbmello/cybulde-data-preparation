import logging
import socket

from subprocess import CalledProcessError, run

# import subprocess


# Function to get a Python logger
def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"[{socket.gethostname()}] {name}")


# Function to run shell commands
# def run_shell_command(cmd: str) -> str:
#     return subprocess.run(cmd, text=True, shell=True, check=True, capture_output=True).stdout


def run_shell_command(cmd: str) -> str:
    try:
        result = run(cmd, text=True, shell=True, check=True, capture_output=True)
        logging.info(f"Command '{cmd}' executed successfully.")
        logging.info(f"stdout: {result.stdout}")
        logging.info(f"stderr: {result.stderr}")
        return result.stdout
    except CalledProcessError as e:
        logging.error(f"Command '{cmd}' failed with return code {e.returncode}")
        logging.error(f"stdout: {e.stdout}")
        logging.error(f"stderr: {e.stderr}")
        raise