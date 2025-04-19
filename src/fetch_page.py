from detect import process_pdf
import cv2

images = process_pdf('./papers/scan_004_20250418_201709.pdf')

for i, image in enumerate(images):
    cv2.imwrite(f'/tmp/{i}.png', image)
