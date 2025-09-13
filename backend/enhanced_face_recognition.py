"""
Enhanced facial recognition module that works with Google Drive URLs using OpenCV template matching
"""
import cv2
import numpy as np
import os
import json
import requests
from pathlib import Path
from PIL import Image
from io import BytesIO
import logging
from typing import List, Dict, Optional, Tuple

class EnhancedFaceRecognition:
    def __init__(self, faces_dir: str = "faces"):
        self.faces_dir = Path(faces_dir)
        self.faces_dir.mkdir(exist_ok=True)
        self.face_data_file = self.faces_dir / "face_data.json"
        self.face_data = {}
        
        # Initialize OpenCV face detector
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        self.load_face_data()
        
    def load_face_data(self):
        """Load face data from file"""
        if self.face_data_file.exists():
            try:
                with open(self.face_data_file, 'r') as f:
                    self.face_data = json.load(f)
            except Exception as e:
                logging.error(f"Error loading face data: {e}")
                self.face_data = {}
    
    def save_face_data(self):
        """Save face data to file"""
        try:
            with open(self.face_data_file, 'w') as f:
                json.dump(self.face_data, f)
        except Exception as e:
            logging.error(f"Error saving face data: {e}")
    
    def download_image_from_url(self, url: str) -> Optional[np.ndarray]:
        """Download image from URL and convert to OpenCV format"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # Convert to PIL Image first
                image = Image.open(BytesIO(response.content))
                # Convert to RGB if needed
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                # Convert to OpenCV format (BGR)
                opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                return opencv_image
            return None
        except Exception as e:
            logging.error(f"Error downloading image from {url}: {e}")
            return None
    
    def extract_and_save_face(self, photo_url: str, student_id: str) -> bool:
        """Extract face from Google Drive URL and save it"""
        try:
            # Download image
            image = self.download_image_from_url(photo_url)
            if image is None:
                return False
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) == 0:
                logging.warning(f"No faces found in image for student {student_id}")
                return False
            
            # Take the largest face
            face = max(faces, key=lambda x: x[2] * x[3])
            x, y, w, h = face
            
            # Extract face region with some padding
            padding = int(min(w, h) * 0.1)
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(gray.shape[1] - x, w + 2*padding)
            h = min(gray.shape[0] - y, h + 2*padding)
            
            face_img = gray[y:y+h, x:x+w]
            
            # Resize to standard size
            face_img = cv2.resize(face_img, (200, 200))
            
            # Apply histogram equalization for better matching
            face_img = cv2.equalizeHist(face_img)
            
            # Save face image
            face_path = self.faces_dir / f"student_{student_id}.jpg"
            cv2.imwrite(str(face_path), face_img)
            
            # Store face data
            self.face_data[student_id] = {
                'face_path': str(face_path),
                'photo_url': photo_url
            }
            self.save_face_data()
            
            logging.info(f"Successfully extracted and saved face for student {student_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error extracting face for student {student_id}: {e}")
            return False
    
    def extract_face_features(self, face_img: np.ndarray) -> np.ndarray:
        """Extract robust features from face image"""
        try:
            # Resize to standard size
            face_img = cv2.resize(face_img, (100, 100))
            
            # Apply multiple preprocessing steps
            # 1. Histogram equalization
            face_img = cv2.equalizeHist(face_img)
            
            # 2. Gaussian blur to reduce noise
            face_img = cv2.GaussianBlur(face_img, (3, 3), 0)
            
            # 3. Normalize pixel values
            face_img = cv2.normalize(face_img, None, 0, 255, cv2.NORM_MINMAX)
            
            # 4. Extract LBP (Local Binary Patterns) features
            # This is more robust to lighting changes
            radius = 1
            n_points = 8 * radius
            lbp = self.calculate_lbp(face_img, radius, n_points)
            
            # Calculate histogram of LBP
            hist, _ = np.histogram(lbp.ravel(), bins=256, range=(0, 256))
            
            # Normalize histogram
            hist = hist.astype(float)
            hist /= (hist.sum() + 1e-7)
            
            return hist
            
        except Exception as e:
            logging.error(f"Error extracting face features: {e}")
            return None
    
    def calculate_lbp(self, image: np.ndarray, radius: int, n_points: int) -> np.ndarray:
        """Calculate Local Binary Pattern"""
        try:
            rows, cols = image.shape
            lbp = np.zeros((rows, cols), dtype=np.uint8)
            
            for i in range(radius, rows - radius):
                for j in range(radius, cols - radius):
                    center = image[i, j]
                    pattern = 0
                    
                    for p in range(n_points):
                        # Calculate neighbor coordinates
                        angle = 2 * np.pi * p / n_points
                        x = int(i + radius * np.cos(angle))
                        y = int(j + radius * np.sin(angle))
                        
                        # Compare with center
                        if x >= 0 and x < rows and y >= 0 and y < cols:
                            if image[x, y] >= center:
                                pattern |= (1 << p)
                    
                    lbp[i, j] = pattern
            
            return lbp
            
        except Exception as e:
            logging.error(f"Error calculating LBP: {e}")
            return image
        """Calculate similarity between two face images using template matching"""
        try:
            # Ensure both images are the same size
            face1 = cv2.resize(face1, (200, 200))
            face2 = cv2.resize(face2, (200, 200))
            
            # Apply histogram equalization
            face1 = cv2.equalizeHist(face1)
            face2 = cv2.equalizeHist(face2)
            
            # Use template matching
            result = cv2.matchTemplate(face1, face2, cv2.TM_CCOEFF_NORMED)
            
            # Get maximum correlation value
            _, max_val, _, _ = cv2.minMaxLoc(result)
            
            return max_val
            
        except Exception as e:
            logging.error(f"Error calculating face similarity: {e}")
            return 0.0
    
    def recognize_face_from_image(self, image: np.ndarray, threshold: float = 0.3) -> Optional[Dict]:
        """Recognize face from image using template matching"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) == 0:
                return None
            
            # Take the largest face
            face = max(faces, key=lambda x: x[2] * x[3])
            x, y, w, h = face
            
            # Extract face region with padding
            padding = int(min(w, h) * 0.1)
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(gray.shape[1] - x, w + 2*padding)
            h = min(gray.shape[0] - y, h + 2*padding)
            
            uploaded_face = gray[y:y+h, x:x+w]
            uploaded_face = cv2.resize(uploaded_face, (200, 200))
            uploaded_face = cv2.equalizeHist(uploaded_face)
            
            # Compare with all stored faces
            best_match = None
            best_similarity = 0.0
            
            for student_id, data in self.face_data.items():
                face_path = data['face_path']
                if os.path.exists(face_path):
                    stored_face = cv2.imread(face_path, cv2.IMREAD_GRAYSCALE)
                    if stored_face is not None:
                        similarity = self.calculate_face_similarity(uploaded_face, stored_face)
                        
                        if similarity > best_similarity and similarity > threshold:
                            best_similarity = similarity
                            best_match = {
                                'student_id': student_id,
                                'confidence': similarity * 100,  # Convert to percentage
                                'similarity': similarity
                            }
            
            return best_match
            
        except Exception as e:
            logging.error(f"Error recognizing face: {e}")
            return None
    
    def recognize_face_from_url(self, photo_url: str, threshold: float = 0.3) -> Optional[Dict]:
        """Recognize face from URL"""
        image = self.download_image_from_url(photo_url)
        if image is None:
            return None
        return self.recognize_face_from_image(image, threshold)
    
    def process_all_students_from_db(self, students_data: List[Dict]) -> Dict:
        """Process all students' photos from database"""
        results = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for student in students_data:
            student_id = str(student['student_id'])
            photo_url = student.get('photo_url')
            name = student.get('name', 'Unknown')
            
            if not photo_url:
                results['errors'].append(f"No photo URL for student {name} (ID: {student_id})")
                results['failed'] += 1
                continue
            
            results['processed'] += 1
            
            if self.extract_and_save_face(photo_url, student_id):
                results['successful'] += 1
                logging.info(f"✅ Processed {name} (ID: {student_id})")
            else:
                results['failed'] += 1
                results['errors'].append(f"Failed to process {name} (ID: {student_id})")
                logging.error(f"❌ Failed to process {name} (ID: {student_id})")
        
        return results
    
    def get_statistics(self) -> Dict:
        """Get statistics about stored face data"""
        total_students = len(self.face_data)
        valid_faces = sum(1 for data in self.face_data.values() 
                         if os.path.exists(data['face_path']))
        
        return {
            'total_students': total_students,
            'valid_face_files': valid_faces,
            'students_with_data': list(self.face_data.keys())
        }

# Create global instance
enhanced_face_recognizer = EnhancedFaceRecognition()