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
    shadows=0,
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

    if shadows != 0:
        b_chan, g_chan, r_chan = cv2.split(
            adjusted.astype(np.float32) / 255.0
        )

        def gamma_to_linear(channel):
            mask = channel <= 0.04045
            channel_linear = np.zeros_like(channel)
            channel_linear[mask] = channel[mask] / 12.92
            channel_linear[~mask] = (
                (channel[~mask] + 0.055) / 1.055
            ) ** 2.4
            return channel_linear

        r_linear = gamma_to_linear(r_chan)
        g_linear = gamma_to_linear(g_chan)
        b_linear = gamma_to_linear(b_chan)

        x_matrix = (
            r_linear * 0.4124564
            + g_linear * 0.3575761
            + b_linear * 0.1804375
        )
        y_matrix = (
            r_linear * 0.2126729
            + g_linear * 0.7151522
            + b_linear * 0.0721750
        )
        z_matrix = (
            r_linear * 0.0193339
            + g_linear * 0.1191920
            + b_linear * 0.9503041
        )

        y_normalized = y_matrix / 1.00000

        delta_epsilon = 6.0 / 29.0
        epsilon_cubed = delta_epsilon**3

        l_mask = y_normalized > epsilon_cubed
        f_y = np.zeros_like(y_normalized)
        f_y[l_mask] = y_normalized[l_mask] ** (1.0 / 3.0)
        f_y[~l_mask] = (
            y_normalized[~l_mask] / (3.0 * (delta_epsilon**2))
        ) + (4.0 / 29.0)

        luminance_l = (116.0 * f_y) - 16.0
        luminance_norm = np.clip(luminance_l / 100.0, 0.0, 1.0)

        shadow_cutoff_low = 0.0
        shadow_cutoff_high = 0.45
        pivot_point = 0.225

        raw_shadow_mask = np.zeros_like(luminance_norm)
        in_range = (luminance_norm >= shadow_cutoff_low) & (
            luminance_norm <= shadow_cutoff_high
        )
        raw_shadow_mask[in_range] = (
            shadow_cutoff_high - luminance_norm[in_range]
        ) / (shadow_cutoff_high - shadow_cutoff_low)

        smooth_shadow_mask = 0.5 * (
            1.0 + np.cos(np.pi * (1.0 - raw_shadow_mask))
        )

        blurred_luminance = cv2.GaussianBlur(
            luminance_norm.astype(np.float32), (15, 15), 0
        )
        high_freq_detail = luminance_norm - blurred_luminance

        shadow_intensity = shadows / 100.0

        if shadow_intensity > 0:
            expansion_factor = 1.0 + (shadow_intensity * 1.5)
            lifted_luminance = np.power(
                luminance_norm, 1.0 / expansion_factor
            )
            processed_luminance = (
                lifted_luminance * smooth_shadow_mask
            ) + (luminance_norm * (1.0 - smooth_shadow_mask))
        else:
            compression_factor = 1.0 + (abs(shadow_intensity) * 1.2)
            crushed_luminance = np.power(
                luminance_norm, compression_factor
            )
            processed_luminance = (
                crushed_luminance * smooth_shadow_mask
            ) + (luminance_norm * (1.0 - smooth_shadow_mask))

        processed_luminance = processed_luminance + (
            high_freq_detail * smooth_shadow_mask * 0.5
        )
        processed_luminance = np.clip(processed_luminance, 0.0, 1.0)

        safe_luminance_orig = np.maximum(luminance_norm, 1e-6)
        luminance_ratio = processed_luminance / safe_luminance_orig

        r_adjusted = np.clip(r_chan * luminance_ratio, 0.0, 1.0)
        g_adjusted = np.clip(g_chan * luminance_ratio, 0.0, 1.0)
        b_adjusted = np.clip(b_chan * luminance_ratio, 0.0, 1.0)

        chroma_suppression = 1.0 - (
            smooth_shadow_mask * max(0.0, shadow_intensity) * 0.35
        )
        gray_point = (
            (r_adjusted * 0.299)
            + (g_adjusted * 0.587)
            + (b_adjusted * 0.114)
        )

        r_final = (r_adjusted * chroma_suppression) + (
            gray_point * (1.0 - chroma_suppression)
        )
        g_final = (g_adjusted * chroma_suppression) + (
            gray_point * (1.0 - chroma_suppression)
        )
        b_final = (b_adjusted * chroma_suppression) + (
            gray_point * (1.0 - chroma_suppression)
        )

        b_out = (np.clip(b_final, 0.0, 1.0) * 255.0).astype(np.uint8)
        g_out = (np.clip(g_final, 0.0, 1.0) * 255.0).astype(np.uint8)
        r_out = (np.clip(r_final, 0.0, 1.0) * 255.0).astype(np.uint8)

        adjusted = cv2.merge([b_out, g_out, r_out])

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
