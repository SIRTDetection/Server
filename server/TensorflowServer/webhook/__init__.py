import os

from datetime import datetime
from flask import Flask, request, jsonify, send_file

from TensorflowServer.tensorflow_worker import Worker

app = Flask(__name__)
_clients = {}
_tokens = []
_tf = None


def genTokens() -> list:
    from binascii import hexlify

    current_tokens = []
    for i in range(10):
        current_tokens.append({"token": hexlify(os.urandom(24)).decode("utf-8"), "used": False})
    return current_tokens


def run():
    import pickle

    global _clients
    global _tokens
    global _tf

    if os.path.exists("clients"):
        with open("clients", "rb") as clients:
            _clients = pickle.load(clients)
    if os.path.exists("tokens"):
        with open("tokens", "rb") as tokens:
            _tokens = pickle.load(tokens)
    else:
        _tokens = genTokens()
        with open("tokens", "wb") as tokens:
            pickle.dump(_tokens, tokens, pickle.HIGHEST_PROTOCOL)
    _tf = Worker()
    app.run()


def _updateFiles():
    import pickle

    with open("clients", "wb") as clients:
        pickle.dump(_clients, clients, pickle.HIGHEST_PROTOCOL)


@app.route("/device/<uuid>", methods=["GET"])
def _registerDeviceOrToken(uuid: str):
    global _clients

    if uuid in _clients:
        _clients[uuid]["latest_connection"] = datetime.now()
        _updateFiles()
        return jsonify({"token": _clients[uuid]["token"],
                        "status": 200}), 200
    else:
        if len(_clients.keys()) >= 10:
            return jsonify({"token": None,
                            "status": 403}), 403
        else:
            token = ""
            for current_token in _tokens:
                if not current_token["used"]:
                    token = current_token["token"]
                    current_token["used"] = True
                    break
            _clients[uuid] = {"token": token,
                              "first_connection": datetime.now(),
                              "latest_connection": datetime.now()}
            _updateFiles()
            return jsonify({"token": _clients[uuid]["token"],
                            "status": 200}), 200


@app.route("/sirt", methods=["POST"])
def _handleImages():
    from io import BytesIO
    from PIL import Image

    global _clients

    token = request.args.get("token")
    print(token)
    found = False
    for current_token in _tokens:
        print(current_token)
        if current_token["token"] == token:
            found = True
            break
    if not found:
        return jsonify({"status": "unauthorized"}), 403
    else:
        uuid = ""
        for key, value in _clients.items():
            print((key, value))
            print(value["token"])
            if value["token"] == token:
                uuid = key
        print(uuid)
    _clients[uuid]["latest_connection"] = datetime.now()
    _updateFiles()
    str_img = request.data
    # image = Image.open(BytesIO(str_img))
    image_with_boxes = _tf.detect_objects(str_img)
    boxed_image = Image.fromarray(image_with_boxes, "RGB")
    image_io = BytesIO()
    boxed_image.save(image_io, "PNG", quality=100)
    image_io.seek(0)
    return send_file(image_io, mimetype="image/png")

# class WebHook(object):
#     def __init__(self):
#         import pickle
#
#         self.__clients = {}
#         self.__tokens = []
#         if os.path.exists("clients"):
#             with open("clients", "rb") as clients:
#                 self.__clients = pickle.load(clients)
#         if os.path.exists("tokens"):
#             with open("tokens", "rb") as tokens:
#                 self.__tokens = pickle.load(tokens)
#         else:
#             self.__tokens = genTokens()
#             with open("tokens", "wb") as tokens:
#                 pickle.dump(self.__tokens, tokens, pickle.HIGHEST_PROTOCOL)
#         self.__tf = Tensorflow()
#         self.__app = Flask(__name__)
#
#     def run(self):
#         self.__app.run()
#
#     def updateFiles(self):
#         import pickle
#
#         with open("clients") as clients:
#             pickle.dump(self.__clients, clients, pickle.HIGHEST_PROTOCOL)
#
#     # @app.route("/device/<uuid>", methods=["GET"])
#     def _registerDeviceOrGetToken(self):
#
#         @self.__app.route("/device/<uuid>", methods=["GET"])
#         def registerDeviceOrGetToken(uuid: str):
#             if uuid in self.__clients:
#                 self.__clients[uuid]["latest_connection"] = datetime.now()
#                 self.updateFiles()
#                 return jsonify({"token": self.__clients[uuid]["token"],
#                                 "status": 200}), 200
#             else:
#                 if len(self.__clients.keys()) >= 10:
#                     return jsonify({"token": None,
#                                     "status": 403}), 403
#                 else:
#                     token = ""
#                     for current_token in self.__tokens:
#                         if not current_token["used"]:
#                             token = current_token
#                             current_token["used"] = True
#                             break
#                     self.__clients[uuid] = {"token": token,
#                                             "first_connection": datetime.now(),
#                                             "latest_connection": datetime.now()}
#                     self.updateFiles()
#                     return jsonify({"token": self.__clients[uuid]["token"],
#                                     "status": 200}), 200
#
#     # @app.route("/sirt", methods=["POST"])
#     def _handler(self):
#
#         @self.__app.route("/sirt", methods=["POST"])
#         def handler():
#             from io import BytesIO
#             from PIL import Image
#
#             token = request.args.get("token")
#             if token not in self.__tokens:
#                 return jsonify({"status": "unauthorized"}), 403
#             else:
#                 uuid = ""
#                 for key, value in self.__clients.items():
#                     if value["token"] == token:
#                         uuid = key
#             self.__clients[uuid]["latest_connection"] = datetime.now()
#             self.updateFiles()
#             str_img = request.data
#             image = Image.open(BytesIO(str_img))
#             image_with_boxes = self.__tf.detect_objects(image)
#             boxed_image = Image.fromarray(image_with_boxes, "RGB")
#             image_io = BytesIO()
#             boxed_image.save(image_io, "PNG", quality=100)
#             image_io.seek(0)
#             return send_file(image_io, mimetype="image/png")

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
