"""
SilkyNet Flask API
Silkworm segmentation and counting service
"""

import os
import io
import base64
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import numpy as np
from PIL import Image
import cv2
from api.inference import SilkyNetInference

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Initialize model
MODEL_PATH = os.getenv('MODEL_PATH', 'Unet.hdf5')
silkynet = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def init_model():
    """Initialize the model (lazy loading)"""
    global silkynet
    if silkynet is None:
        if os.path.exists(MODEL_PATH):
            silkynet = SilkyNetInference(MODEL_PATH)
            print(f"✅ Model loaded from {MODEL_PATH}")
        else:
            print(f"⚠️  Model not found at {MODEL_PATH}")
    return silkynet

@app.route('/')
def index():
    """Serve the web interface"""
    return render_template('index.html')

@app.route('/api/health')
def health():
    """Health check endpoint"""
    model_loaded = silkynet is not None
    return jsonify({
        'status': 'healthy',
        'model_loaded': model_loaded,
        'version': '1.0.0'
    })

@app.route('/api/segment', methods=['POST'])
def segment():
    """
    Segment silkworm image and return mask + count

    Request:
        - file: Image file (multipart/form-data)
        OR
        - image: Base64 encoded image (JSON)

    Response:
        {
            "success": true,
            "count": 15,
            "segmentation_mask": "base64_image_data",
            "confidence": 0.85,
            "metadata": {...}
        }
    """
    try:
        # Initialize model if needed
        model = init_model()
        if model is None:
            return jsonify({
                'success': False,
                'error': 'Model not loaded. Please ensure Unet.hdf5 is available.'
            }), 500

        # Get image from request
        image = None

        # Method 1: File upload
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'}), 400

            if not allowed_file(file.filename):
                return jsonify({
                    'success': False,
                    'error': 'Invalid file type. Allowed: png, jpg, jpeg'
                }), 400

            # Read image
            image_bytes = file.read()
            image = Image.open(io.BytesIO(image_bytes))

        # Method 2: Base64 encoded image
        elif request.is_json and 'image' in request.json:
            image_data = request.json['image']
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))

        else:
            return jsonify({
                'success': False,
                'error': 'No image provided. Send as file or base64.'
            }), 400

        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Run inference
        result = model.predict(image)

        # Convert mask to base64
        mask_img = Image.fromarray((result['mask'] * 255).astype(np.uint8))
        buffer = io.BytesIO()
        mask_img.save(buffer, format='PNG')
        mask_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # Convert visualization to base64 if available
        viz_base64 = None
        if result.get('visualization') is not None:
            viz_img = Image.fromarray(result['visualization'])
            buffer = io.BytesIO()
            viz_img.save(buffer, format='JPEG', quality=85)
            viz_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return jsonify({
            'success': True,
            'count': result['total_count'],
            'segmentation_mask': f"data:image/png;base64,{mask_base64}",
            'visualization': f"data:image/jpeg;base64,{viz_base64}" if viz_base64 else None,
            'confidence': result.get('confidence', 0.0),
            'metadata': {
                'overlapped': result.get('overlapped_count', 0),
                'partial': result.get('partial_count', 0),
                'artifacts': result.get('artifacts_count', 0),
                'individual': result.get('individual_count', 0)
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/batch', methods=['POST'])
def batch_segment():
    """
    Process multiple images in batch

    Request:
        - files: Multiple image files

    Response:
        {
            "success": true,
            "results": [...]
        }
    """
    try:
        model = init_model()
        if model is None:
            return jsonify({
                'success': False,
                'error': 'Model not loaded'
            }), 500

        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'No files provided'}), 400

        files = request.files.getlist('files')
        if len(files) > 10:
            return jsonify({
                'success': False,
                'error': 'Maximum 10 files per batch'
            }), 400

        results = []
        for file in files:
            if file and allowed_file(file.filename):
                image_bytes = file.read()
                image = Image.open(io.BytesIO(image_bytes))

                if image.mode != 'RGB':
                    image = image.convert('RGB')

                result = model.predict(image)
                results.append({
                    'filename': secure_filename(file.filename),
                    'count': result['total_count'],
                    'metadata': {
                        'overlapped': result.get('overlapped_count', 0),
                        'partial': result.get('partial_count', 0),
                        'artifacts': result.get('artifacts_count', 0)
                    }
                })

        return jsonify({
            'success': True,
            'total_processed': len(results),
            'results': results
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum size is 16MB.'
    }), 413

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Run app
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
