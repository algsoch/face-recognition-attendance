#!/usr/bin/env python3
"""
Test user uploaded photo against stored face database
"""

import cv2
import numpy as np
import os
import sys
from backend.robust_face_recognition import enhanced_face_recognizer

def test_uploaded_photo(photo_path):
    """Test an uploaded photo against the face database"""
    
    print(f"Testing photo: {photo_path}")
    
    # Check if photo exists
    if not os.path.exists(photo_path):
        print(f"Photo not found: {photo_path}")
        return None
    
    try:
        # Load the test photo
        test_img = cv2.imread(photo_path)
        if test_img is None:
            print("Failed to load image")
            return None
            
        print(f"Loaded image with shape: {test_img.shape}")
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces in the uploaded photo
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
        
        if len(faces) == 0:
            print("No faces detected in the uploaded photo")
            return None
            
        print(f"Detected {len(faces)} face(s) in the photo")
        
        # Use the first (largest) face
        x, y, w, h = faces[0]
        face_region = gray[y:y+h, x:x+w]
        
        # Resize to standard size (100x100)
        face_resized = cv2.resize(face_region, (100, 100))
        
        print(f"Extracted face region: {face_resized.shape}")
        
        # Create a dummy color image from grayscale for recognition
        face_color = cv2.cvtColor(face_resized, cv2.COLOR_GRAY2BGR)
        
        # Try to recognize this face
        result = enhanced_face_recognizer.recognize_face_from_image(face_color)
        
        if result:
            student_id = result['student_id']
            confidence = result['confidence'] / 100.0  # Convert back to decimal
            print(f"\n🎯 RECOGNITION RESULT:")
            print(f"   Student ID: {student_id}")
            print(f"   Confidence: {confidence:.2%}")
            
            if confidence > 0.7:  # 70% threshold
                print(f"   ✅ MATCH FOUND - High confidence")
            elif confidence > 0.5:  # 50% threshold  
                print(f"   ⚠️  POSSIBLE MATCH - Medium confidence")
            else:
                print(f"   ❌ NO MATCH - Low confidence")
                
        else:
            print("❌ No recognition result")
            
        return result
        
    except Exception as e:
        print(f"Error processing photo: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_uploaded_photo_from_base64(base64_data, filename="uploaded_photo.jpg"):
    """Save a base64 encoded photo to disk"""
    import base64
    
    try:
        # Remove data URL prefix if present
        if base64_data.startswith('data:'):
            base64_data = base64_data.split(',')[1]
            
        # Decode and save
        img_data = base64.b64decode(base64_data)
        with open(filename, 'wb') as f:
            f.write(img_data)
        print(f"Photo saved as: {filename}")
        return filename
    except Exception as e:
        print(f"Error saving photo: {e}")
        return None

if __name__ == "__main__":
    # Test with a sample photo if provided
    if len(sys.argv) > 1:
        photo_path = sys.argv[1]
        test_uploaded_photo(photo_path)
    else:
        print("Usage: python test_user_photo.py <photo_path>")
        print("Or run interactively to upload a photo")
        
        # For now, test with an existing face
        print("\nTesting with existing student photo...")
        test_photo_path = "faces/student_1.jpg"
        if os.path.exists(test_photo_path):
            test_uploaded_photo(test_photo_path)