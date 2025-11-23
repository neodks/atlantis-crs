from flask import Flask, request
import subprocess

app = Flask(__name__)

@app.route("/run")
def run():
    cmd = request.args.get("cmd")
    # This is a command injection vulnerability
    subprocess.run(cmd, shell=True)
    return "OK"

if __name__ == "__main__":
    app.run()
