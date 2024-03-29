import sys
import time

import numpy as np
import cv2
import math

import ailia

# import original modules
sys.path.append('../../util')
from utils import get_base_parser, update_parser, get_savepath  # noqa: E402
from model_utils import check_and_download_models  # noqa: E402
from detector_utils import load_image  # noqa: E402
import webcamera_utils  # noqa: E402
from pose_resnet_util import compute, keep_aspect  # noqa: E402

# logger
from logging import getLogger   # noqa: E402
logger = getLogger(__name__)


# ======================
# Parameters
# ======================
POSE_MODEL_NAME = 'pose_resnet_50_256x192'
POSE_WEIGHT_PATH = f'{POSE_MODEL_NAME}.onnx'
POSE_MODEL_PATH = f'{POSE_MODEL_NAME}.onnx.prototxt'
POSE_REMOTE_PATH = 'https://storage.googleapis.com/ailia-models/pose_resnet/'

WEIGHT_PATH = 'yolox_s.opt.onnx'
MODEL_PATH = 'yolox_s.opt.onnx.prototxt'
REMOTE_PATH = 'https://storage.googleapis.com/ailia-models/yolox/'

IMAGE_PATH = 'input.jpg'
SAVE_IMAGE_PATH = 'output.png'

COCO_CATEGORY = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train",
    "truck", "boat", "traffic light", "fire hydrant", "stop sign",
    "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow",
    "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
    "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard",
    "sports ball", "kite", "baseball bat", "baseball glove", "skateboard",
    "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork",
    "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "dining table", "toilet", "tv",
    "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave",
    "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase",
    "scissors", "teddy bear", "hair drier", "toothbrush"
]
THRESHOLD = 0.4
IOU = 0.45
POSE_THRESHOLD = 0.4


# ======================
# Arguemnt Parser Config
# ======================
parser = get_base_parser(
    'Simple Baseline for Pose Estimation', IMAGE_PATH, SAVE_IMAGE_PATH,
)
parser.add_argument(
    '--reverse',
    action='store_true',
    help='Reverse input image.'
)
parser.add_argument(
    '--model_type',
    default=None, type=str,
    help='Model type.'
)
parser.add_argument(
    '--category_fallen',
    action='store_true',
    help='Detect fallen.'
)
parser.add_argument(
    '--category_sitting',
    action='store_true',
    help='Detect sitting.'
)
parser.add_argument(
    '-th', '--detection_threshold',
    default=THRESHOLD, type=float,
    help='The detection threshold for yolo. (default: '+str(THRESHOLD)+')'
)
parser.add_argument(
    '-pth', '--pose_threshold',
    default=POSE_THRESHOLD, type=float,
    help='The pose threshold for yolo. (default: '+str(POSE_THRESHOLD)+')'
)
args = update_parser(parser)


# ======================
# Display result
# ======================
def hsv_to_rgb(h, s, v):
    bgr = cv2.cvtColor(
        np.array([[[h, s, v]]], dtype=np.uint8), cv2.COLOR_HSV2BGR)[0][0]
    return (int(bgr[0]), int(bgr[1]), int(bgr[2]), 255)


def line(input_img, person, point1, point2):
    threshold = args.pose_threshold
    if person.points[point1].score > threshold and\
       person.points[point2].score > threshold:
        color = hsv_to_rgb(255*point1/ailia.POSE_KEYPOINT_CNT, 255, 255)

        x1 = int(input_img.shape[1] * person.points[point1].x)
        y1 = int(input_img.shape[0] * person.points[point1].y)
        x2 = int(input_img.shape[1] * person.points[point2].x)
        y2 = int(input_img.shape[0] * person.points[point2].y)
        cv2.line(input_img, (x1, y1), (x2, y2), color, 5)


