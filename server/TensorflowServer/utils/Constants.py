M_DEFAULT_MODEL = "ssd_mobilenet_v2_quantized_300x300_coco_2018_09_14"
M_GRAPH = "frozen_inference_graph.pb"
M_LABELS = "mscoco_label_map.pbtxt"

T_KEYS = ['num_detections', 'detection_boxes', 'detection_scores', 'detection_classes', 'detection_masks']

W_DEFAULT_MODEL_URL = "https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1"
W_MODELS = {
    "MobilenetV2": "https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1",
    "Faster RCNN": "https://tfhub.dev/google/faster_rcnn/openimages_v4/inception_resnet_v2/1"
}

L_CONSOLE = "console_logger"
L_FILE = "file_logger"
L_FILENAME = "TensorflowServer.log"
