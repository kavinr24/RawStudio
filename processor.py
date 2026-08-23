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
    aspect_ratio="Original",
    vignette=0,
    blur=0,
    sharpen=0,
    grayscale=False,
):
    if img is None:
        return None

    adjusted = img.copy()

    if aspect_ratio != "Original":
        h, w = adjusted.shape[:2]
        target_w, target_h = w, h
        if aspect_ratio == "1:1":
            target_w = target_h = min(w, h)
        elif aspect_ratio == "4:3":
            if w / h > 4 / 3:
                target_w = int(h * (4 / 3))
            else:
                target_h = int(w * (3 / 4))
        elif aspect_ratio == "16:9":
            if w / h > 16 / 9:
                target_w = int(h * (16 / 9))
            else:
                target_h = int(w * (9 / 16))

        start_x = (w - target_w) // 2
        start_y = (h - target_h) // 2
        adjusted = adjusted[
            start_y : start_y + target_h, start_x : start_x + target_w
        ]

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

    if contrast != 1.0 or brightness != 0:
        adjusted = cv2.convertScaleAbs(
            adjusted, alpha=contrast, beta=brightness
        )

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

    if vignette > 0:
        h, w = adjusted.shape[:2]
        kernel_x = cv2.getGaussianKernel(w, w / (vignette / 20.0))
        kernel_y = cv2.getGaussianKernel(h, h / (vignette / 20.0))
        mask = (kernel_x * kernel_y.T).T
        mask = mask / mask.max()
        adjusted = (adjusted * mask[:, :, np.newaxis]).astype(np.uint8)

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


def get_histogram_image(img, width=256, height=120):
    if img is None:
        return None

    sample = img[::2, ::2]
    hist_canvas = np.zeros((height, width, 3), dtype=np.uint8)

    if len(sample.shape) == 2:
        hist = cv2.calcHist([sample], [0], None, [256], [0, 256])
        cv2.normalize(hist, hist, 0, height, cv2.NORM_MINMAX)
        pts = np.int32(np.column_stack((np.arange(256), height - hist.ravel())))
        cv2.polylines(
            hist_canvas, [pts], isClosed=False, color=(200, 200, 200), thickness=1
        )
    else:
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        for i, color in enumerate(colors):
            hist = cv2.calcHist([sample], [i], None, [256], [0, 256])
            cv2.normalize(hist, hist, 0, height, cv2.NORM_MINMAX)
            pts = np.int32(
                np.column_stack((np.arange(256), height - hist.ravel()))
            )
            cv2.polylines(
                hist_canvas, [pts], isClosed=False, color=color, thickness=1
            )

    return hist_canvas
