import os

from datetime import datetime
from flask import Flask, request, jsonify, send_file, logging

from TensorflowServer.tensorflow_worker import Worker
from TensorflowServer.utils import LoggingHandler

app = Flask(__name__)
_clients = {}
_tokens = []
_tf = None
_log = LoggingHandler()


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
    custom_logs = LoggingHandler().getLoggers()
    app.logger.removeHandler(logging.default_handler)
    for custom_log in custom_logs:
        handlers = custom_log.handlers
        for handler in handlers:
            app.logger.addHandler(handler)
    app.run()


def _updateFiles():
    import pickle

    with open("clients", "wb") as clients:
        pickle.dump(_clients, clients, pickle.HIGHEST_PROTOCOL)


@app.route("/device/<uuid>", methods=["GET"])
def _registerDeviceOrToken(uuid: str):
    global _clients

    _log.info("New device petition received")
    if uuid in _clients:
        _log.debug("Device is already registered\nUUID: {}".format(uuid))
        _clients[uuid]["latest_connection"] = datetime.now()
        _updateFiles()
        return jsonify({"token": _clients[uuid]["token"],
                        "status": 200}), 200
    else:
        _log.debug("New device UUID: {}".format(uuid))
        if len(_clients.keys()) >= 10:
            _log.warning("Maximum clients reached (10)")
            return jsonify({"token": None,
                            "status": 403}), 403
        else:
            _log.debug("Registering a new client. Client number #{}".format(len(_clients.keys())))
            token = ""
            for current_token in _tokens:
                if not current_token["used"]:
                    token = current_token["token"]
                    current_token["used"] = True
                    break
            _clients[uuid] = {"token": token,
                              "first_connection": datetime.now(),
                              "latest_connection": datetime.now()}
            _log.debug("Client UUID: {}".format(uuid))
            _log.debug("Client token: {}".format(token))
            _log.debug("First connection: {}".format(_clients[uuid]["first_connection"]
                                                     .strftime("%H:%M:%S %Z @ %Y/%m/%d")))
            _log.debug("Latest connection: {}".format(_clients[uuid]["latest_connection"]
                                                      .strftime("%H:%M:%S %Z @ %Y/%m/%d")))
            _updateFiles()
            return jsonify({"token": _clients[uuid]["token"],
                            "status": 200}), 200


@app.route("/sirt", methods=["POST"])
def _handleImages():
    from time import clock
    from io import BytesIO
    from PIL import Image

    global _clients

    token = request.args.get("token")
    found = False
    _log.info("New petition received!")
    _log.debug("User token: {}".format(token))
    for current_token in _tokens:
        if current_token["token"] == token:
            found = True
            break
    if not found:
        _log.warning("Unauthorized user - token not found in tokens")
        return jsonify({"status": "unauthorized"}), 403
    else:
        uuid = ""
        for key, value in _clients.items():
            if value["token"] == token:
                uuid = key
    _log.debug("User UUID: {}".format(uuid))
    _clients[uuid]["latest_connection"] = datetime.now()
    _log.debug("First connection: {}".format(_clients[uuid]["first_connection"]
                                             .strftime("%H:%M:%S %Z @ %Y/%m/%d")))
    _log.debug("Latest connection: {}".format(_clients[uuid]["latest_connection"]
                                              .strftime("%H:%M:%S %Z @ %Y/%m/%d")))
    _updateFiles()
    str_img = request.data
    _log.debug("Starting object inference...")
    start_time = clock()
    image_with_boxes = _tf.detect_objects(str_img)
    _log.debug("Inference took %.2f seconds" % (clock() - start_time))
    boxed_image = Image.fromarray(image_with_boxes, "RGB")
    image_io = BytesIO()
    boxed_image.save(image_io, "PNG", quality=100)
    image_io.seek(0)
    _log.debug("Sending file...")
    return send_file(image_io, mimetype="image/png")
