import cv2
from src.filters import apply_filter

FILTERS = ["sketch", "color_sketch", "cartoon", "background"]
FILTER_LABELS = {
    "sketch": "Pencil Sketch",
    "color_sketch": "Color Sketch",
    "cartoon": "Cartoon",
    "background": "Background Color",
}

current_filter_index = 0


def mouse_callback(event, x, y, flags, param):
    global current_filter_index
    if event == cv2.EVENT_LBUTTONDOWN:
        current_filter_index = (current_filter_index + 1) % len(FILTERS)


def empty(a):
    pass


def run_video_mode(camera_index: int = 0, initial_filter: str = "sketch") -> None:
    global current_filter_index

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("❌ تعذّر فتح الكاميرا.")
        return

    # ضبط الفلتر الابتدائي
    if initial_filter in FILTERS:
        current_filter_index = FILTERS.index(initial_filter)
    else:
        current_filter_index = 0

    window_name = "Image to Art - Video"
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, mouse_callback)

    cv2.createTrackbar("Blur", window_name, 9, 50, empty)
    cv2.createTrackbar("Edge", window_name, 9, 50, empty)

    print(f"\n✅ الكاميرا تعمل الآن. الفلتر الحالي: {FILTER_LABELS[FILTERS[current_filter_index]]}")
    print("🖱️ اضغط بزر الفأرة الأيسر لتبديل الفلتر.")
    print("❌ للإغلاق: اضغط Esc.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        blur_val = cv2.getTrackbarPos("Blur", window_name)
        edge_val = cv2.getTrackbarPos("Edge", window_name)

        if blur_val < 1: blur_val = 1
        if edge_val < 1: edge_val = 1

        current_filter = FILTERS[current_filter_index]
        result = apply_filter(frame, current_filter, blur_val, edge_val)

        cv2.putText(result, f"Filter: {FILTER_LABELS[current_filter]}", (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(result, "Left Click: Change Filter", (10, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.imshow(window_name, result)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
        elif key == 38 or key == 40:
            current_filter_index = (current_filter_index + 1) % len(FILTERS)

    cap.release()
    cv2.destroyAllWindows()