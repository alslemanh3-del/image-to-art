import argparse
import cv2

from src.filters import apply_filter
from src.video import run_video_mode

def process_image(input_path, output_path, filter_name):
    image = cv2.imread(input_path)
    if image is None:
        print(f"❌ لم يتم العثور على الصورة: {input_path}")
        return
    result = apply_filter(image, filter_name, blur_val=9, edge_val=9)
    cv2.imwrite(output_path, result)
    print(f"✅ تم الحفظ في: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Image to Art Converter")
    parser.add_argument("--mode", choices=["image", "video"], default="image")
    parser.add_argument("--input", required=True, help="مسار الصورة أو رقم الكاميرا (0)")
    parser.add_argument("--output", default="result.jpg")
    parser.add_argument("--filter", choices=["sketch", "color_sketch", "cartoon", "background"], default="sketch")
    args = parser.parse_args()

    if args.mode == "image":
        process_image(args.input, args.output, args.filter)
    else:
        run_video_mode(int(args.input), args.filter)

if __name__ == "__main__":
    main()