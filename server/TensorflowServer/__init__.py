import os
import six.moves.urllib as urllib
import tarfile
import traceback

from argparse import ArgumentParser

from TensorflowServer.object_detection.utils import (ops as utils_ops,
                                                     label_map_util,
                                                     visualization_utils as vis_utils)
from TensorflowServer.utils.Constants import (M_DEFAULT_MODEL,
                                              M_GRAPH,
                                              M_LABELS)
from TensorflowServer.tensorflow_worker import Tensorflow
from TensorflowServer.webhook import WebHook

__program_name__ = """TensorFlow Server client"""
__program_executable__ = "TensorflowServer"
__program_description__ = """The TensorFlow Server API listening to devices requests. By using object_detection API, 
looks for objects contained at the image given"""

"""if StrictVersion(tf.__version__) < StrictVersion('1.9.0'):
    raise ImportError("At least, TensorFlow:1.9.0 is needed. Please, upgrade your installation")"""


def is_website_available(url: str) -> bool:
    from urllib.request import urlopen
    return urlopen(url).getcode() == 200


def main(arg):
    use_mobilenet_v1 = arg.mobilenet_v1
    use_mobilenet_v2 = arg.mobilenet_v2
    use_faster_rcnn = arg.faster_rcnn
    custom_model = arg.custom

    # default_model = "ssd_mobilenet_v2_quantized_300x300_coco_2018_09_14"
    download_base_url = "http://download.tensorflow.org/models/object_detection/"
    download_extension = ".tar.gz"

    if use_mobilenet_v1 and use_mobilenet_v2 and use_faster_rcnn:
        raise AttributeError("Only one Coco trained mobile can be used for detecting images!")
    if use_mobilenet_v1:
        model_name = "ssd_mobilenet_v1_ppn_shared_box_predictor_300x300_coco14_sync_2018_07_03"
    elif use_mobilenet_v2:
        model_name = M_DEFAULT_MODEL
    elif use_faster_rcnn:
        model_name = "faster_rcnn_resnet101_coco_2018_01_28.tar.gz"
    elif custom_model is not None:
        model_name = custom_model
    else:
        model_name = M_DEFAULT_MODEL

    download_url = download_base_url + model_name + download_extension
    if not is_website_available(download_url):
        raise ConnectionError("The following URL: \"" + download_url + "\" is not valid!")

    path_to_frozen_graph = model_name + "/" + M_GRAPH
    # path_to_labels = os.path.join("data", M_LABELS)

    if not os.path.exists(path_to_frozen_graph):
        downloader = urllib.request.URLopener()
        downloader.retrieve(download_url, model_name + download_extension)
        tar_file = tarfile.open(model_name + download_extension)
        for file in tar_file.getmembers():
            filename = os.path.basename(file.name)
            if M_GRAPH in filename:
                tar_file.extract(file, os.getcwd())
    Tensorflow(model=model_name)
    webhook_runner = WebHook()
    webhook_runner.run()


if __name__ == '__main__':
    arguments = ArgumentParser(prog=__program_name__,
                               usage=__program_executable__,
                               description=__program_description__)
    arguments.add_argument("--mobilenet_v1",
                           action="store_true",
                           help="Uses MobileNet V1 PPN Coco trained model")
    arguments.add_argument("--mobilenet_v2",
                           action="store_true",
                           help="Uses MobileNet V2 Quantized Coco trained model")
    arguments.add_argument("--faster_rcnn",
                           action="store_true",
                           help="Uses Faster RCNN Resnet 101 Coco trained model")
    arguments.add_argument("--custom",
                           type=str,
                           default=None,
                           help="Uses a custom Coco trained model. It must have the following structure "
                                "(omit '<', '>' characters):\n"
                                "\"<model_name>_<extra_specs>_<release_date>\".\n"
                                "You can find all the available models here: "
                                "https://github.com/tensorflow_worker/models/blob/master/research/object_detection/"
                                "g3doc/detection_model_zoo.md#coco-trained-models")
    args = arguments.parse_args()
    try:
        main(args)
    except Exception as e:
        print(e)
        traceback.print_exc()
        exit(-1)
