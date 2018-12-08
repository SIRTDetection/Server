from typing import Tuple

import numpy as np
import os
import tensorflow as tf
import tensorflow_hub as hub

from distutils.version import StrictVersion
from PIL import (Image,
                 ImageColor,
                 ImageDraw,
                 ImageFont,
                 ImageOps)

from TensorflowServer.object_detection.utils import (ops as utils_ops,
                                                     label_map_util,
                                                     visualization_utils as vis_utils)
from TensorflowServer.utils.Constants import (M_DEFAULT_MODEL,
                                              M_GRAPH,
                                              M_LABELS,
                                              T_KEYS,
                                              W_DEFAULT_MODEL_URL)

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


class Worker(Tensorflow):
    class __Worker(object):
        def __init__(self, model_url: str = None):
            self.__model_url = model_url
            self.__detection_graph = tf.Graph()
            with self.__detection_graph.as_default():
                detector = hub.Module(model_url)
                self.__image_string_placeholder = tf.placeholder(tf.string)
                self.__decoded_image = tf.image.decode_jpeg(self.__image_string_placeholder)
                decoded_image_float = tf.image.convert_image_dtype(image=self.__decoded_image, dtype=tf.float32)
                module_input = tf.expand_dims(decoded_image_float, 0)
                self.__result = detector(module_input, as_dict=True)
                init_ops = [tf.global_variables_initializer(), tf.tables_initializer()]

                self.__session = tf.Session()
                self.__session.run(init_ops)

        @staticmethod
        def _resize_image(image: Image, new_width: int = 256, new_height: int = 256) -> Image:
            image = ImageOps.fit(image, (new_width, new_height), Image.ANTIALIAS)
            image_rgb = image.convert("RGB")
            return image_rgb

        @staticmethod
        def _draw_bounding_box_on_image(image: Image.Image,
                                        yMin: float,
                                        xMin: float,
                                        yMax: float,
                                        xMax: float,
                                        color,
                                        font,
                                        thickness: int = 4,
                                        display_str_list: list = ()):
            draw = ImageDraw.Draw(image)
            img_width, img_height = image.size
            (left, right, top, bottom) = (xMin * img_width, xMax * img_width, yMin * img_height, yMax * img_height)
            draw.line([(left, top), (left, bottom), (right, bottom), (right, top), (left, top)],
                      width=thickness,
                      fill=color)

            display_str_heights = [font.getsize(ds)[1] for ds in display_str_list]
            total_display_str_height = (1 + 2 * 0.05) * sum(display_str_heights)

            text_bottom = top if top > total_display_str_height else bottom + total_display_str_height

            for display_str in display_str_list[::1]:
                text_width, text_height = font.getsize(display_str)
                margin = np.ceil(0.05 * text_height)
                draw.rectangle([(left, text_bottom - text_height - 2 * margin),
                                (left + text_width, text_bottom)],
                               fill=color)
                draw.text((left + margin, text_bottom - text_height - margin),
                          display_str,
                          fill="black",
                          font=font)
                text_bottom -= text_height - 2 * margin

        def _draw_boxes(self, image, boxes, class_names, scores, max_boxes=10, min_score=0.1):
            colors = list(ImageColor.colormap.values())

            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Regular.ttf", 25)
            except IOError:
                font = ImageFont.load_default()

            for i in range(min(boxes.shape[0], max_boxes)):
                if scores[i] >= min_score:
                    y_min, x_min, y_max, x_max = tuple(boxes[i].tolist())
                    display_str = "{0}: {1}%".format(class_names[i].decode("ascii"), int(100 * scores[i]))
                    color = colors[hash(class_names[i]) % len(colors)]
                    image_pil = Image.fromarray(np.uint8(image)).convert("RGB")
                    self._draw_bounding_box_on_image(image_pil,
                                                     y_min,
                                                     x_min,
                                                     y_max,
                                                     x_max,
                                                     color,
                                                     font,
                                                     display_str_list=[display_str])
                    np.copyto(image, np.array(image_pil))
            return image

        def detect_objects(self, image):
            img_width, img_height = image.size
            if img_height > 1280:
                image = self._resize_image(image, 720, 1280)

            result_out, image_out = self.__session.run([self.__result, self.__decoded_image],
                                                       feed_dict={self.__image_string_placeholder: image})
            image_with_boxes = self._draw_boxes(np.array(image_out),
                                                result_out["detection_boxes"],
                                                result_out["detection_class_entities"],
                                                result_out["detection_scores"])
            return image_with_boxes

    __instance = None

    def __new__(cls, *args, **kwargs):
        if not Worker.__instance:
            model = kwargs.get("model", W_DEFAULT_MODEL_URL)
            Worker.__instance = Worker.__Worker(model)
        return Worker.__instance

    def __getattr__(self, item):
        return getattr(self.__instance, item)

    def __setattr__(self, key, value):
        return setattr(self.__instance, key, value)

    def detect_objects(self, image) -> np.ndarray:
        return self.__instance.detect_objects(image)
