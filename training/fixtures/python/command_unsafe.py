from flask import request
import subprocess


def check_host():
    host = request.args.get("host", "localhost")
    command = "echo Checking host: " + str(host)
    return subprocess.run(command, shell=True, capture_output=True, text=True)
