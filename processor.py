import cv2
import numpy as np


def _build_gamma_to_linear_lut():
    x = np.arange(256, dtype=np.float32) / 255.0
    linear = np.zeros_like(x)
    mask = x <= 0.04045
    linear[mask] = x[mask] / 12.92
    linear[~mask] = ((x[~mask] + 0.055) / 1.055) ** 2.4
    return linear


_GAMMA_TO_LINEAR_LUT = _build_gamma_to_linear_lut()


def _gamma_to_linear(channel):
    idx = np.clip((channel * 255.0 + 0.5).astype(np.int32), 0, 255)
    return _GAMMA_TO_LINEAR_LUT[idx]


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

        r_linear = _gamma_to_linear(r_chan)
        g_linear = _gamma_to_linear(g_chan)
        b_linear = _gamma_to_linear(b_chan)

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


def extract_edge_mask(
    image_data,
    click_pos=None,
    min_val=50,
    max_val=150,
    padding=5,
    blur_amount=15,
):
    if image_data is None:
        return None

    frame_h, frame_w = image_data.shape[:2]

    if click_pos is None:
        click_pos = (frame_w // 2, frame_h // 2)

    if len(image_data.shape) == 3:
        mono_frame = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
    else:
        mono_frame = image_data

    smoothed_frame = cv2.GaussianBlur(mono_frame, (5, 5), 0)
    detected_edges = cv2.Canny(smoothed_frame, min_val, max_val)

    fill_grid = np.zeros((frame_h + 2, frame_w + 2), dtype=np.uint8)
    fill_grid[1:-1, 1:-1] = detected_edges

    working_canvas = mono_frame.copy()
    fill_flags = 4 | (255 << 8) | cv2.FLOODFILL_FIXED_RANGE | cv2.FLOODFILL_MASK_ONLY

    cv2.floodFill(
        working_canvas,
        fill_grid,
        click_pos,
        newVal=255,
        loDiff=20,
        upDiff=20,
        flags=fill_flags,
    )

    cropped_selection = fill_grid[1:-1, 1:-1].astype(np.uint8)

    box_size = max(3, padding)
    morph_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (box_size, box_size))

    cleaned_selection = cv2.morphologyEx(cropped_selection, cv2.MORPH_CLOSE, morph_kernel)
    expanded_selection = cv2.dilate(cleaned_selection, morph_kernel, iterations=1)

    if blur_amount > 0:
        kernel_dim = blur_amount * 2 + 1
        normalized_mask = expanded_selection.astype(np.float32) / 255.0
        smoothed_mask = cv2.GaussianBlur(normalized_mask, (kernel_dim, kernel_dim), 0)
        return np.clip(smoothed_mask, 0.0, 1.0)

    return (expanded_selection > 0).astype(np.float32)


def adjust_bright_tones(frame_buffer, highlight_amount):
    if highlight_amount == 0:
        return frame_buffer

    blue_ch = frame_buffer[:, :, 0]
    green_ch = frame_buffer[:, :, 1]
    red_ch = frame_buffer[:, :, 2]

    lum_map = 0.2126 * red_ch + 0.7152 * green_ch + 0.0722 * blue_ch

    bright_region = np.clip((lum_map - 0.5) / 0.5, 0.0, 1.0)
    blend_curve = 0.5 * (1.0 - np.cos(np.pi * bright_region))

    strength_factor = highlight_amount / 100.0

    if strength_factor < 0:
        curve_power = 1.0 + abs(strength_factor) * 1.5
        compressed_lum = 1.0 - np.power(np.maximum(0.0, 1.0 - lum_map), curve_power)
        scaling_ratio = np.where(
            lum_map > 1e-6, compressed_lum / np.maximum(lum_map, 1e-6), 1.0
        )
        mask_multiplier = (scaling_ratio * blend_curve) + (1.0 - blend_curve)
        frame_buffer = np.clip(
            frame_buffer * mask_multiplier[:, :, np.newaxis], 0.0, 1.0
        )
    else:
        gain_value = 1.0 + (strength_factor * 0.4 * blend_curve[:, :, np.newaxis])
        frame_buffer = np.clip(frame_buffer * gain_value, 0.0, 1.0)

    return frame_buffer


