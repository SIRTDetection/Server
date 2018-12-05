import os

from datetime import datetime, timedelta
from flask import Flask, request, abort, jsonify


def genTokens() -> list:
    from binascii import hexlify

    current_tokens = []
    for i in range(10):
        current_tokens.append({"token": hexlify(os.urandom(24)).decode("utf-8"), "used": False})
    return current_tokens


class WebHook(object):
    app = Flask(__name__)

    def __init__(self):
        import pickle

        self.__clients = {}
        self.__tokens = []
        if os.path.exists("clients"):
            with open("clients") as clients:
                self.__clients = pickle.load(clients)
        if os.path.exists("tokens"):
            with open("tokens") as tokens:
                self.__tokens = pickle.load(tokens)
        else:
            self.__tokens = genTokens()
            with open("tokens") as tokens:
                pickle.dump(self.__tokens, tokens, pickle.HIGHEST_PROTOCOL)

    def start(self):
        self.app.run()

    def updateFiles(self):
        import pickle

        with open("clients") as clients:
            pickle.dump(self.__clients, clients, pickle.HIGHEST_PROTOCOL)

    @app.route("/device/<uuid: device_uuid>", methods=["GET"])
    def registerDeviceOrGetToken(self, device_uuid):
        if device_uuid in self.__clients:
            self.__clients[device_uuid]["latest_connection"] = datetime.now()
            self.updateFiles()
            return jsonify({"token": self.__clients[device_uuid]["token"],
                            "status": 200}), 200
        else:
            if len(self.__clients.keys()) >= 10:
                return jsonify({"token": None,
                                "status": 403}), 403
            else:
                token = ""
                for current_token in self.__tokens:
                    if not current_token["used"]:
                        token = current_token
                        current_token["used"] = True
                        break
                self.__clients[device_uuid] = {"token": token,
                                               "first_connection": datetime.now(),
                                               "latest_connection": datetime.now()}
                self.updateFiles()
                return jsonify({"token": self.__clients[device_uuid]["token"],
                                "status": 200}), 200

    @app.route("/sirt", methods=["POST"])
    def handler(self):
        from io import BytesIO
        from PIL import Image

        token = request.args.get("token")
        if token not in self.__tokens:
            return jsonify({"status": "unauthorized"}), 403
        else:
            uuid = ""
            for key, value in self.__clients.items():
                if value["token"] == token:
                    uuid = key
        self.__clients[uuid]["latest_connection"] = datetime.now()
        self.updateFiles()
        str_img = request.data
        image = Image.open(BytesIO(str_img))
        image_with_boxes = None  # TODO - here TensorFlow is called and process the image
        boxed_image = Image.fromarray(image_with_boxes, "RGB")

        return jsonify({"status": "success",
                        "boxed_image": image_with_boxes}), 200


# tokens = []


"""@app.route("/sirt", methods=["GET", "POST"])
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
    app.run()"""
