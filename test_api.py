#!/usr/bin/env python3
"""
Test script for SilkyNet API
Run this after starting the server to verify everything works
"""

import requests
import json
import sys
import os


def test_health(base_url):
    """Test health endpoint"""
    print("Testing /api/health...")
    try:
        response = requests.get(f"{base_url}/api/health")
        data = response.json()

        print(f"✅ Status: {data.get('status')}")
        print(f"✅ Model loaded: {data.get('model_loaded')}")
        print(f"✅ Version: {data.get('version')}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_segment(base_url, image_path):
    """Test segmentation endpoint"""
    print(f"\nTesting /api/segment with {image_path}...")

    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return False

    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{base_url}/api/segment",
                files=files,
                timeout=60
            )

        if response.status_code != 200:
            print(f"❌ Request failed: {response.status_code}")
            print(response.text)
            return False

        data = response.json()

        if not data.get('success'):
            print(f"❌ Segmentation failed: {data.get('error')}")
            return False

        print(f"✅ Success!")
        print(f"   Total count: {data.get('count')}")
        print(f"   Confidence: {data.get('confidence', 0):.2%}")
        print(f"   Individual: {data.get('metadata', {}).get('individual', 0)}")
        print(f"   Overlapped: {data.get('metadata', {}).get('overlapped', 0)}")
        print(f"   Partial: {data.get('metadata', {}).get('partial', 0)}")
        print(f"   Artifacts: {data.get('metadata', {}).get('artifacts', 0)}")

        return True
    except Exception as e:
        print(f"❌ Segmentation test failed: {e}")
        return False


def test_batch(base_url, image_paths):
    """Test batch endpoint"""
    print(f"\nTesting /api/batch with {len(image_paths)} images...")

    # Filter existing images
    existing = [p for p in image_paths if os.path.exists(p)]

    if not existing:
        print("❌ No valid images found")
        return False

    try:
        files = [('files', open(path, 'rb')) for path in existing]
        response = requests.post(
            f"{base_url}/api/batch",
            files=files,
            timeout=180
        )

        # Close files
        for _, f in files:
            f.close()

        if response.status_code != 200:
            print(f"❌ Request failed: {response.status_code}")
            return False

        data = response.json()

        if not data.get('success'):
            print(f"❌ Batch processing failed: {data.get('error')}")
            return False

        print(f"✅ Success!")
        print(f"   Total processed: {data.get('total_processed')}")

        for result in data.get('results', []):
            print(f"   - {result['filename']}: {result['count']} larvae")

        return True
    except Exception as e:
        print(f"❌ Batch test failed: {e}")
        return False


def main():
    # Configuration
    BASE_URL = os.getenv('API_URL', 'http://localhost:5000')

    print("=" * 50)
    print("SilkyNet API Test Suite")
    print("=" * 50)
    print(f"Testing API at: {BASE_URL}\n")

    # Test 1: Health check
    health_ok = test_health(BASE_URL)

    if not health_ok:
        print("\n⚠️  Health check failed. Is the server running?")
        print("Start server with: python app.py")
        sys.exit(1)

    # Test 2: Single image segmentation
    test_images = [
        'data/larvaTest/img/1.jpg',
        'data/larvaTest/img/10.jpg',
        'data/20221127/1.jpg'
    ]

    test_image = None
    for img in test_images:
        if os.path.exists(img):
            test_image = img
            break

    if test_image:
        segment_ok = test_segment(BASE_URL, test_image)
    else:
        print("\n⚠️  No test images found. Skipping segmentation test.")
        print("   Place test images in data/larvaTest/img/")
        segment_ok = False

    # Test 3: Batch processing
    batch_images = [
        'data/larvaTest/img/1.jpg',
        'data/larvaTest/img/10.jpg',
        'data/larvaTest/img/100.jpg'
    ]

    existing_batch = [p for p in batch_images if os.path.exists(p)]

    if len(existing_batch) >= 2:
        batch_ok = test_batch(BASE_URL, existing_batch)
    else:
        print("\n⚠️  Not enough images for batch test (need 2+)")
        batch_ok = False

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    print(f"Health Check:  {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"Segmentation:  {'✅ PASS' if segment_ok else '⚠️  SKIP'}")
    print(f"Batch Process: {'✅ PASS' if batch_ok else '⚠️  SKIP'}")

    if health_ok and (segment_ok or not test_image):
        print("\n🎉 All available tests passed!")
        print(f"\n🌐 Web interface: {BASE_URL}")
        print(f"📡 API endpoint: {BASE_URL}/api/segment")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
