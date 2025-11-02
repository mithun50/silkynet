# 🐛 SilkyNet API Documentation

AI-powered silkworm segmentation and counting service built with Flask.

---

## 🚀 Quick Start

### Local Development

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Place Model File**
Ensure your trained model `Unet.hdf5` is in the project root directory.

3. **Run Server**
```bash
python app.py
```

Server runs on `http://localhost:5000`

---

## 🌐 Deploy to Render

### Method 1: GitHub Integration (Recommended)

1. **Push to GitHub**
```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

2. **Create Render Account**
- Go to [render.com](https://render.com)
- Sign up with GitHub

3. **Deploy**
- Click "New +" → "Web Service"
- Connect your GitHub repository
- Render will auto-detect settings from `render.yaml`
- Click "Create Web Service"

4. **Upload Model**
After deployment:
- Go to your service dashboard
- Navigate to "Shell" tab
- Upload `Unet.hdf5` to the root directory

OR use Render Disk (persistent storage):
- Create a Disk in Render dashboard
- Attach it to your service
- Upload model file via shell or SFTP

### Method 2: Manual Deployment

1. **Connect Repository**
```bash
# In Render dashboard
Repository: https://github.com/yourusername/silkynet
Branch: main
```

2. **Configure Service**
```
Name: silkynet-api
Environment: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

3. **Environment Variables**
```
PYTHON_VERSION=3.10.0
PORT=10000
```

---

## 📡 API Endpoints

### Health Check

**GET** `/api/health`

Check if API is running and model is loaded.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "1.0.0"
}
```

---

### Single Image Segmentation

**POST** `/api/segment`

Segment a single silkworm image and return count.

**Request (multipart/form-data):**
```bash
curl -X POST http://localhost:5000/api/segment \
  -F "file=@silkworm_image.jpg"
```

**Request (JSON with base64):**
```bash
curl -X POST http://localhost:5000/api/segment \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
  }'
```

**Response:**
```json
{
  "success": true,
  "count": 15,
  "segmentation_mask": "data:image/png;base64,...",
  "visualization": "data:image/jpeg;base64,...",
  "confidence": 0.87,
  "metadata": {
    "individual": 12,
    "overlapped": 2,
    "partial": 1,
    "artifacts": 3
  }
}
```

**Fields:**
- `count`: Total silkworm count
- `segmentation_mask`: Binary mask (base64 PNG)
- `visualization`: Original image with contours overlay (base64 JPEG)
- `confidence`: Model confidence score (0-1)
- `metadata.individual`: Non-overlapping larvae
- `metadata.overlapped`: Overlapped larvae detected
- `metadata.partial`: Partially visible larvae
- `metadata.artifacts`: Noise/artifacts filtered out

---

### Batch Processing

**POST** `/api/batch`

Process multiple images at once (max 10 per request).

**Request:**
```bash
curl -X POST http://localhost:5000/api/batch \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F "files=@image3.jpg"
```

**Response:**
```json
{
  "success": true,
  "total_processed": 3,
  "results": [
    {
      "filename": "image1.jpg",
      "count": 15,
      "metadata": {
        "individual": 12,
        "overlapped": 2,
        "partial": 1,
        "artifacts": 3
      }
    },
    {
      "filename": "image2.jpg",
      "count": 18,
      "metadata": {...}
    },
    ...
  ]
}
```

---

## 🌐 Web Interface

Access the web UI at the root URL: `http://your-app.onrender.com`

Features:
- Drag & drop image upload
- Real-time processing
- Visual segmentation results
- Detailed counting statistics
- Confidence scoring

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `5000` |
| `MODEL_PATH` | Path to model file | `Unet.hdf5` |

### Model Requirements

- **Format**: Keras HDF5 (`.hdf5` or `.h5`)
- **Architecture**: U-Net
- **Input**: RGB images (512×512)
- **Output**: Binary segmentation mask

### File Upload Limits

- **Max file size**: 16MB
- **Allowed formats**: JPG, JPEG, PNG
- **Batch limit**: 10 images per request

---

## 🧪 Testing

### Test Health Endpoint
```bash
curl http://localhost:5000/api/health
```

### Test Segmentation
```bash
curl -X POST http://localhost:5000/api/segment \
  -F "file=@data/larvaTest/img/1.jpg"
```

### Test from Python
```python
import requests

url = "http://localhost:5000/api/segment"
files = {'file': open('silkworm_image.jpg', 'rb')}
response = requests.post(url, files=files)
print(response.json())
```

