from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import cv2
from skimage import exposure
from skimage.restoration import denoise_nl_means, estimate_sigma
from pathlib import Path
import base64
import os

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

def enhance_signal(image):
    # Histogram equalization
    image_eq = exposure.equalize_hist(image)
    
    # Contrast Limited Adaptive Histogram Equalization (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    image_clahe = clahe.apply((image * 255).astype(np.uint8)) / 255.0
    
    # Gamma correction for better brightness
    gamma = 1.2
    image_gamma = np.power(image, gamma)
    
    # Sharpening using unsharp masking
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    image_sharp = cv2.filter2D(image, -1, kernel)
    
    # Combine all enhancements (adjust weights as needed)
    enhanced_image = 0.3 * image_eq + 0.3 * image_clahe + 0.2 * image_gamma + 0.2 * image_sharp
    enhanced_image = np.clip(enhanced_image, 0, 1)  # Keep pixel values in [0, 1]
    
    return enhanced_image

def reduce_noise(image):
    # Estimate noise
    sigma_est = np.mean(estimate_sigma(image))
    
    # Non-local means denoising
    image_nlm = denoise_nl_means(image, h=1.15 * sigma_est, fast_mode=True,
                                 patch_size=5, patch_distance=3)
    
    # Bilateral filtering for smoothing while preserving edges
    image_bilateral = cv2.bilateralFilter((image * 255).astype(np.uint8), d=9,
                                          sigmaColor=75, sigmaSpace=75) / 255.0
    
    # Wavelet denoising for grayscale images
    image_wavelet = cv2.fastNlMeansDenoising((image * 255).astype(np.uint8), None, 10, 7, 21) / 255.0
    
    # Combine denoising techniques (adjust weights)
    denoised_image = 0.4 * image_nlm + 0.3 * image_bilateral + 0.3 * image_wavelet
    denoised_image = np.clip(denoised_image, 0, 1)  # Keep pixel values in [0, 1]
    
    return denoised_image

def process_image(image_path):
    # Read the image as grayscale
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    
    if image is None:
        raise ValueError(f"Could not read the image at {image_path}")
    
    # Normalize the image to float32 in range [0, 1]
    image = image.astype(np.float32) / 255.0
    
    # Enhance the signal
    enhanced_image = enhance_signal(image)
    
    # Reduce noise
    denoised_image = reduce_noise(enhanced_image)
    
    return enhanced_image, denoised_image

@app.route('/api/process-image', methods=['POST'])
def process_image_api():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    image_file = request.files['image']
    temp_path = Path('temp_image.png')
    image_file.save(temp_path)

    try:
        enhanced_image, denoised_image = process_image(temp_path)

        # Convert numpy arrays to base64 encoded strings
        _, enhanced_buffer = cv2.imencode('.png', (enhanced_image * 255).astype(np.uint8))
        enhanced_base64 = base64.b64encode(enhanced_buffer).decode('utf-8')

        _, denoised_buffer = cv2.imencode('.png', (denoised_image * 255).astype(np.uint8))
        denoised_base64 = base64.b64encode(denoised_buffer).decode('utf-8')

        return jsonify({
            'enhancedImage': enhanced_base64,
            'denoisedImage': denoised_base64
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up temporary file
        if temp_path.exists():
            os.remove(temp_path)

if __name__ == '__main__':
    app.run(debug=True)