from flask import request
import subprocess


def check_host():
    host = request.args.get("host", "localhost")
    return subprocess.run(
        ["echo", "Checking", "host:", str(host)],
        shell=False,
        capture_output=True,
        text=True,
    )
