import os

from datetime import datetime
from flask import Flask, request, jsonify, send_file

from ..tensorflow import Tensorflow


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
        self.__tf = Tensorflow()

    def start(self):
        self.app.run()

    def updateFiles(self):
        import pickle

        with open("clients") as clients:
            pickle.dump(self.__clients, clients, pickle.HIGHEST_PROTOCOL)

    @app.route("/device/<uuid>", methods=["GET"])
    def registerDeviceOrGetToken(self, uuid: str):
        if uuid in self.__clients:
            self.__clients[uuid]["latest_connection"] = datetime.now()
            self.updateFiles()
            return jsonify({"token": self.__clients[uuid]["token"],
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
                self.__clients[uuid] = {"token": token,
                                               "first_connection": datetime.now(),
                                               "latest_connection": datetime.now()}
                self.updateFiles()
                return jsonify({"token": self.__clients[uuid]["token"],
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
        image_with_boxes = self.__tf.detect_objects(image)
        boxed_image = Image.fromarray(image_with_boxes, "RGB")
        image_io = BytesIO()
        boxed_image.save(image_io, "PNG", quality=100)
        image_io.seek(0)
        return send_file(image_io, mimetype="image/png")

    # @app.route("/sirt/training", methods=["POST"])
    # def train(self):
    #     from io import BytesIO
    #     from PIL import Image
    #
    #     token = request.args.get("token")
    #     if token not in self.__tokens:
    #         return jsonify({"status": "unauthorized"}), 403
    #     else:
    #         uuid = ""
    #         for key, value in self.__clients.items():
    #             if value["token"] == token
    #                 uuid = key
    #     self.__clients[uuid]["latest_connection"] = datetime.now()
    #     self.updateFiles()
    #     str_img = request.data
