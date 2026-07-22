from pathlib import Path

from PIL import Image, ImageOps


def detect_face_box(image, min_size=(50, 50)):
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None

    cascade_classifier = getattr(cv2, "CascadeClassifier", None)
    cvt_color = getattr(cv2, "cvtColor", None)
    color_rgb_to_gray = getattr(cv2, "COLOR_RGB2GRAY", None)
    haarcascades = getattr(getattr(cv2, "data", None), "haarcascades", "")
    if not all([cascade_classifier, cvt_color, color_rgb_to_gray, haarcascades]):
        return None

    try:
        gray = cvt_color(np.array(image.convert("RGB")), color_rgb_to_gray)
        cascade = cascade_classifier(haarcascades + "haarcascade_frontalface_default.xml")
        if hasattr(cascade, "empty") and cascade.empty():
            return None
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=min_size)
    except Exception:
        return None

    if len(faces) == 0:
        return None
    return max(faces, key=lambda face: face[2] * face[3])


def face_focused_square(image):
    face_box = detect_face_box(image, min_size=(60, 60))
    width, height = image.size

    if face_box is not None:
        left, top, face_width, face_height = face_box
        center_x = left + face_width / 2
        center_y = top + face_height / 2
        crop_size = int(max(face_width, face_height) * 2.8)
    else:
        center_x = width / 2
        center_y = height * 0.42
        crop_size = min(width, height)

    crop_size = min(max(crop_size, 1), width, height)
    left = max(0, min(width - crop_size, int(center_x - crop_size / 2)))
    top = max(0, min(height - crop_size, int(center_y - crop_size / 2)))
    return image.crop((left, top, left + crop_size, top + crop_size))


def face_focused_portrait(image, target_ratio=4 / 5):
    face_box = detect_face_box(image, min_size=(50, 50))
    width, height = image.size

    if face_box is not None:
        left, top, face_width, face_height = face_box
        center_x = left + face_width / 2
        center_y = top + face_height * 1.35
    else:
        center_x = width / 2
        center_y = height * 0.48

    crop_height = height
    crop_width = int(crop_height * target_ratio)
    if crop_width > width:
        crop_width = width
        crop_height = int(crop_width / target_ratio)

    left = max(0, min(width - crop_width, int(center_x - crop_width / 2)))
    top = max(0, min(height - crop_height, int(center_y - crop_height / 2)))
    return image.crop((left, top, left + crop_width, top + crop_height))


def optimize_image_file(
    image_path,
    *,
    fit_size=None,
    max_size=None,
    quality=82,
    background="#ffffff",
    crop_alpha=False,
    pre_crop=None,
):
    image_path = Path(image_path)
    if not image_path.exists():
        return

    with Image.open(image_path) as image:
        image = ImageOps.exif_transpose(image)
        has_alpha = image.mode in ("RGBA", "LA") or ("transparency" in image.info)
        if has_alpha:
            image = image.convert("RGBA")
            if crop_alpha:
                alpha_box = image.getbbox()
                if alpha_box:
                    image = image.crop(alpha_box)
        else:
            image = image.convert("RGB")

        if pre_crop:
            image = pre_crop(image)

        if fit_size:
            image = ImageOps.fit(image, fit_size, method=Image.Resampling.LANCZOS)
        elif max_size:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

        suffix = image_path.suffix.lower()
        if suffix == ".webp":
            image.save(image_path, "WEBP", quality=quality, method=6)
            return

        if suffix == ".png" and has_alpha:
            image.save(image_path, "PNG", optimize=True, compress_level=9)
            return

        if image.mode == "RGBA":
            canvas = Image.new("RGB", image.size, background)
            canvas.paste(image, mask=image.getchannel("A"))
            image = canvas
        else:
            image = image.convert("RGB")

        if suffix == ".png":
            image.save(image_path, "PNG", optimize=True, compress_level=9)
        else:
            image.save(image_path, "JPEG", quality=quality, optimize=True, progressive=True)
