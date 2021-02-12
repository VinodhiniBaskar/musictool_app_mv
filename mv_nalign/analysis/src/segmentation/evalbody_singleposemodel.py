import os
import cv2
import numpy as np
# import matplotlib.pyplot as plt
# import matplotlib.patches as patches
# from PIL import Image
from mv_nalign.analysis.src.segmentation.utils import get_input_tensors, get_output_tensors
import tensorflow as tf

# from src.processing.utils.contours_correction import correction

KEYPOINT_NAMES = [
    "nose", "leftEye", "rightEye", "leftEar", "rightEar", "leftShoulder",
    "rightShoulder", "leftElbow", "rightElbow", "leftWrist", "rightWrist",
    "leftHip", "rightHip", "leftKnee", "rightKnee", "leftAnkle", "rightAnkle"
]

KEYPOINT_IDS = {name: id for id, name in enumerate(KEYPOINT_NAMES)}

CONNECTED_KEYPOINTS_NAMES = [
    ("leftHip", "leftShoulder"), ("leftElbow", "leftShoulder"),
    ("leftElbow", "leftWrist"), ("leftHip", "leftKnee"),
    ("leftKnee", "leftAnkle"), ("rightHip", "rightShoulder"),
    ("rightElbow", "rightShoulder"), ("rightElbow", "rightWrist"),
    ("rightHip", "rightKnee"), ("rightKnee", "rightAnkle"),
    ("leftShoulder", "rightShoulder"), ("leftHip", "rightHip")
]

CONNECTED_KEYPOINT_INDICES = [(KEYPOINT_IDS[a], KEYPOINT_IDS[b])
                              for a, b in CONNECTED_KEYPOINTS_NAMES]


FRONT_PARTS = [
    'head',
    'l_shoulder',
    'r_shoulder',
    'l_forearm',
    'r_forearm',
    'left_hand',
    'right_hand',
    'backbone',
    'l_thigh',
    'r_thigh',
    'l_leg',
    'r_leg',
    'l_big_foot',
    'r_big_foot'
]

BIG_PART_COLORS = {
    'head': (255, 0, 127),
    'l_shoulder': (0, 255, 255),
    'r_shoulder': (255, 255, 0),
    'l_forearm': (0, 127, 255),
    'r_forearm': (255, 127, 0),
    'left_hand': (0, 0, 127),
    'right_hand': (127, 0, 0),
    'backbone': (0, 127, 0),
    'l_thigh': (0, 127, 255),
    'r_thigh': (255, 127, 0),
    'l_leg': (0, 0, 127),
    'r_leg': (127, 0, 0),
    'l_big_foot': (127, 127, 255),
    'r_big_foot': (255, 127, 127),
}

BIG_PART_INDEX = {
    'head': [0, 1],
    'l_shoulder': [2, 3],
    'r_shoulder': [4, 5],
    'l_forearm': [6, 7],
    'r_forearm': [8, 9],
    'left_hand': [10],
    'right_hand': [11],
    'backbone': [12, 13],
    'l_thigh': [14, 15],
    'r_thigh': [16, 17],
    'l_leg': [18, 19],
    'r_leg': [20, 21],
    'l_big_foot': [22],
    'r_big_foot': [23],
}

PERSONS_COLOR = [
    (0, 0, 0),
    (255, 255, 255),
    (0, 0, 255),
    (0, 255, 0),
    (255, 0, 0),
    (255, 255, 0),
    (0, 255, 255),
    (255, 0, 255),

]


# make tensorflow stop spamming messages
os.environ['TF_CPP_MIN_LOG_LEVEL'] = "3"


def adjust_height(image, height, interp=cv2.INTER_LANCZOS4):
    """
    Resize image to specified 'height' with proportion kipping
    (!) Do not use to resize two images to the same shape. Calculated width can be differ due to rounding
    """
    width = int(np.round(image.shape[1] * height / image.shape[0]))

    return cv2.resize(image, (width, height), interp)


def scale_contours(contours, scale):
    """
    Scale OpenCV contours list
    """
    return [np.round(c * scale).astype(int) for c in contours]


def get_best_contour(contours):
    """
    Get best contour
    """
    if len(contours) == 0:
        return contours

    areas = np.array([cv2.contourArea(c) for c in contours])
    best = np.argmax(areas)

    return [contours[best]]