def display_result(input_img, person):
    line(input_img, person, ailia.POSE_KEYPOINT_NOSE,
         ailia.POSE_KEYPOINT_SHOULDER_CENTER)
    line(input_img, person, ailia.POSE_KEYPOINT_SHOULDER_LEFT,
         ailia.POSE_KEYPOINT_SHOULDER_CENTER)
    line(input_img, person, ailia.POSE_KEYPOINT_SHOULDER_RIGHT,
         ailia.POSE_KEYPOINT_SHOULDER_CENTER)

    line(input_img, person, ailia.POSE_KEYPOINT_EYE_LEFT,
         ailia.POSE_KEYPOINT_NOSE)
    line(input_img, person, ailia.POSE_KEYPOINT_EYE_RIGHT,
         ailia.POSE_KEYPOINT_NOSE)
    line(input_img, person, ailia.POSE_KEYPOINT_EAR_LEFT,
         ailia.POSE_KEYPOINT_EYE_LEFT)
    line(input_img, person, ailia.POSE_KEYPOINT_EAR_RIGHT,
         ailia.POSE_KEYPOINT_EYE_RIGHT)

    line(input_img, person, ailia.POSE_KEYPOINT_ELBOW_LEFT,
         ailia.POSE_KEYPOINT_SHOULDER_LEFT)
    line(input_img, person, ailia.POSE_KEYPOINT_ELBOW_RIGHT,
         ailia.POSE_KEYPOINT_SHOULDER_RIGHT)
    line(input_img, person, ailia.POSE_KEYPOINT_WRIST_LEFT,
         ailia.POSE_KEYPOINT_ELBOW_LEFT)
    line(input_img, person, ailia.POSE_KEYPOINT_WRIST_RIGHT,
         ailia.POSE_KEYPOINT_ELBOW_RIGHT)

    line(input_img, person, ailia.POSE_KEYPOINT_BODY_CENTER,
         ailia.POSE_KEYPOINT_SHOULDER_CENTER)
    line(input_img, person, ailia.POSE_KEYPOINT_HIP_LEFT,
         ailia.POSE_KEYPOINT_BODY_CENTER)
    line(input_img, person, ailia.POSE_KEYPOINT_HIP_RIGHT,
         ailia.POSE_KEYPOINT_BODY_CENTER)

    line(input_img, person, ailia.POSE_KEYPOINT_KNEE_LEFT,
         ailia.POSE_KEYPOINT_HIP_LEFT)
    line(input_img, person, ailia.POSE_KEYPOINT_ANKLE_LEFT,
         ailia.POSE_KEYPOINT_KNEE_LEFT)
    line(input_img, person, ailia.POSE_KEYPOINT_KNEE_RIGHT,
         ailia.POSE_KEYPOINT_HIP_RIGHT)
    line(input_img, person, ailia.POSE_KEYPOINT_ANKLE_RIGHT,
         ailia.POSE_KEYPOINT_KNEE_RIGHT)


def pose_estimation(detector, pose, img):
    pose_img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    h, w = img.shape[0], img.shape[1]
    count = detector.get_object_count()
    pose_detections = []
    for idx in range(count):
        obj = detector.get_object(idx)
        top_left = (int(w*obj.x), int(h*obj.y))
        bottom_right = (int(w*(obj.x+obj.w)), int(h*(obj.y+obj.h)))
        CATEGORY_PERSON = 0
        if obj.category != CATEGORY_PERSON:
            pose_detections.append(None)
            continue
        px1, py1, px2, py2 = keep_aspect(
            top_left, bottom_right, pose_img, pose
        )
        crop_img = pose_img[py1:py2, px1:px2, :]
        offset_x = px1/img.shape[1]
        offset_y = py1/img.shape[0]
        scale_x = crop_img.shape[1]/img.shape[1]
        scale_y = crop_img.shape[0]/img.shape[0]
        detections = compute(
            pose, crop_img, offset_x, offset_y, scale_x, scale_y
        )
        pose_detections.append(detections)
    return pose_detections


