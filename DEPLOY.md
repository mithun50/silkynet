# 🚀 Quick Deployment Guide

## Step-by-Step: Deploy to Render

### 1️⃣ Prepare Repository

```bash
# Add all new files
git add app.py api/ templates/ requirements.txt render.yaml .gitignore README_API.md

# Commit
git commit -m "Add Flask API for deployment"

# Push to GitHub
git push origin main
```

### 2️⃣ Deploy on Render

1. Go to **[render.com](https://render.com)**
2. Click **"Sign Up"** (use GitHub)
3. Click **"New +"** → **"Web Service"**
4. **Connect your repository**:
   - Select: `silkynet` repository
   - Branch: `main`
5. Render auto-detects settings from `render.yaml` ✅
6. Click **"Create Web Service"**

### 3️⃣ Upload Model File

**Option A: Via Shell (After Deployment)**

1. Go to your service dashboard
2. Click **"Shell"** tab
3. Upload `Unet.hdf5`:
```bash
# On your local machine, use SCP or:
# 1. Convert model to base64
base64 Unet.hdf5 > model.txt

# 2. In Render shell, decode
cat > Unet.hdf5 << EOF
[paste base64 content]
EOF
base64 -d Unet.hdf5
```

**Option B: Via Render Disk (Recommended)**

1. In Render dashboard → **"Disks"**
2. Click **"New Disk"**
   - Name: `model-storage`
   - Size: 1GB
3. Attach disk to your web service
4. Mount path: `/opt/render/project/src`
5. Upload model via SFTP or shell

**Option C: GitHub LFS (Large Files)**

```bash
# Install Git LFS
git lfs install

# Track .hdf5 files
git lfs track "*.hdf5"

# Add and commit
git add .gitattributes Unet.hdf5
git commit -m "Add model with LFS"
git push
```

### 4️⃣ Test Your API

```bash
# Replace with your Render URL
export API_URL="https://silkynet-api-xxxx.onrender.com"

# Test health
curl $API_URL/api/health

# Test segmentation
curl -X POST $API_URL/api/segment \
  -F "file=@data/larvaTest/img/1.jpg"
```

### 5️⃣ Access Web Interface

Open in browser:
```
https://your-app-name.onrender.com
```

---

## ⚠️ Important Notes

### First Request is Slow
- Render free tier spins down after 15min inactivity
- First request takes 30-60s to wake up
- Subsequent requests are fast

### Model File Size
- If model >100MB, use Render Disk or external storage
- Consider model compression (ONNX, quantization)

### Free Tier Limits
- 750 hours/month
- 512MB RAM (may need upgrade for TensorFlow)
- Spins down after inactivity

### Upgrade if Needed
- **Starter Plan**: $7/month
  - 2GB RAM (recommended for ML)
  - Always on
  - Faster builds

---

## 🔍 Troubleshooting

### Build Fails: "Out of Memory"

Render free tier has limited RAM for builds.

**Solution 1**: Reduce dependencies
```txt
# Use lighter versions
tensorflow-cpu==2.13.0  # Instead of full TensorFlow
opencv-python-headless==4.8.0.76  # Headless version
```

**Solution 2**: Upgrade to Starter plan ($7/mo)

### Model Not Found

**Error**: `Model not loaded. Please ensure Unet.hdf5 is available.`

**Check**:
```bash
# In Render Shell
ls -lh Unet.hdf5

# Should show file size, e.g., 87M
```

### API Timeout

**Error**: 504 Gateway Timeout

**Cause**: Image processing takes >30s

**Solution**:
- Upgrade Render plan (more CPU)
- Resize images before upload
- Optimize model (ONNX conversion)

---

## 🎯 Post-Deployment Checklist

- [ ] API responds at `/api/health`
- [ ] Web interface loads
- [ ] Image upload works
- [ ] Segmentation returns results
- [ ] Counts are reasonable
- [ ] No errors in Render logs

---

## 📱 Share Your API

Your API is now live! Share with others:

**Web Interface:**
```
https://your-app.onrender.com
```

**API Endpoint:**
```
https://your-app.onrender.com/api/segment
```

**Example cURL:**
```bash
curl -X POST https://your-app.onrender.com/api/segment \
  -F "file=@silkworm_image.jpg"
```

---

## 🚀 What's Next?

1. **Custom Domain** (Render Pro)
2. **API Authentication** (JWT tokens)
3. **Rate Limiting** (prevent abuse)
4. **Analytics** (track usage)
5. **Model Versioning** (A/B testing)
6. **Multi-breed Support** (breed selector)

---

**Congratulations! Your SilkyNet API is live! 🎉🐛**