def adjust_midtone_clarity(frame_buffer, clarity_amount):
    if clarity_amount == 0:
        return frame_buffer

    blue_ch = frame_buffer[:, :, 0]
    green_ch = frame_buffer[:, :, 1]
    red_ch = frame_buffer[:, :, 2]

    lum_map = 0.2126 * red_ch + 0.7152 * green_ch + 0.0722 * blue_ch

    blurred_lum = cv2.GaussianBlur(lum_map, (21, 21), 0)
    detail_frequencies = lum_map - blurred_lum

    mid_weights = np.clip(1.0 - np.abs(lum_map - 0.5) * 2.0, 0.0, 1.0)

    clarity_boost = detail_frequencies * mid_weights * (clarity_amount / 100.0) * 0.8
    updated_lum = np.clip(lum_map + clarity_boost, 0.0, 1.0)

    tone_ratio = np.where(lum_map > 1e-6, updated_lum / np.maximum(lum_map, 1e-6), 1.0)
    frame_buffer = np.clip(frame_buffer * tone_ratio[:, :, np.newaxis], 0.0, 1.0)

    return frame_buffer


def adjust_green_magenta_tint(frame_buffer, tint_amount):
    if tint_amount == 0:
        return frame_buffer

    offset_val = (tint_amount / 100.0) * 0.1

    frame_buffer[:, :, 1] = np.clip(frame_buffer[:, :, 1] + offset_val, 0.0, 1.0)
    frame_buffer[:, :, 0] = np.clip(frame_buffer[:, :, 0] - (offset_val * 0.5), 0.0, 1.0)
    frame_buffer[:, :, 2] = np.clip(frame_buffer[:, :, 2] - (offset_val * 0.5), 0.0, 1.0)

    return frame_buffer


def apply_split_color_grading(frame_buffer, shadow_grade, highlight_grade):
    if shadow_grade == 0 and highlight_grade == 0:
        return frame_buffer

    blue_ch = frame_buffer[:, :, 0]
    green_ch = frame_buffer[:, :, 1]
    red_ch = frame_buffer[:, :, 2]

    lum_map = 0.2126 * red_ch + 0.7152 * green_ch + 0.0722 * blue_ch

    dark_mask = np.clip((0.5 - lum_map) / 0.5, 0.0, 1.0)
    light_mask = np.clip((lum_map - 0.5) / 0.5, 0.0, 1.0)

    if shadow_grade != 0:
        dark_shift = (shadow_grade / 100.0) * 0.12 * dark_mask
        frame_buffer[:, :, 2] = np.clip(frame_buffer[:, :, 2] + dark_shift, 0.0, 1.0)
        frame_buffer[:, :, 0] = np.clip(frame_buffer[:, :, 0] - dark_shift, 0.0, 1.0)

    if highlight_grade != 0:
        light_shift = (highlight_grade / 100.0) * 0.12 * light_mask
        frame_buffer[:, :, 2] = np.clip(frame_buffer[:, :, 2] + light_shift, 0.0, 1.0)
        frame_buffer[:, :, 0] = np.clip(frame_buffer[:, :, 0] - light_shift, 0.0, 1.0)

    return frame_buffer


def run_extra_effects_pipeline(
    input_img,
    highlights=0,
    clarity=0,
    tint=0,
    shadow_tint=0,
    highlight_tint=0,
):
    if input_img is None:
        return None

    frame_buffer = input_img.copy().astype(np.float32) / 255.0
    frame_buffer = adjust_bright_tones(frame_buffer, highlights)
    frame_buffer = adjust_midtone_clarity(frame_buffer, clarity)
    frame_buffer = adjust_green_magenta_tint(frame_buffer, tint)
    frame_buffer = apply_split_color_grading(frame_buffer, shadow_tint, highlight_tint)
    return (np.clip(frame_buffer, 0.0, 1.0) * 255.0).astype(np.uint8)