def is_safety(detections):
    threshold = args.pose_threshold
    theta = 0
    status = ""

    if args.category_sitting:
        # 膝がヒップよりも上にある
        if detections.points[ailia.POSE_KEYPOINT_HIP_LEFT].score > threshold and detections.points[ailia.POSE_KEYPOINT_KNEE_LEFT].score > threshold:
            if detections.points[ailia.POSE_KEYPOINT_HIP_LEFT].y > detections.points[ailia.POSE_KEYPOINT_KNEE_LEFT].y:
                return False, "(Hip > Knee)"
        if detections.points[ailia.POSE_KEYPOINT_HIP_RIGHT].score > threshold and detections.points[ailia.POSE_KEYPOINT_HIP_RIGHT].score > threshold:
            if detections.points[ailia.POSE_KEYPOINT_HIP_RIGHT].y > detections.points[ailia.POSE_KEYPOINT_KNEE_RIGHT].y:
                return False, "(Hip > Knee)"

    if args.category_fallen:
        # 頭が横にある
        if detections.points[ailia.POSE_KEYPOINT_NOSE].score > threshold and detections.points[ailia.POSE_KEYPOINT_BODY_CENTER].score:
            theta = math.atan2(-(detections.points[ailia.POSE_KEYPOINT_NOSE].y - detections.points[ailia.POSE_KEYPOINT_BODY_CENTER].y),
                                detections.points[ailia.POSE_KEYPOINT_NOSE].x - detections.points[ailia.POSE_KEYPOINT_BODY_CENTER].x)
            theta = 180 * theta / math.pi
            status = "(Head Body angle " + str(int(theta)) + ")"
            if not (theta >= 30 and theta <= 180 - 30):
                return False, status
        #else:
        #    if detections.points[ailia.POSE_KEYPOINT_NOSE].score > threshold and detections.points[ailia.POSE_KEYPOINT_SHOULDER_CENTER].score:
        #        theta = math.atan2(-(detections.points[ailia.POSE_KEYPOINT_NOSE].y - detections.points[ailia.POSE_KEYPOINT_SHOULDER_CENTER].y),
        #                            detections.points[ailia.POSE_KEYPOINT_NOSE].x - detections.points[ailia.POSE_KEYPOINT_SHOULDER_CENTER].x)
        #        theta = 180 * theta / math.pi
        #        status = "(Head Shoulder angle " + str(int(theta)) + ")"
        #        if not (theta >= 30 and theta <= 180 - 30):
        #            return False, status

    return True, status


def plot_results(detector, pose, img, category, pose_detections, logging=True):
    h, w = img.shape[0], img.shape[1]
    count = detector.get_object_count()
    if logging:
        logger.info(f'object_count={count}')

    for idx in range(count):
        obj = detector.get_object(idx)
        top_left = (int(w*obj.x), int(h*obj.y))
        bottom_right = (int(w*(obj.x+obj.w)), int(h*(obj.y+obj.h)))
        text_position = (int(w*obj.x)+4, int(h*(obj.y+obj.h)-8))

        # update image
        if not (obj.category == 0):
            continue
        
        CATEGORY_PERSON = 0
        if obj.category != CATEGORY_PERSON:
            continue

        # pose detection
        px1, py1, px2, py2 = keep_aspect(
            top_left, bottom_right, img, pose
        )
        detections = pose_detections[idx]

        safety, status = is_safety(detections)

        color = (0, 255, 0, 255) # Safety
        if not safety:
            color = (0, 0, 255, 255) # Not Safety
        fontScale = w / 1024.0
        cv2.rectangle(img, top_left, bottom_right, color, 4)

        cv2.rectangle(img, (px1, py1), (px2, py2), color, 1)
        display_result(img, detections)
        

        # is fall
        text = "Safety"
        if not safety:
            text = "Not safety"
        text = text + status
        cv2.putText(
            img,
            text,
            text_position,
            cv2.FONT_HERSHEY_SIMPLEX,
            fontScale,
            color,
            4
        )

    return img


