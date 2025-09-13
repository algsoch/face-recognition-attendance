#/usr/bin/env python3
"""
Professional Face Recognition System
Using proper face recognition methodology without external dependencies
"""

import cv2
import numpy as np
import logging
import json
import os
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import requests
from PIL import Image
from io import BytesIO
import sqlite3

class ProfessionalFaceRecognition:
    """Professional face recognition system with proper methodology"""
    
    def __init__(self, faces_dir: str = "professional_faces"):
        self.faces_dir = Path(faces_dir)
        self.faces_dir.mkdir(exist_ok=True)
        
        # Professional recognition parameters
        self.FACE_RECOGNITION_TOLERANCE = 0.6  # Standard face recognition tolerance
        self.HIGH_CONFIDENCE_THRESHOLD = 0.4   # Lower is better (distance-based)
        self.MEDIUM_CONFIDENCE_THRESHOLD = 0.5
        self.REJECT_THRESHOLD = 0.8  # Above this distance = reject
        
        # Advanced face detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        
        # Storage
        self.face_encodings = {}
        self.face_data = {}
        
        # File paths
        self.encodings_file = Path("professional_face_encodings.json")
        self.face_data_file = Path("professional_face_data.json")
        
        # Load existing data
        self.load_face_data()
        self.load_face_encodings()
        
        logging.basicConfig(level=logging.INFO)
        logging.info("✅ Professional Face Recognition System Initialized")
    
    def detect_faces_advanced(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Advanced face detection using multiple cascades"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Primary face detection
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5, 
                minSize=(50, 50),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            # If no frontal faces, try profile detection
            if len(faces) == 0:
                faces = self.profile_cascade.detectMultiScale(
                    gray, 
                    scaleFactor=1.1, 
                    minNeighbors=5, 
                    minSize=(50, 50)
                )
            
            return [(x, y, w, h) for x, y, w, h in faces]
            
        except Exception as e:
            logging.error(f"Error in face detection: {e}")
            return []
    
    def extract_face_encoding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Extract professional face encoding using advanced computer vision"""
        try:
            faces = self.detect_faces_advanced(image)
            if len(faces) == 0:
                return None
            
            # Use the largest face
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            
            # Extract face with proper padding
            padding = max(10, min(w, h) // 10)
            face_region = image[
                max(0, y-padding):min(image.shape[0], y+h+padding),
                max(0, x-padding):min(image.shape[1], x+w+padding)
            ]
            
            if face_region.size == 0:
                return None
            
            # Convert to grayscale if needed
            if len(face_region.shape) == 3:
                face_gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            else:
                face_gray = face_region
            
            # Normalize to standard size (128x128 like real face recognition)
            face_normalized = cv2.resize(face_gray, (128, 128))
            
            # Advanced preprocessing for robust recognition
            face_normalized = cv2.equalizeHist(face_normalized)
            face_normalized = cv2.GaussianBlur(face_normalized, (3, 3), 0)
            
            # Extract comprehensive facial features
            encoding = self.extract_comprehensive_features(face_normalized)
            return encoding
            
        except Exception as e:
            logging.error(f"Error extracting face encoding: {e}")
            return None
    
    def extract_comprehensive_features(self, face_image: np.ndarray) -> np.ndarray:
        """Extract comprehensive facial features using multiple techniques"""
        try:
            features = []
            logging.info("--- Starting Comprehensive Feature Extraction ---")

            # 1. Statistical features from different face regions
            h, w = face_image.shape
            regions = [
                face_image[0:h//3, 0:w//3], face_image[0:h//3, w//3:2*w//3], face_image[0:h//3, 2*w//3:w],
                face_image[h//3:2*h//3, 0:w//3], face_image[h//3:2*h//3, w//3:2*w//3], face_image[h//3:2*h//3, 2*w//3:w],
                face_image[2*h//3:h, 0:w//3], face_image[2*h//3:h, w//3:2*w//3], face_image[2*h//3:h, 2*w//3:w],
            ]
            
            stat_features = []
            for i, region in enumerate(regions):
                if region.size > 0:
                    stat_features.extend([
                        np.mean(region), np.std(region), np.median(region),
                        np.percentile(region, 25), np.percentile(region, 75)
                    ])
            features.extend(stat_features)
            logging.info(f"Statistical features extracted. Length: {len(stat_features)}. Contains NaN/Inf: {np.any(np.isnan(stat_features)) or np.any(np.isinf(stat_features))}")

            # 2. Local Binary Pattern (LBP) features
            lbp_features = self.calculate_robust_lbp(face_image)
            features.extend(lbp_features)
            logging.info(f"LBP features extracted. Length: {len(lbp_features)}. Contains NaN/Inf: {np.any(np.isnan(lbp_features)) or np.any(np.isinf(lbp_features))}")

            # 3. Gradient features (edges and contours)
            gradient_features = self.calculate_gradient_features(face_image)
            features.extend(gradient_features)
            logging.info(f"Gradient features extracted. Length: {len(gradient_features)}. Contains NaN/Inf: {np.any(np.isnan(gradient_features)) or np.any(np.isinf(gradient_features))}")

            # 4. Histogram features
            hist_features = self.calculate_histogram_features(face_image)
            features.extend(hist_features)
            logging.info(f"Histogram features extracted. Length: {len(hist_features)}. Contains NaN/Inf: {np.any(np.isnan(hist_features)) or np.any(np.isinf(hist_features))}")

            # 5. Texture features
            texture_features = self.calculate_texture_features(face_image)
            features.extend(texture_features)
            logging.info(f"Texture features extracted. Length: {len(texture_features)}. Contains NaN/Inf: {np.any(np.isnan(texture_features)) or np.any(np.isinf(texture_features))}")
            
            final_encoding = np.array(features, dtype=np.float64)
            logging.info(f"--- Finished Comprehensive Feature Extraction --- Total length: {len(final_encoding)}")
            if np.any(np.isnan(final_encoding)) or np.any(np.isinf(final_encoding)):
                logging.error("CRITICAL: Final encoding contains NaN or Inf values.")
            
            return final_encoding
            
        except Exception as e:
            logging.error(f"Error extracting comprehensive features: {e}")
            return np.array([])
    
    def calculate_robust_lbp(self, image: np.ndarray) -> List[float]:
        """Calculate robust Local Binary Pattern features"""
        try:
            features = []
            
            # Multiple LBP configurations for robustness
            configs = [(1, 8), (2, 16), (3, 24)]
            
            for radius, n_points in configs:
                lbp = self.calculate_lbp_pattern(image, radius, n_points)
                if lbp is not None:
                    hist, _ = np.histogram(lbp.ravel(), bins=n_points + 2, range=(0, n_points + 2))
                    hist = hist.astype(float)
                    hist /= (hist.sum() + 1e-7)
                    features.extend(hist)
            
            return features
            
        except Exception as e:
            logging.error(f"Error calculating LBP: {e}")
            return []
    
    def calculate_lbp_pattern(self, image: np.ndarray, radius: int, n_points: int) -> Optional[np.ndarray]:
        """Calculate LBP pattern with error handling"""
        try:
            rows, cols = image.shape
            # Use uint32 to avoid overflow, then convert safely
            lbp = np.zeros((rows, cols), dtype=np.uint32)
            
            for i in range(radius, rows - radius):
                for j in range(radius, cols - radius):
                    center = int(image[i, j])
                    pattern = 0
                    
                    for p in range(n_points):
                        angle = 2.0 * np.pi * p / n_points
                        x = int(round(i + radius * np.cos(angle)))
                        y = int(round(j + radius * np.sin(angle)))
                        
                        # Bounds checking
                        x = max(0, min(rows-1, x))
                        y = max(0, min(cols-1, y))
                        
                        if int(image[x, y]) >= center:
                            pattern |= (1 << p)
                    
                    # Safely assign pattern with bounds checking
                    lbp[i, j] = min(pattern, 255)
            
            # Convert back to uint8 safely
            return lbp.astype(np.uint8)
            
        except Exception as e:
            logging.error(f"Error in LBP calculation: {e}")
            return None
    
    def calculate_gradient_features(self, image: np.ndarray) -> List[float]:
        """Calculate gradient-based features"""
        try:
            # Sobel gradients
            grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
            
            magnitude = np.sqrt(grad_x**2 + grad_y**2)
            direction = np.arctan2(grad_y, grad_x)
            
            # Histogram of gradients
            mag_hist, _ = np.histogram(magnitude.ravel(), bins=32, range=(0, 255))
            dir_hist, _ = np.histogram(direction.ravel(), bins=32, range=(-np.pi, np.pi))
            
            # Normalize
            mag_hist = mag_hist.astype(float) / (mag_hist.sum() + 1e-7)
            dir_hist = dir_hist.astype(float) / (dir_hist.sum() + 1e-7)
            
            features = list(mag_hist) + list(dir_hist)
            
            # Add gradient statistics
            features.extend([
                np.mean(magnitude),
                np.std(magnitude),
                np.mean(np.abs(direction)),
                np.std(direction)
            ])
            
            return features
            
        except Exception as e:
            logging.error(f"Error calculating gradient features: {e}")
            return []
    
    def calculate_histogram_features(self, image: np.ndarray) -> List[float]:
        """Calculate histogram-based features"""
        try:
            # Multiple histogram bins for different granularity
            features = []
            
            for bins in [16, 32, 64]:
                hist, _ = np.histogram(image.ravel(), bins=bins, range=(0, 256))
                hist = hist.astype(float) / (hist.sum() + 1e-7)
                features.extend(hist)
            
            return features
            
        except Exception as e:
            logging.error(f"Error calculating histogram features: {e}")
            return []
    
    def calculate_texture_features(self, image: np.ndarray) -> List[float]:
        """Calculate texture-based features"""
        try:
            features = []
            
            # Variance in different directions
            for angle in [0, 45, 90, 135]:
                if angle == 0:
                    kernel = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
                elif angle == 45:
                    kernel = np.array([[-2, -1, 0], [-1, 0, 1], [0, 1, 2]])
                elif angle == 90:
                    kernel = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])
                else:  # 135
                    kernel = np.array([[0, -1, -2], [1, 0, -1], [2, 1, 0]])
                
                filtered = cv2.filter2D(image, cv2.CV_64F, kernel)
                filtered_array = np.array(filtered)
                features.append(float(np.var(filtered_array)))
            
            return features
            
        except Exception as e:
            logging.error(f"Error calculating texture features: {e}")
            return []
    
    def calculate_face_distance(self, encoding1: np.ndarray, encoding2: np.ndarray) -> float:
        """Calculate distance between face encodings (lower = more similar)"""
        try:
            if len(encoding1) == 0 or len(encoding2) == 0:
                logging.warning("Empty encoding detected, returning maximum distance")
                return 1.0
            
            # Check for NaN or infinite values
            if np.any(np.isnan(encoding1)) or np.any(np.isnan(encoding2)):
                logging.warning("NaN values detected in encodings")
                return 1.0
                
            if np.any(np.isinf(encoding1)) or np.any(np.isinf(encoding2)):
                logging.warning("Infinite values detected in encodings")
                return 1.0
            
            # Calculate norms safely
            norm1 = np.linalg.norm(encoding1)
            norm2 = np.linalg.norm(encoding2)
            
            if norm1 == 0 or norm2 == 0:
                logging.warning("Zero norm detected in encodings")
                return 1.0
            
            # Normalize encodings
            encoding1_norm = encoding1 / norm1
            encoding2_norm = encoding2 / norm2
            
            # Use euclidean distance (standard in face recognition)
            distance = float(np.linalg.norm(encoding1_norm - encoding2_norm))
            
            # Ensure distance is finite and in reasonable range
            if not np.isfinite(distance):
                logging.warning("Non-finite distance calculated")
                return 1.0
                
            return min(distance, 2.0)  # Cap at 2.0 for normalized vectors
            
        except Exception as e:
            logging.error(f"Error calculating face distance: {e}")
            return 1.0
    
    def download_image_from_url(self, url: str) -> Optional[np.ndarray]:
        """Download image from URL"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            return None
        except Exception as e:
            logging.error(f"Error downloading image: {e}")
            return None
    
    def extract_and_save_face(self, photo_url: str, student_id: str) -> bool:
        """Extract and save face encoding from photo URL"""
        try:
            # Download image
            image = self.download_image_from_url(photo_url)
            if image is None:
                logging.error(f"Failed to download image for student {student_id}")
                return False
            
            # Extract face encoding
            encoding = self.extract_face_encoding(image)
            if encoding is None or len(encoding) == 0:
                logging.error(f"Failed to extract face encoding for student {student_id}")
                return False
            
            # Save face image
            face_path = self.faces_dir / f"professional_student_{student_id}.jpg"
            cv2.imwrite(str(face_path), image)
            
            # Store encoding and data
            self.face_encodings[student_id] = encoding
            self.face_data[student_id] = {
                'face_path': str(face_path),
                'photo_url': photo_url,
                'encoding_length': len(encoding)
            }
            
            # Save to files
            self.save_face_encodings()
            self.save_face_data()
            
            logging.info(f"✅ Professional encoding extracted for student {student_id} (length: {len(encoding)})")
            return True
            
        except Exception as e:
            logging.error(f"Error extracting face for student {student_id}: {e}")
            return False
    
    def recognize_face_from_image(self, image: np.ndarray) -> Dict:
        """Recognize face using professional methodology"""
        try:
            # Extract encoding from uploaded image
            uploaded_encoding = self.extract_face_encoding(image)
            if uploaded_encoding is None or len(uploaded_encoding) == 0:
                return {
                    'match_found': False,
                    'reason': 'Could not extract face features from uploaded image',
                    'confidence': 0.0,
                    'all_distances': {}
                }
            
            # Compare with all stored encodings
            distances = {}
            best_match = None
            best_distance = float('inf')
            
            for student_id, stored_encoding in self.face_encodings.items():
                distance = self.calculate_face_distance(uploaded_encoding, stored_encoding)
                distances[student_id] = distance
                
                if distance < best_distance:
                    best_distance = distance
                    best_match = student_id
            
            # Get student details
            student_details = self.get_student_details(best_match) if best_match else None
            
            # Professional decision making (distance-based)
            if best_distance <= self.FACE_RECOGNITION_TOLERANCE:
                if best_distance <= self.HIGH_CONFIDENCE_THRESHOLD:
                    confidence_level = "HIGH"
                elif best_distance <= self.MEDIUM_CONFIDENCE_THRESHOLD:
                    confidence_level = "MEDIUM"
                else:
                    confidence_level = "LOW"
                
                # Convert distance to confidence percentage (inverse relationship)
                confidence_percentage = max(0, (1 - best_distance) * 100)
                
                return {
                    'match_found': True,
                    'student_id': best_match,
                    'confidence': confidence_percentage,
                    'confidence_level': confidence_level,
                    'distance': best_distance,
                    'all_distances': distances,
                    'student_details': student_details,
                    'encoding_length': len(uploaded_encoding),
                    'recognition_method': 'professional_face_recognition'
                }
            else:
                return {
                    'match_found': False,
                    'reason': f'Best distance {best_distance:.3f} above tolerance {self.FACE_RECOGNITION_TOLERANCE}',
                    'confidence': max(0, (1 - best_distance) * 100),
                    'best_rejected_match': {
                        'student_id': best_match,
                        'distance': best_distance,
                        'student_details': student_details
                    } if best_match else None,
                    'all_distances': distances
                }
                
        except Exception as e:
            logging.error(f"Error recognizing face: {e}")
            return {
                'match_found': False,
                'reason': f'Error during recognition: {str(e)}',
                'confidence': 0.0,
                'all_distances': {}
            }
    
    def get_student_details(self, student_id: str) -> Optional[Dict]:
        """Get student details from database"""
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT student_id, roll_number, name, class_name, section, branch, 
                       photo_url, is_active, created_at, updated_at
                FROM students 
                WHERE student_id = ?
            ''', (student_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'student_id': result[0],
                    'roll_number': result[1],
                    'name': result[2],
                    'class_name': result[3],
                    'section': result[4],
                    'branch': result[5],
                    'photo_url': result[6],
                    'is_active': result[7],
                    'created_at': result[8],
                    'updated_at': result[9]
                }
            
            return None
            
        except Exception as e:
            logging.error(f"Error getting student details: {e}")
            return None
    
    def load_face_encodings(self):
        """Load face encodings from file"""
        if self.encodings_file.exists():
            try:
                with open(self.encodings_file, 'r') as f:
                    data = json.load(f)
                    self.face_encodings = {k: np.array(v) for k, v in data.items()}
            except Exception as e:
                logging.error(f"Error loading face encodings: {e}")
                self.face_encodings = {}
    
    def save_face_encodings(self):
        """Save face encodings to file"""
        try:
            data = {k: v.tolist() for k, v in self.face_encodings.items()}
            with open(self.encodings_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logging.error(f"Error saving face encodings: {e}")
    
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
                json.dump(self.face_data, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving face data: {e}")

# Initialize professional face recognizer
professional_face_recognizer = ProfessionalFaceRecognition()