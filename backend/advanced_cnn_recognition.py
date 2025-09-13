#!/usr/bin/env python3
"""
Advanced CNN Face Recognition System using DeepFace
This system uses state-of-the-art deep learning models for accurate face recognition
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

# Import for fallback CNN implementation
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    print("⚠️ DeepFace not available, using fallback CNN implementation")

class AdvancedCNNFaceRecognition:
    """Advanced CNN-based face recognition with multiple models"""
    
    def __init__(self, faces_dir: str = "cnn_faces"):
        self.faces_dir = Path(faces_dir)
        self.faces_dir.mkdir(exist_ok=True)
        
        # CNN Model settings
        self.model_name = "VGG-Face"  # Options: VGG-Face, Facenet, OpenFace, DeepFace, DeepID, ArcFace
        self.detector_backend = "opencv"  # Options: opencv, ssd, dlib, mtcnn, retinaface
        self.distance_metric = "cosine"  # Options: cosine, euclidean, euclidean_l2
        
        # Recognition thresholds (more permissive for real-world use)
        self.VERIFICATION_THRESHOLD = 0.65  # 65% similarity for verification
        self.HIGH_CONFIDENCE_THRESHOLD = 0.75  # 75% for high confidence
        self.REJECT_THRESHOLD = 0.45  # Below 45% is rejected
        
        # Storage
        self.face_encodings = {}
        self.face_data = {}
        
        # File paths
        self.encodings_file = Path("cnn_face_encodings.json")
        self.face_data_file = Path("cnn_face_data.json")
        
        # Load existing data
        self.load_face_data()
        self.load_face_encodings()
        
        logging.basicConfig(level=logging.INFO)
        
        if DEEPFACE_AVAILABLE:
            logging.info(f"✅ DeepFace CNN System Initialized with {self.model_name}")
        else:
            logging.info("⚠️ Using fallback CNN implementation")
    
    def extract_cnn_features(self, image_path: str) -> Optional[np.ndarray]:
        """Extract CNN features using DeepFace or fallback method"""
        try:
            if DEEPFACE_AVAILABLE:
                # Use DeepFace for advanced CNN feature extraction
                try:
                    # Generate face embedding using CNN model
                    embedding = DeepFace.represent(
                        img_path=image_path,
                        model_name=self.model_name,
                        detector_backend=self.detector_backend,
                        enforce_detection=False  # Don't fail if face detection is uncertain
                    )
                    
                    # DeepFace returns a list of embeddings
                    if embedding and len(embedding) > 0:
                        return np.array(embedding[0]['embedding'])
                    else:
                        return None
                        
                except Exception as e:
                    logging.warning(f"DeepFace extraction failed, using fallback: {e}")
                    return self.extract_fallback_features(image_path)
            else:
                return self.extract_fallback_features(image_path)
                
        except Exception as e:
            logging.error(f"Error extracting CNN features: {e}")
            return None
    
    def extract_fallback_features(self, image_path: str) -> Optional[np.ndarray]:
        """Fallback CNN-inspired feature extraction using OpenCV"""
        try:
            # Load image
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                return None
            
            # Resize to standard size
            image = cv2.resize(image, (224, 224))  # CNN input size
            
            # Advanced preprocessing similar to CNN
            image = cv2.equalizeHist(image)
            image = cv2.GaussianBlur(image, (3, 3), 0)
            image = image.astype(np.float32) / 255.0
            
            # Multi-scale feature extraction (CNN-inspired)
            features = []
            
            # 1. Local Binary Patterns (multiple scales)
            for radius in [1, 2, 3, 4]:
                lbp = self.calculate_lbp(image, radius, 8)
                lbp_hist, _ = np.histogram(lbp.ravel(), bins=256, range=(0, 256))
                lbp_hist = lbp_hist.astype(float)
                lbp_hist /= (lbp_hist.sum() + 1e-7)
                features.extend(lbp_hist)
            
            # 2. Histogram of Oriented Gradients (HOG)
            grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
            magnitude = np.sqrt(grad_x**2 + grad_y**2)
            direction = np.arctan2(grad_y, grad_x)
            
            # HOG features
            mag_hist, _ = np.histogram(magnitude.ravel(), bins=64, range=(0, 1))
            dir_hist, _ = np.histogram(direction.ravel(), bins=64, range=(-np.pi, np.pi))
            features.extend(mag_hist / (mag_hist.sum() + 1e-7))
            features.extend(dir_hist / (dir_hist.sum() + 1e-7))
            
            # 3. Regional features (grid-based)
            h, w = image.shape
            for i in range(0, h, h//8):
                for j in range(0, w, w//8):
                    region = image[i:i+h//8, j:j+w//8]
                    if region.size > 0:
                        # Statistical features
                        features.extend([
                            np.mean(region),
                            np.std(region),
                            np.min(region),
                            np.max(region)
                        ])
            
            return np.array(features)
            
        except Exception as e:
            logging.error(f"Error in fallback feature extraction: {e}")
            return None
    
    def calculate_lbp(self, image: np.ndarray, radius: int, n_points: int) -> np.ndarray:
        """Calculate Local Binary Pattern"""
        try:
            # Convert to uint8 if needed
            if image.dtype != np.uint8:
                image = (image * 255).astype(np.uint8)
                
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
                        
                        # Ensure coordinates are within bounds
                        x = max(0, min(rows-1, x))
                        y = max(0, min(cols-1, y))
                        
                        # Compare with center and build pattern
                        if image[x, y] >= center:
                            pattern |= (1 << p)
                    
                    lbp[i, j] = pattern
            
            return lbp
            
        except Exception as e:
            logging.error(f"Error calculating LBP: {e}")
            return np.zeros_like(image, dtype=np.uint8)
    
    def calculate_similarity(self, encoding1: np.ndarray, encoding2: np.ndarray) -> float:
        """Calculate similarity between two face encodings"""
        try:
            # Normalize encodings
            encoding1 = encoding1 / (np.linalg.norm(encoding1) + 1e-7)
            encoding2 = encoding2 / (np.linalg.norm(encoding2) + 1e-7)
            
            if self.distance_metric == "cosine":
                # Cosine similarity
                similarity = np.dot(encoding1, encoding2)
                return max(0, similarity)  # Ensure non-negative
            elif self.distance_metric == "euclidean":
                # Euclidean distance (converted to similarity)
                distance = np.linalg.norm(encoding1 - encoding2)
                return 1.0 / (1.0 + distance)
            else:
                # Default to cosine
                similarity = np.dot(encoding1, encoding2)
                return max(0, similarity)
                
        except Exception as e:
            logging.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def download_image_from_url(self, url: str) -> Optional[np.ndarray]:
        """Download image from URL and convert to OpenCV format"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                image = Image.open(BytesIO(response.content))
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            return None
        except Exception as e:
            logging.error(f"Error downloading image from {url}: {e}")
            return None
    
    def extract_and_save_face(self, photo_url: str, student_id: str) -> bool:
        """Extract face from photo URL and save CNN encodings"""
        try:
            # Download image
            image = self.download_image_from_url(photo_url)
            if image is None:
                logging.error(f"Failed to download image for student {student_id}")
                return False
            
            # Save temporary image for CNN processing
            temp_path = self.faces_dir / f"temp_student_{student_id}.jpg"
            cv2.imwrite(str(temp_path), image)
            
            # Extract CNN features
            encoding = self.extract_cnn_features(str(temp_path))
            if encoding is None:
                logging.error(f"Failed to extract CNN features for student {student_id}")
                return False
            
            # Save permanent face image
            face_path = self.faces_dir / f"cnn_student_{student_id}.jpg"
            cv2.imwrite(str(face_path), image)
            
            # Store encoding and data
            self.face_encodings[student_id] = encoding
            self.face_data[student_id] = {
                'face_path': str(face_path),
                'photo_url': photo_url,
                'encoding_length': len(encoding),
                'model_used': self.model_name if DEEPFACE_AVAILABLE else 'fallback_cnn'
            }
            
            # Save to files
            self.save_face_encodings()
            self.save_face_data()
            
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            
            logging.info(f"✅ CNN encoding extracted for student {student_id} (length: {len(encoding)})")
            return True
            
        except Exception as e:
            logging.error(f"Error extracting face for student {student_id}: {e}")
            return False
    
    def recognize_face_from_image(self, image: np.ndarray) -> Optional[Dict]:
        """Recognize face using CNN with detailed student information"""
        try:
            # Save temporary image for CNN processing
            temp_path = self.faces_dir / "temp_recognition.jpg"
            cv2.imwrite(str(temp_path), image)
            
            # Extract CNN features from uploaded image
            uploaded_encoding = self.extract_cnn_features(str(temp_path))
            if uploaded_encoding is None:
                return {
                    'match_found': False,
                    'reason': 'Could not extract face features from uploaded image',
                    'confidence': 0.0
                }
            
            # Compare with all stored encodings
            best_match = None
            best_similarity = 0.0
            all_similarities = {}
            
            for student_id, stored_encoding in self.face_encodings.items():
                similarity = self.calculate_similarity(uploaded_encoding, stored_encoding)
                all_similarities[student_id] = similarity
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = student_id
            
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            
            # Get detailed student information from database
            student_details = self.get_student_details(best_match) if best_match else None
            
            # Determine if match is acceptable
            if best_similarity >= self.VERIFICATION_THRESHOLD:
                confidence_level = "HIGH" if best_similarity >= self.HIGH_CONFIDENCE_THRESHOLD else "MEDIUM"
                
                return {
                    'match_found': True,
                    'student_id': best_match,
                    'confidence': best_similarity * 100,
                    'confidence_level': confidence_level,
                    'similarity_score': best_similarity,
                    'all_similarities': all_similarities,
                    'student_details': student_details,
                    'model_used': self.model_name if DEEPFACE_AVAILABLE else 'fallback_cnn',
                    'encoding_length': len(uploaded_encoding)
                }
            else:
                return {
                    'match_found': False,
                    'reason': f'Best similarity {best_similarity:.3f} below threshold {self.VERIFICATION_THRESHOLD}',
                    'confidence': best_similarity * 100,
                    'best_rejected_match': {
                        'student_id': best_match,
                        'similarity': best_similarity,
                        'student_details': student_details
                    } if best_match else None,
                    'all_similarities': all_similarities
                }
                
        except Exception as e:
            logging.error(f"Error recognizing face: {e}")
            return {
                'match_found': False,
                'reason': f'Error during recognition: {str(e)}',
                'confidence': 0.0
            }
    
    def get_student_details(self, student_id: str) -> Optional[Dict]:
        """Get comprehensive student details from database"""
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
                    'updated_at': result[9],
                    'face_data': self.face_data.get(student_id, {})
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
    
    def get_statistics(self) -> Dict:
        """Get system statistics"""
        return {
            'total_students': len(self.face_encodings),
            'model_used': self.model_name if DEEPFACE_AVAILABLE else 'fallback_cnn',
            'verification_threshold': self.VERIFICATION_THRESHOLD,
            'high_confidence_threshold': self.HIGH_CONFIDENCE_THRESHOLD,
            'detector_backend': self.detector_backend,
            'distance_metric': self.distance_metric,
            'deepface_available': DEEPFACE_AVAILABLE,
            'students_enrolled': list(self.face_encodings.keys())
        }

# Initialize the advanced CNN face recognizer
advanced_cnn_recognizer = AdvancedCNNFaceRecognition()