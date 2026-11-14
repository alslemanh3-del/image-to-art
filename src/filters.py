import cv2
import numpy as np
import mediapipe as mp

# تهيئة نموذج MediaPipe لعزل الشخص (نحتاجه لفلتر الخلفية)
mp_selfie_segmentation = mp.solutions.selfie_segmentation
segmenter = mp_selfie_segmentation.SelfieSegmentation(model_selection=1)


def pencil_sketch(image: np.ndarray, detail: int = 21) -> np.ndarray:
    """تحويل الصورة إلى رسم بالقلم الرصاص مع التحكم في الوضوح."""
    if detail % 2 == 0:
        detail += 1

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    inverted = 255 - gray
    blurred = cv2.GaussianBlur(inverted, (detail, detail), 0)
    inverted_blur = 255 - blurred
    sketch = cv2.divide(gray, inverted_blur, scale=256.0)
    return sketch


def color_sketch(image: np.ndarray, detail: int = 21) -> np.ndarray:
    """رسم رصاص ملوّن (يحافظ على ألوان الصورة الأصلية)."""
    sketch = pencil_sketch(image, detail)
    sketch_bgr = cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)
    result = cv2.addWeighted(image, 0.5, sketch_bgr, 0.5, 0)
    return result


def cartoon_effect(image: np.ndarray, blur_value: int = 9, edge_value: int = 9) -> np.ndarray:
    """تحويل الصورة إلى تأثير كرتوني مع إمكانية التحكم في التمويه والحواف."""
    if blur_value % 2 == 0: blur_value += 1
    if edge_value % 2 == 0: edge_value += 1

    color = cv2.bilateralFilter(image, d=blur_value, sigmaColor=300, sigmaSpace=300)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    edges = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY,
        blockSize=edge_value, C=9
    )

    edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    cartoon = cv2.bitwise_and(color, edges_bgr)
    return cartoon


def background_removal_effect(image: np.ndarray) -> np.ndarray:
    """عزل الشخص وجعل الخلفية رمادية (أبيض وأسود)."""
    # تحويل الصورة إلى RGB لأن MediaPipe يتطلب ذلك
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # الحصول على قناع العزل
    results = segmenter.process(image_rgb)
    mask = results.segmentation_mask

    # تحويل الصورة الأصلية إلى رمادية
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    # تحويل القناع إلى 3 قنوات ليتوافق مع أبعاد الصورة
    mask_3d = np.stack((mask,) * 3, axis=-1)

    # عتبة العزل: القيم الأكبر من 0.5 تعتبر شخص، وما دونها تعتبر خلفية
    condition = mask_3d > 0.5

    # دمج الصورة الأصلية مع الرمادية بناءً على القناع
    result = np.where(condition, image, gray_bgr)

    return result


def apply_filter(image: np.ndarray, filter_name: str, blur_val: int = 9, edge_val: int = 9,
                 sketch_detail: int = 21) -> np.ndarray:
    """واجهة موحّدة لاختيار الفلتر بالاسم مع تمرير قيم التحكم."""
    if filter_name == "sketch":
        result = pencil_sketch(image, sketch_detail)
    elif filter_name == "color_sketch":
        result = color_sketch(image, sketch_detail)
    elif filter_name == "cartoon":
        result = cartoon_effect(image, blur_val, edge_val)
    elif filter_name == "background":
        result = background_removal_effect(image)
    else:
        raise ValueError(f"فلتر غير معروف: {filter_name}")

    # التأكد من أن النتيجة 3 قنوات (BGR) حتى لو كان الفلتر يعيد صورة رمادية
    if len(result.shape) == 2:
        result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

    return result