"""
Enhanced facial recognition module that works with Google Drive URLs using robust feature matching
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
        self.features_file = self.faces_dir / "face_features.json"
        self.face_data = {}
        self.face_features = {}
        
        # Initialize OpenCV face detector
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        self.load_face_data()
        self.load_face_features()
        
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
    
    def load_face_features(self):
        """Load face features from file"""
        if self.features_file.exists():
            try:
                with open(self.features_file, 'r') as f:
                    data = json.load(f)
                    # Convert back to numpy arrays
                    self.face_features = {k: np.array(v) for k, v in data.items()}
            except Exception as e:
                logging.error(f"Error loading face features: {e}")
                self.face_features = {}
    
    def save_face_features(self):
        """Save face features to file"""
        try:
            # Convert numpy arrays to lists for JSON serialization
            data = {k: v.tolist() for k, v in self.face_features.items()}
            with open(self.features_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logging.error(f"Error saving face features: {e}")
    
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
            
            # 4. Extract multiple feature types
            features = []
            
            # LBP histogram
            lbp = self.calculate_lbp(face_img, 1, 8)
            lbp_hist, _ = np.histogram(lbp.ravel(), bins=256, range=(0, 256))
            lbp_hist = lbp_hist.astype(float)
            lbp_hist /= (lbp_hist.sum() + 1e-7)
            features.extend(lbp_hist)
            
            # Gradient features
            grad_x = cv2.Sobel(face_img, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(face_img, cv2.CV_64F, 0, 1, ksize=3)
            grad_mag = np.sqrt(grad_x**2 + grad_y**2)
            grad_hist, _ = np.histogram(grad_mag.ravel(), bins=50, range=(0, 255))
            grad_hist = grad_hist.astype(float)
            grad_hist /= (grad_hist.sum() + 1e-7)
            features.extend(grad_hist)
            
            # Intensity histogram
            intensity_hist, _ = np.histogram(face_img.ravel(), bins=50, range=(0, 255))
            intensity_hist = intensity_hist.astype(float)
            intensity_hist /= (intensity_hist.sum() + 1e-7)
            features.extend(intensity_hist)
            
            return np.array(features)
            
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
    
    def calculate_feature_similarity(self, features1: np.ndarray, features2: np.ndarray) -> float:
        """Calculate similarity between feature vectors"""
        try:
            # Cosine similarity
            dot_product = np.dot(features1, features2)
            norms = np.linalg.norm(features1) * np.linalg.norm(features2)
            if norms == 0:
                return 0.0
            cosine_sim = dot_product / norms
            
            # Euclidean distance (converted to similarity)
            euclidean_dist = np.linalg.norm(features1 - features2)
            euclidean_sim = 1.0 / (1.0 + euclidean_dist)
            
            # Correlation coefficient
            correlation = np.corrcoef(features1, features2)[0, 1]
            if np.isnan(correlation):
                correlation = 0.0
            
            # Combined similarity
            combined = (0.4 * cosine_sim + 0.3 * euclidean_sim + 0.3 * correlation)
            return max(0.0, min(1.0, combined))
            
        except Exception as e:
            logging.error(f"Error calculating feature similarity: {e}")
            return 0.0
    
    def extract_and_save_face(self, photo_url: str, student_id: str) -> bool:
        """Extract face from Google Drive URL and save features"""
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
            
            # Extract face region with padding
            padding = int(min(w, h) * 0.1)
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(gray.shape[1] - x, w + 2*padding)
            h = min(gray.shape[0] - y, h + 2*padding)
            
            face_img = gray[y:y+h, x:x+w]
            
            # Extract features
            features = self.extract_face_features(face_img)
            if features is None:
                return False
            
            # Save face image for debugging
            face_img_resized = cv2.resize(face_img, (100, 100))
            face_path = self.faces_dir / f"student_{student_id}.jpg"
            cv2.imwrite(str(face_path), face_img_resized)
            
            # Store face data and features
            self.face_data[student_id] = {
                'face_path': str(face_path),
                'photo_url': photo_url
            }
            self.face_features[student_id] = features
            
            self.save_face_data()
            self.save_face_features()
            
            logging.info(f"Successfully extracted features for student {student_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error extracting face for student {student_id}: {e}")
            return False
    
    def recognize_face_from_image(self, image: np.ndarray, threshold: float = 0.5) -> Optional[Dict]:
        """Recognize face from image using feature matching"""
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
            
            # Extract features from uploaded face
            uploaded_features = self.extract_face_features(uploaded_face)
            if uploaded_features is None:
                return None
            
            # Compare with all stored features
            best_match = None
            best_similarity = 0.0
            
            for student_id, stored_features in self.face_features.items():
                similarity = self.calculate_feature_similarity(uploaded_features, stored_features)
                
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
    
    def recognize_face_from_url(self, photo_url: str, threshold: float = 0.5) -> Optional[Dict]:
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
        total_features = len(self.face_features)
        
        return {
            'total_students': total_students,
            'valid_face_files': valid_faces,
            'total_features': total_features,
            'students_with_data': list(self.face_data.keys()),
            'students_with_features': list(self.face_features.keys())
        }

# Create global instance
enhanced_face_recognizer = EnhancedFaceRecognition()