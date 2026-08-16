import cv2
import numpy as np


def process_image(
    img,
    rotation_angle=0,
    flip_h=False,
    flip_v=False,
    exposure=0,
    brightness=0,
    contrast=1.0,
    temperature=0,
    saturation=1.0,
    r_scale=1.0,
    g_scale=1.0,
    b_scale=1.0,
    blur=0,
    sharpen=0,
    grayscale=False,
):
    if img is None:
        return None

    adjusted = img.copy()

    if rotation_angle == 90:
        adjusted = cv2.rotate(adjusted, cv2.ROTATE_90_CLOCKWISE)
    elif rotation_angle == 180:
        adjusted = cv2.rotate(adjusted, cv2.ROTATE_180)
    elif rotation_angle == 270:
        adjusted = cv2.rotate(adjusted, cv2.ROTATE_90_COUNTERCLOCKWISE)

    if flip_h and flip_v:
        adjusted = cv2.flip(adjusted, -1)
    elif flip_h:
        adjusted = cv2.flip(adjusted, 1)
    elif flip_v:
        adjusted = cv2.flip(adjusted, 0)

    if exposure != 0:
        gamma = 2.0 ** (exposure / 50.0)
        inv_gamma = 1.0 / gamma
        lut = np.array(
            [((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]
        ).astype("uint8")
        adjusted = cv2.LUT(adjusted, lut)

    adjusted = cv2.convertScaleAbs(adjusted, alpha=contrast, beta=brightness)

    if temperature != 0:
        b, g, r = cv2.split(adjusted.astype(np.float32))
        r = np.clip(r + temperature, 0, 255)
        b = np.clip(b - temperature, 0, 255)
        adjusted = cv2.merge([b, g, r]).astype(np.uint8)

    if saturation != 1.0:
        hsv = cv2.cvtColor(adjusted, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation, 0, 255)
        adjusted = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    if r_scale != 1.0 or g_scale != 1.0 or b_scale != 1.0:
        b, g, r = cv2.split(adjusted.astype(np.float32))
        b = np.clip(b * b_scale, 0, 255)
        g = np.clip(g * g_scale, 0, 255)
        r = np.clip(r * r_scale, 0, 255)
        adjusted = cv2.merge([b, g, r]).astype(np.uint8)

    if blur > 0:
        ksize = blur * 2 + 1
        adjusted = cv2.GaussianBlur(adjusted, (ksize, ksize), 0)

    if sharpen > 0:
        blurred = cv2.GaussianBlur(adjusted, (0, 0), 3)
        strength = sharpen * 0.2
        adjusted = cv2.addWeighted(
            adjusted, 1.0 + strength, blurred, -strength, 0
        )

    if grayscale:
        adjusted = cv2.cvtColor(adjusted, cv2.COLOR_BGR2GRAY)

    return adjusted