def contour_resample(contour, point_count=50):
    if len(contour) == 0:
        return contour
    length = cv2.arcLength(contour[0], closed=True)
    step = int(np.round(length / point_count))
    result = []
    for i in range(0, contour[0].shape[0], step):
        result.append(contour[0][i])

    return [np.array(result)]


def filter_contours(contours):
    if len(contours) == 0:
        return contours
    perimeters = [cv2.arcLength(c, closed=False) for c in contours]
    max_perimeter = np.max(perimeters)
    contours = [c for p, c in zip(perimeters, contours) if p >= max_perimeter * 0.1]

    return contours


def get_segments(graph, image, target_height=600, output_stride=16):

    img_height, img_width, _ = image.shape
    target_height = (int(img_height) // output_stride) * output_stride + 1
    target_width = (int(img_width) // output_stride) * output_stride + 1
    img = cv2.resize(image, (target_width, target_height))
    x = np.asarray(img, dtype=np.float32)

    input_tensor_names = get_input_tensors(graph)
    output_tensor_names = get_output_tensors(graph)
    input_tensor = graph.get_tensor_by_name(input_tensor_names[0])

    # Preprocessing Image
    # For Resnet
    if any('resnet_v1' in name for name in output_tensor_names):
        # add imagenet mean - extracted from body-pix source
        m = np.array([-123.15, -115.90, -103.06])
        x = np.add(x, m)
        # print("resnet_v1 model selected")
    # For Mobilenet
    elif any('MobilenetV1' in name for name in output_tensor_names):
        x = (x / 127.5) - 1
        # print("MobilenetV1 model selected")
    else:
        print('Unknown Model')

    sample_image = x[np.newaxis, ...]
    # print("done.\nRunning inference...", end="")

    # evaluate the loaded model directly
    with tf.compat.v1.Session(graph=graph) as sess:
        results = sess.run(output_tensor_names, feed_dict={
            input_tensor: sample_image})
    # print("done. {} outputs received".format(len(results)))  # should be 8 outputs

    segments = None
    part_heatmaps = None

    for idx, name in enumerate(output_tensor_names):
        if 'float_part_heatmaps' in name:
            part_heatmaps = np.squeeze(results[idx], 0)
            # print('partHeatmaps', part_heatmaps.shape)
        elif 'float_segments' in name:
            segments = np.squeeze(results[idx], 0)
            # print('segments', segments.shape)

    return segments, part_heatmaps


def get_body_contour(graph, image, target_height=600, output_stride=16, segmentation_threshold=0.7):
    source_height, source_width, _ = image.shape
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = adjust_height(image, target_height, interp=cv2.INTER_LANCZOS4)
    segments, part_heatmaps = get_segments(graph, image, target_height=target_height, output_stride=output_stride)
    # getting body mask
    segments = cv2.resize(segments, (image.shape[1], image.shape[0]))
    segments_scores = (255 / (1 + np.exp(segments))).astype("uint8")
    ret, mask_img = cv2.threshold(segments_scores, 255 * segmentation_threshold, 255, cv2.THRESH_BINARY_INV)

    # getting body contour
    body_contour, _ = cv2.findContours(mask_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)
    body_contour = filter_contours(scale_contours(body_contour, source_height / target_height))

    return body_contour


def get_bodypix_result(graph, image, target_height=600, output_stride=16, segmentation_threshold=0.7):

    # getting bodypix results
    source_height, source_width, _ = image.shape
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = adjust_height(image, target_height, interp=cv2.INTER_LANCZOS4)
    segments, part_heatmaps = get_segments(graph, image, target_height=target_height, output_stride=output_stride)

    # getting body mask
    segments = cv2.resize(segments, (image.shape[1], image.shape[0]))
    segments_scores = (255 / (1 + np.exp(segments))).astype("uint8")
    ret, mask_img = cv2.threshold(segments_scores, 255 * segmentation_threshold, 255, cv2.THRESH_BINARY_INV)

    # getting body contour
    body_contour, _ = cv2.findContours(mask_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)
    body_contour = filter_contours(scale_contours(body_contour, source_height / target_height))

    # resizing heatmaps stack
    layers = []
    for i in range(part_heatmaps.shape[2]):
        heatmap = part_heatmaps[:, :, i]
        heatmap = adjust_height(heatmap, target_height, cv2.INTER_AREA)
        layers.append(heatmap)

    part_heatmaps = np.stack(layers, axis=-1)

    # getting max scored body part
    mask_heatmap = np.argmax(part_heatmaps, axis=2)
    mask_heatmap = np.asarray(mask_heatmap, dtype=np.uint8)
    part_mask = np.zeros_like(mask_heatmap, dtype=np.uint8)

    segments_dictionary = {}
    for j, key in enumerate(BIG_PART_INDEX.keys()):
        ind = BIG_PART_INDEX[key]
        part_mask.fill(0)
        for i in ind:
            part_mask[mask_heatmap == i] = 255
        part_mask_big = cv2.resize(part_mask, (image.shape[1], image.shape[0]), cv2.INTER_LANCZOS4)
        part_mask_big[mask_img == 0] = 0
        contours, hierarchy = cv2.findContours(part_mask_big, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_KCOS)
        resulting_contour = scale_contours(contours, source_height / target_height)
        segments_dictionary.update(
            {
                list(BIG_PART_INDEX.keys())[j]: resulting_contour
            }
        )

    result = {"body_contour": body_contour, "parts": segments_dictionary}

    return result


# def segmentation(image, projection="front", segmentation_threshold=0.7):
#
#     source_height, source_width, _ = image.shape
#
#     # Loading graph
#     print("Loading model...", end="")
#     graph = load_graph_model(modelPath)  # downloaded from the link above
#     print("done.\nLoading sample image...", end="")
#
#     # getting body mask
#     segments, _ = get_bodypix_result(graph, image, target_height=BODY_MASK_TARGET_HEIGHT)
#     segments = adjust_height(segments, BODY_MASK_TARGET_HEIGHT)
#     segments_scores = (255 / (1 + np.exp(segments))).astype("uint8")
#     ret, mask_img = cv2.threshold(segments_scores, 255 * segmentation_threshold, 255, cv2.THRESH_BINARY_INV)
#
#     # getting parts heatmaps
#     _, part_heatmaps = get_bodypix_result(graph, image, target_height=BODY_PARTS_TARGET_HEIGHT)
#
#     # resizing heatmaps stack
#     layers = []
#     for i in range(part_heatmaps.shape[2]):
#         heatmap = part_heatmaps[:, :, i]
#         heatmap = adjust_height(heatmap, BODY_PARTS_TARGET_HEIGHT, cv2.INTER_AREA)
#         # heatmap = cv2.blur(heatmap, (3, 3))
#         layers.append(heatmap)
#
#     part_heatmaps = np.stack(layers, axis=-1)
#
#     segments_dictionary = {}
#
#     # getting max scored body part
#     mask_heatmap = np.argmax(part_heatmaps, axis=2)
#     mask_heatmap = np.asarray(mask_heatmap, dtype=np.uint8)
#
#     # body mask simplification for side projection
#     if projection == "side":
#         blank = np.zeros_like(mask_heatmap)
#         for j, key in enumerate(BIG_PART_INDEX.keys()):
#             if key not in SIDE_PARTS:
#                 continue
#             ind = BIG_PART_INDEX[key]
#             for i in ind:
#                 blank[mask_heatmap == i] = 255
#         blank = cv2.resize(blank, (mask_img.shape[1], mask_img.shape[0]), cv2.INTER_NEAREST)
#         mask_img = cv2.bitwise_and(mask_img, blank)
#
#     # getting parts contours
#     part_mask = np.zeros_like(mask_heatmap, dtype="uint8")
#     for j, key in enumerate(BIG_PART_INDEX.keys()):
#         if projection == "side" and key not in SIDE_PARTS:
#             continue
#         ind = BIG_PART_INDEX[key]
#         part_mask.fill(0)
#         for i in ind:
#             part_mask[mask_heatmap == i] = 255
#         part_mask_big = cv2.resize(part_mask, (mask_img.shape[1], mask_img.shape[0]), cv2.INTER_CUBIC)
#         part_mask_big[mask_img == 0] = 0
#         contours, hierarchy = cv2.findContours(part_mask_big, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
#         best = get_best_contour(contours)
#
#         best = contour_resample(best)
#
#         resulting_contour = scale_contours(best, source_height / BODY_MASK_TARGET_HEIGHT)
#         segments_dictionary.update(
#             {
#                 list(BIG_PART_INDEX.keys())[j]: resulting_contour
#             }
#         )
#
#     body_contour, _ = cv2.findContours(mask_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)
#     body_contour = scale_contours(body_contour, source_height / BODY_MASK_TARGET_HEIGHT)
#     result = {"body_contour": get_best_contour(body_contour), "parts": segments_dictionary}
#
#     return result
