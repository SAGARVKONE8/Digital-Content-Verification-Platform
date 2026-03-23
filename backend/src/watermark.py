import sys
import cv2
import numpy as np
import os

# ---------- IMAGE WATERMARKING ----------

def add_visible_watermark(image_path, text):
    try:
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Could not read image from {image_path}", file=sys.stderr)
            return False

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.5, min(image.shape[1] / 800.0, image.shape[0] / 800.0))
        color = (255, 255, 255)
        thickness = max(1, int(font_scale * 2))

        position = (20, image.shape[0] - 30)
        cv2.putText(image, text, position, font, font_scale, color, thickness, cv2.LINE_AA)

        cv2.imwrite(image_path, image)
        return True

    except Exception as e:
        print(f"Error in visible watermark: {e}", file=sys.stderr)
        return False


def embed_lsb_watermark(image_path, text):
    try:
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Could not read image from {image_path}", file=sys.stderr)
            return False

        separator = "<END>"
        payload = text + separator
        bits = ''.join([format(ord(ch), '08b') for ch in payload])

        h, w, c = image.shape
        capacity = h * w * c
        if len(bits) > capacity:
            print("Error: Watermark is too large for this image", file=sys.stderr)
            return False

        flat = image.flatten()
        for i, b in enumerate(bits):
            flat[i] = (flat[i] & ~1) | int(b)
        watermarked = flat.reshape(image.shape)

        cv2.imwrite(image_path, watermarked)
        return True

    except Exception as e:
        print(f"Error in LSB watermark: {e}", file=sys.stderr)
        return False


def extract_lsb_watermark(image_path):
    try:
        image = cv2.imread(image_path)
        if image is None:
            return None

        flat = image.flatten()
        bits = ''.join(str(pixel & 1) for pixel in flat)

        chars = [chr(int(bits[i:i+8], 2)) for i in range(0, len(bits), 8)]
        data = ''.join(chars)
        if '<END>' in data:
            return data.split('<END>')[0]
        return None

    except Exception:
        return None


# ---------- VIDEO WATERMARKING ----------

def add_visible_watermark_video(video_path, text):
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video {video_path}", file=sys.stderr)
            return False

        fps = cap.get(cv2.CAP_PROP_FPS) or 24
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")

        temp_output = f"{video_path}.watermarked.mp4"
        writer = cv2.VideoWriter(temp_output, fourcc, fps, (width, height))

        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % 5 == 0:
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = max(0.5, width / 1200.0)
                color = (255, 255, 255)
                thickness = 2
                position = (20, height - 30)
                cv2.putText(frame, text, position, font, font_scale, color, thickness, cv2.LINE_AA)

            writer.write(frame)
            frame_count += 1

        cap.release()
        writer.release()

        os.replace(temp_output, video_path)
        return True

    except Exception as e:
        print(f"Error in video watermark: {e}", file=sys.stderr)
        return False


# ---------- CLI INTERFACE ----------

if __name__ == "__main__":
    # Backwards compatibility: python watermark.py <file> <text>
    if len(sys.argv) == 3:
        file_path = sys.argv[1]
        text = sys.argv[2]
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
            success = add_visible_watermark_video(file_path, text)
        else:
            success = add_visible_watermark(file_path, text)

        if not success:
            sys.exit(1)
        print(f"Successfully watermarked {file_path}")
        sys.exit(0)

    if len(sys.argv) >= 4:
        asset_type = sys.argv[1].lower()  # image/video
        file_path = sys.argv[2]
        text = sys.argv[3]
        mode = (sys.argv[4].lower() if len(sys.argv) >= 5 else 'visible')

        if asset_type == 'image':
            if mode == 'invisible-lsb':
                success = embed_lsb_watermark(file_path, text)
            else:
                success = add_visible_watermark(file_path, text)
        elif asset_type == 'video':
            success = add_visible_watermark_video(file_path, text)
        else:
            print('Unsupported asset type for watermarking', file=sys.stderr)
            sys.exit(1)

        if not success:
            sys.exit(1)

        print(f"Successfully watermarked {file_path} (asset_type={asset_type} mode={mode})")
        sys.exit(0)

    print("Usage: python watermark.py <image/video> <file_path> <watermark_text> [visible|invisible-lsb]", file=sys.stderr)
    sys.exit(1)