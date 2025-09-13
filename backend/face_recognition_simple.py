"""
Simple facial recognition module using OpenCV
"""
import cv2
import numpy as np
import os
import json
from pathlib import Path
import logging

class SimpleFaceRecognition:
    def __init__(self, faces_dir: str = "faces"):
        self.faces_dir = Path(faces_dir)
        self.faces_dir.mkdir(exist_ok=True)
        
        # Initialize face detector
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
    def extract_face_from_image(self, image_path: str) -> bool:
        """Extract and save face from image"""
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                return False
                
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) == 0:
                return False
                
            # Take the largest face
            face = max(faces, key=lambda x: x[2] * x[3])
            x, y, w, h = face
            
            # Extract face region
            face_img = img[y:y+h, x:x+w]
            
            # Resize to standard size
            face_img = cv2.resize(face_img, (150, 150))
            
            # Save face
            student_id = Path(image_path).stem
            face_path = self.faces_dir / f"{student_id}_face.jpg"
            cv2.imwrite(str(face_path), face_img)
            
            return True
            
        except Exception as e:
            logging.error(f"Error extracting face: {e}")
            return False
    
    def compare_faces_simple(self, image1_path: str, image2_path: str) -> float:
        """Simple face comparison using template matching"""
        try:
            img1 = cv2.imread(image1_path, cv2.IMREAD_GRAYSCALE)
            img2 = cv2.imread(image2_path, cv2.IMREAD_GRAYSCALE)
            
            if img1 is None or img2 is None:
                return 0.0
                
            # Resize both images to same size
            img1 = cv2.resize(img1, (150, 150))
            img2 = cv2.resize(img2, (150, 150))
            
            # Template matching
            result = cv2.matchTemplate(img1, img2, cv2.TM_CCOEFF_NORMED)
            confidence = result[0][0]
            
            return max(0.0, confidence)
            
        except Exception as e:
            logging.error(f"Error comparing faces: {e}")
            return 0.0
    
    def recognize_student(self, input_image_path: str, student_id: str) -> float:
        """Recognize student by comparing with stored face"""
        try:
            stored_face_path = self.faces_dir / f"{student_id}_face.jpg"
            
            if not stored_face_path.exists():
                return 0.0
                
            # Extract face from input image first
            temp_face_path = self.faces_dir / "temp_face.jpg"
            
            # Read and process input image
            img = cv2.imread(input_image_path)
            if img is None:
                return 0.0
                
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) == 0:
                return 0.0
                
            # Take the largest face
            face = max(faces, key=lambda x: x[2] * x[3])
            x, y, w, h = face
            
            # Extract and save temp face
            face_img = img[y:y+h, x:x+w]
            face_img = cv2.resize(face_img, (150, 150))
            cv2.imwrite(str(temp_face_path), face_img)
            
            # Compare faces
            confidence = self.compare_faces_simple(str(stored_face_path), str(temp_face_path))
            
            # Clean up temp file
            if temp_face_path.exists():
                temp_face_path.unlink()
                
            return confidence
            
        except Exception as e:
            logging.error(f"Error recognizing student: {e}")
            return 0.0
    
    def get_all_stored_faces(self) -> list:
        """Get list of all stored face files"""
        try:
            face_files = list(self.faces_dir.glob("*_face.jpg"))
            return [f.stem.replace("_face", "") for f in face_files]
        except:
            return []

# Initialize global face recognition instance
face_recognizer = SimpleFaceRecognition()