# ======================
# Main functions
# ======================
def recognize_from_image():
    # net initialize
    detector = ailia.Detector(
        MODEL_PATH,
        WEIGHT_PATH,
        len(COCO_CATEGORY),
        format=ailia.NETWORK_IMAGE_FORMAT_BGR,
        channel=ailia.NETWORK_IMAGE_CHANNEL_FIRST,
        range=ailia.NETWORK_IMAGE_RANGE_U_INT8,
        algorithm=ailia.DETECTOR_ALGORITHM_YOLOX,
        env_id=args.env_id,
    )

    pose = ailia.Net(POSE_MODEL_PATH, POSE_WEIGHT_PATH, env_id=args.env_id)

    # input image loop
    for image_path in args.input:
        # prepare input data
        logger.info(image_path)
        img = load_image(image_path)
        logger.debug(f'input image shape: {img.shape}')

        # inference
        logger.info('Start inference...')
        detector.compute(img, args.detection_threshold, IOU)

        # pose estimation
        if args.benchmark:
            logger.info('BENCHMARK mode')
            total_time = 0
            for i in range(args.benchmark_count):
                start = int(round(time.time() * 1000))
                pose_detections = pose_estimation(detector, pose, img)
                end = int(round(time.time() * 1000))
                logger.info(f'\tailia processing detection time {end - start} ms')
                if i != 0:
                    total_time = total_time + (end - start)
            logger.info(f'\taverage detection time {total_time / (args.benchmark_count-1)} ms')
        else:
            pose_detections = pose_estimation(detector, pose, img)

        # plot result
        res_img = plot_results(detector, pose, img, COCO_CATEGORY, pose_detections)
        savepath = get_savepath(args.savepath, image_path)
        logger.info(f'saved at : {savepath}')
        cv2.imwrite(savepath, res_img)
    logger.info('Script finished successfully.')


def recognize_from_video():
    # net initialize
    detector = ailia.Detector(
        MODEL_PATH,
        WEIGHT_PATH,
        len(COCO_CATEGORY),
        format=ailia.NETWORK_IMAGE_FORMAT_RGB,
        channel=ailia.NETWORK_IMAGE_CHANNEL_FIRST,
        range=ailia.NETWORK_IMAGE_RANGE_U_INT8,
        algorithm=ailia.DETECTOR_ALGORITHM_YOLOX,
        env_id=args.env_id,
    )

    pose = ailia.Net(POSE_MODEL_PATH, POSE_WEIGHT_PATH, env_id=args.env_id)

    capture = webcamera_utils.get_capture(args.video)
    # create video writer if savepath is specified as video format
    if args.savepath != SAVE_IMAGE_PATH:
        f_h = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        f_w = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        writer = webcamera_utils.get_writer(args.savepath, f_h, f_w)
    else:
        writer = None
    
    frame_shown = False
    frame_cnt = 0
    while(True):
        ret, frame = capture.read()
        if args.reverse:
            frame = frame[::-1,:,:].copy()
        if frame_cnt % 10 != 0:
            frame_cnt = frame_cnt + 1
            continue
        frame_cnt = frame_cnt + 1
        if (cv2.waitKey(1) & 0xFF == ord('q')) or not ret:
            break
        if frame_shown and cv2.getWindowProperty('frame', cv2.WND_PROP_VISIBLE) == 0:
            break

        img = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
        detector.compute(img, args.detection_threshold, IOU)
        pose_detections = pose_estimation(detector, pose, img)
        res_img = plot_results(detector, pose, frame, COCO_CATEGORY, pose_detections, False)
        cv2.imshow('frame', res_img)
        frame_shown = True
        # save results
        if writer is not None:
            writer.write(res_img)

    capture.release()
    cv2.destroyAllWindows()
    if writer is not None:
        writer.release()
    logger.info('Script finished successfully.')


def main():
    # model files check and download
    check_and_download_models(WEIGHT_PATH, MODEL_PATH, REMOTE_PATH)
    check_and_download_models(
        POSE_WEIGHT_PATH, POSE_MODEL_PATH, POSE_REMOTE_PATH
    )

    if args.video is not None:
        # video mode
        recognize_from_video()
    else:
        # image mode
        recognize_from_image()


if __name__ == '__main__':
    main()
