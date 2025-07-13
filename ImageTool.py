import cv2
import numpy as np
from PIL import Image


def cvt_color(img, fmt=cv2.COLOR_BGR2RGB):
    return cv2.cvtColor(img, fmt)

def decode_img(img_path):
    with open(img_path, "rb") as f:
        img_data = f.read()
    img = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR)
    return img

def get_img_size(img_path):
    with Image.open(img_path) as img:
        return img.size  # 返回 (宽度, 高度)

def resize_img(image):
    h, w = image.shape[:2]
    aspect_ratio = w / h  # 原始宽高比

    new_w = int((w // 4) * 4)
    new_h = new_w / aspect_ratio
    new_h = int((new_h // 4) * 4)

    new_w = max(new_w, 4)
    new_h = max(new_h, 4)

    # 选择插值方法（放大用线性，缩小用区域插值）
    interpolation = cv2.INTER_LINEAR if (new_w > w or new_h > h) else cv2.INTER_AREA
    resized = cv2.resize(image, (new_w, new_h), interpolation=interpolation)

    return resized

def adjust_img(img_path):
    img = decode_img(img_path)
    img = resize_img(img)
    return cvt_color(img)