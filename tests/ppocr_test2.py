import cv2
from paddleocr import PaddleOCR

# Initialize PaddleOCR
# Set use_angle_cls to True for angle classification, and specify the language
ocr = PaddleOCR(use_angle_cls=True) 

# Load an image using OpenCV, which returns a NumPy array
# Replace 'path/to/your/image.jpg' with the actual path to your image
img_path = 'assets/images/screenshot_1.jpeg'
img_np_array = cv2.imread(img_path)
print(img_np_array.shape)

# Ensure the image is loaded correctly
if img_np_array is None:
    print(f"Error: Could not load image from {img_path}")
else:
    # Perform OCR prediction on the NumPy array
    result = ocr.ocr(img_np_array)

    # Process and print the results
    for line in result:
        # Each line contains bounding box coordinates, recognized text, and confidence score
        print(line)
