from typing import Tuple

import numpy as np
import os
import tensorflow as tf

from distutils.version import StrictVersion
from PIL import Image

from TensorflowServer.object_detection.utils import (ops as utils_ops,
                                                     label_map_util,
                                                     visualization_utils as vis_utils)
from TensorflowServer.utils.Constants import (M_DEFAULT_MODEL,
                                              M_GRAPH,
                                              M_LABELS,
                                              T_KEYS)

if StrictVersion(tf.__version__) < StrictVersion('1.9.0'):
    raise ImportError('Please upgrade your TensorFlow installation to v1.9.* or later!')


class Tensorflow(object):
    class __Tensorflow:
        def __init__(self, model: str = None, image_size: Tuple = (12, 8)):
            self.__model = model
            self.__detection_graph = tf.Graph()
            with self.__detection_graph.as_default():
                od_graph_def = tf.GraphDef()
                with tf.gfile.GFile(self.__model + '/' + M_GRAPH, "rb") as fid:
                    serialized_graph = fid.read()
                    od_graph_def.ParseFromString(serialized_graph)
                    tf.import_graph_def(od_graph_def, name='')
            self.__category_index = label_map_util.create_category_index_from_labelmap(os.path.join('data', M_LABELS),
                                                                                       use_display_name=True)
            self.__image_size = image_size

        @staticmethod
        def load_image_into_numpy_array(image: Image.Image) -> np.ndarray:
            (img_width, img_height) = image.size
            return np.array(image.getdata()).reshape((img_height, img_width, 3)).astype(np.uint8)

        def _run_inference_on_single_image(self, image) -> dict:
            with self.__detection_graph.as_default():
                with tf.Session() as sess:
                    ops = tf.get_default_graph().get_operations()
                    all_tensors_name = {output.name for op in ops for output in op.outputs}
                    tensor_dict = {}
                    for key in T_KEYS:
                        tensor_name = key + ':0'
                        if tensor_name in all_tensors_name:
                            tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(tensor_name)
                    if 'detection_masks' in tensor_dict:
                        detection_boxes = tf.squeeze(tensor_dict["detection_boxes"], [0])
                        detection_masks = tf.squeeze(tensor_dict["detection_masks"], [0])
                        real_number_of_detections = tf.cast(tensor_dict["num_detections"][0], tf.int32)
                        detection_boxes = tf.slice(detection_boxes, [0, 0], [real_number_of_detections, -1])
                        detection_masks = tf.slice(detection_masks, [0, 0, 0], [real_number_of_detections, -1, -1])
                        detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(detection_masks,
                                                                                              detection_boxes,
                                                                                              image.shape[0],
                                                                                              image.shape[1])
                        detection_masks_reframed = tf.cast(tf.greater(detection_masks_reframed, 0.5), tf.uint8)
                        tensor_dict["detection_masks"] = tf.expand_dims(detection_masks_reframed, 0)
                        image_tensor = tf.get_default_graph().get_tensor_by_name("image_tensor:0")
                        output_dict = sess.run(tensor_dict, feed_dict={image_tensor: np.expand_dims(image, 0)})
                        output_dict["num_detections"] = int(output_dict["num_detections"][0])
                        output_dict["detection_classes"] = output_dict["detection_classes"][0].astype(np.uint8)
                        output_dict["detection_boxes"] = output_dict["detection_boxes"][0]
                        output_dict["detection_scores"] = output_dict["detection_scores"][0]
                        if "detection_masks" in output_dict:
                            output_dict["detection_masks"] = output_dict["detection_masks"][0]
            return output_dict

        def detect_objects(self, image) -> np.ndarray:
            # image = Image.open(image_path)
            numpy_image = self.load_image_into_numpy_array(image)
            numpy_image_expanded = np.expand_dims(numpy_image, axis=0)
            output = self._run_inference_on_single_image(numpy_image)
            vis_utils.visualize_boxes_and_labels_on_image_array(
                numpy_image,
                output["detection_boxes"],
                output["detection_classes"],
                output["detection_scores"],
                self.__category_index,
                instance_masks=output.get("detection_masks"),
                use_normalized_coordinates=True,
                line_thickness=8
            )
            return numpy_image
            # plt.figure(figsize=self.__image_size)

    __instance = None

    def __new__(cls, *args, **kwargs):
        if not Tensorflow.__instance:
            model = kwargs.get("model", M_DEFAULT_MODEL)
            image_size = kwargs.get("size", (12, 8))
            Tensorflow.__instance = Tensorflow.__Tensorflow(model, image_size)
        return Tensorflow.__instance

    def __getattr__(self, item):
        return getattr(self.__instance, item)

    def __setattr__(self, key, value):
        return setattr(self.__instance, key, value)

    def detect_objects(self, image_path: str) -> np.ndarray:
        return self.__instance.detect_objects(image_path)
