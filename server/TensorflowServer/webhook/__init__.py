import os

from datetime import datetime, timedelta
from flask import Flask, request, abort, jsonify

app = Flask(__name__)
authorised_clients = {}


def genTokens() -> list:
    from binascii import hexlify

    current_tokens = []
    for i in range(10):
        current_tokens.append(hexlify(os.urandom(24)).decode("utf-8"))
    return current_tokens


tokens = []


@app.route("/sirt", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        token = request.args.get("token")
        if token in tokens:
            authorised_clients[request.remote_addr] = datetime.now()
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "failed"}), 401
    elif request.method == "POST":
        client = request.remote_addr
        if client in authorised_clients:
            if datetime.now() - authorised_clients.get(client) > timedelta(hours=10):
                authorised_clients.pop(client)
                return jsonify({"status": "auth timeout"}), 401
            else:
                print(request.json)
                return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "not authorised"}), 401
    else:
        abort(400)


if __name__ == '__main__':
    if len(tokens) == 0:
        print("Generating tokens...")
        tokens = genTokens()
        print("Tokens: %s" % tokens)
    else:
        print(tokens)
    app.run()