### Test from JavaScript
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('/api/segment', {
  method: 'POST',
  body: formData
})
.then(res => res.json())
.then(data => console.log(data));
```

---

## 📊 Performance

### Expected Response Times

| Operation | Time | Notes |
|-----------|------|-------|
| Health check | <100ms | Instant |
| Single image | 10-30s | Depends on image size |
| Batch (10 images) | 60-180s | Sequential processing |

### Optimization Tips

1. **Resize large images** before upload
2. **Use batch endpoint** for multiple images
3. **Enable model caching** (already implemented)
4. **Scale horizontally** on Render (paid plans)

---

## 🐛 Troubleshooting

### Model Not Loaded

**Error:** `Model not loaded. Please ensure Unet.hdf5 is available.`

**Solution:**
- Verify `Unet.hdf5` exists in project root
- Check file permissions
- On Render: Upload model via Shell or Disk

### Out of Memory

**Error:** `MemoryError` or process killed

**Solution:**
- Upgrade Render plan (512MB → 2GB+ RAM)
- Reduce batch size
- Process images sequentially

### Slow Performance

**Solution:**
- Images >2MB: Resize before upload
- Use dedicated instance (Render paid plans)
- Consider GPU acceleration (advanced)

### CORS Issues

**Error:** `CORS policy blocked`

**Solution:**
Already handled by `flask-cors`. If issues persist:
```python
# In app.py, customize CORS
CORS(app, origins=['https://your-frontend.com'])
```

---

## 🔐 Security Considerations

### Production Checklist

- [ ] Set `debug=False` in production
- [ ] Add rate limiting (Flask-Limiter)
- [ ] Implement API authentication
- [ ] Enable HTTPS (automatic on Render)
- [ ] Validate all file uploads
- [ ] Set up monitoring/logging

### Rate Limiting (Optional)

```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    default_limits=["100 per hour"]
)

@app.route('/api/segment')
@limiter.limit("10 per minute")
def segment():
    ...
```

---

## 📈 Monitoring

### Render Logs

View logs in Render dashboard:
- Real-time log streaming
- Filter by severity
- Download historical logs

### Health Monitoring

```bash
# Ping health endpoint
curl https://your-app.onrender.com/api/health

# Set up uptime monitoring (UptimeRobot, Pingdom)
```

---

## 🚀 Scaling

### Vertical Scaling (Render)

Upgrade instance type:
- Free: 512MB RAM
- Starter: 2GB RAM ($7/mo)
- Standard: 4GB RAM ($25/mo)

### Horizontal Scaling

Deploy multiple instances:
- Load balancer (Render Pro)
- Session affinity
- Shared model storage

### Optimization

1. **Model Optimization**
   - Convert to ONNX for faster inference
   - Quantization (FP16, INT8)
   - Model pruning

2. **Caching**
   - Cache repeated requests
   - Redis for distributed caching

3. **Async Processing**
   - Background job queue (Celery)
   - WebSocket for progress updates

---

## 🤝 Contributing

### Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run in debug mode
export FLASK_ENV=development
python app.py
```

### Code Structure

```
silkynet/
├── app.py                 # Flask application
├── api/
│   ├── __init__.py
│   └── inference.py       # Model inference logic
├── templates/
│   └── index.html         # Web interface
├── static/                # CSS, JS (if needed)
├── uploads/               # Temporary uploads
├── requirements.txt       # Python dependencies
└── render.yaml           # Render configuration
```

---

## 📞 Support

### Common Issues

1. **Model accuracy low on new breeds**
   - Solution: Fine-tune model with new breed data
   - See main README for retraining instructions

2. **API timeout on large images**
   - Solution: Resize images to 1024×1024 max
   - Use image compression before upload

3. **Deployment fails on Render**
   - Check build logs
   - Verify requirements.txt versions
   - Ensure Python 3.10+ compatibility

### Resources

- Main Documentation: `README.md`
- Training Guide: `Silkynet.py`
- Render Docs: https://render.com/docs
- Flask Docs: https://flask.palletsprojects.com/

---

## 📄 License

GNU General Public License v3.0 - Same as main project

---

## 🎯 Next Steps

1. ✅ Deploy to Render
2. ⏳ Upload trained model
3. ⏳ Test API endpoints
4. ⏳ Share your live URL!

**Example Live URL:** `https://silkynet-api-xxxx.onrender.com`

---

**Happy Counting! 🐛✨**
