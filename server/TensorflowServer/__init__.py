import traceback
import logging

from argparse import ArgumentParser
from flask.logging import wsgi_errors_stream

from TensorflowServer.object_detection.utils import (ops as utils_ops,
                                                     label_map_util,
                                                     visualization_utils as vis_utils)
from TensorflowServer.utils.Constants import (W_DEFAULT_MODEL_URL,
                                              L_CONSOLE,
                                              L_FILE)
from TensorflowServer.tensorflow_worker import Worker
from TensorflowServer.webhook import run
from TensorflowServer.utils import (setup_logging,
                                    setup_console_logging,
                                    LoggingHandler)

__program_name__ = """TensorFlow Server client"""
__program_executable__ = "TensorflowServer"
__program_description__ = """The TensorFlow Server API listening to devices requests. By using object_detection API, 
looks for objects contained at the image given"""


def is_website_available(url: str) -> bool:
    from urllib.request import urlopen
    return urlopen(url).getcode() == 200


def main(arg):
    # use_mobilenet_v1 = arg.mobilenet_v1
    use_mobilenet_v2 = arg.mobilenet_v2
    use_faster_rcnn = arg.faster_rcnn
    custom_model = arg.custom
    log_to_console = arg.no_console
    setup_logging(L_FILE, "TensorflowServer.log")
    if log_to_console:
        setup_console_logging(L_CONSOLE, wsgi_errors_stream)
    else:
        setup_console_logging(L_CONSOLE, None)

    log = LoggingHandler(logs=[logging.getLogger(L_CONSOLE), logging.getLogger(L_FILE)])
    log.info("Running TensorflowServer - initializing Tensorflow, models and more...")

    if use_mobilenet_v2 and use_faster_rcnn:
        log.error("Only one model can be used at once, not two")
        log.error("Exiting...")
        raise AttributeError("Only one Coco trained mobile can be used for detecting images!")
    if use_mobilenet_v2:
        log.debug("Using Mobilenet V2")
        model_name = W_DEFAULT_MODEL_URL
    elif use_faster_rcnn:
        log.debug("Using Faster RCNN")
        model_name = "https://tfhub.dev/google/faster_rcnn/openimages_v4/inception_resnet_v2/1"
    elif custom_model is not None:
        log.debug("Using custom model")
        log.info("Model info: {}".format(custom_model))
        model_name = custom_model
    else:
        log.debug("Using default model (Mobilenet V2)")
        model_name = W_DEFAULT_MODEL_URL

    log.debug("Setting up the Tensorflow Worker")
    Worker(model=model_name)
    log.debug("Starting webhook...")
    run()


if __name__ == '__main__':
    arguments = ArgumentParser(prog=__program_name__,
                               usage=__program_executable__,
                               description=__program_description__)
    arguments.add_argument("--mobilenet_v2",
                           action="store_true",
                           help="Uses MobileNet V2 Quantized Coco trained model")
    arguments.add_argument("--faster_rcnn",
                           action="store_true",
                           help="Uses Faster RCNN Resnet 101 Coco trained model")
    arguments.add_argument("--custom",
                           type=str,
                           default=None,
                           help="Uses a custom model available at: \"https://tfhub.dev/\" - you must include the full "
                                "model URL. For example, for \"Mobilenet V2\": "
                                "https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1")
    arguments.add_argument("--no_console",
                           action="store_true",
                           help="The server application does not log to console")
    args = arguments.parse_args()
    try:
        main(args)
    except KeyboardInterrupt:
        try:
            key_log = LoggingHandler()
            key_log.warning("Received KeyboardInterrupt! Finishing...")
            key_log.info("Stopping server...")
        except AttributeError:
            print("Finishing...")
        finally:
            exit(0)
    except Exception as e:
        ex = traceback.format_exc()
        try:
            exc_log = LoggingHandler()
            exc_log.exception("Unhandled exception occurred - exception info: {}".format(e))
        except AttributeError:
            print(e)
            print(ex)
        finally:
            exit(-1)
