#!/usr/bin/env python3
"""
Ultra-Robust Face Recognition System with Advanced Validation
This system prevents false positives with multiple validation layers
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

class UltraRobustFaceRecognition:
    """Ultra-robust face recognition with multiple validation layers"""
    
    def __init__(self, faces_dir: str = "ultra_faces"):
        self.faces_dir = Path(faces_dir)
        self.faces_dir.mkdir(exist_ok=True)
        
        # ULTRA-STRICT thresholds to prevent false positives
        self.ULTRA_HIGH_THRESHOLD = 0.95    # 95% for ultra-high confidence
        self.HIGH_THRESHOLD = 0.85          # 85% for high confidence
        self.MEDIUM_THRESHOLD = 0.75        # 75% for medium confidence
        self.MINIMUM_THRESHOLD = 0.65       # 65% absolute minimum
        self.REJECT_THRESHOLD = 0.50        # Below 50% is definitely rejected
        
        # Multi-metric validation requirements
        self.REQUIRE_CONSENSUS = True       # Multiple metrics must agree
        self.MIN_CONSENSUS_COUNT = 3        # At least 3 metrics must agree
        self.MAX_VARIANCE = 0.15           # Max variance between metrics
        
        # Storage
        self.face_encodings = {}
        self.face_data = {}
        self.validation_cache = {}
        
        # File paths
        self.encodings_file = Path("ultra_face_encodings.json")
        self.face_data_file = Path("ultra_face_data.json")
        
        # Load existing data
        self.load_face_data()
        self.load_face_encodings()
        
        logging.basicConfig(level=logging.INFO)
        logging.info("🛡️ Ultra-Robust Face Recognition System Initialized")
    
    def extract_ultra_robust_features(self, image_path: str) -> Optional[Dict[str, np.ndarray]]:
        """Extract multiple feature types for ultra-robust recognition"""
        try:
            # Load and preprocess image
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                return None
            
            # Resize and normalize
            image = cv2.resize(image, (256, 256))  # Larger size for better features
            image = cv2.equalizeHist(image)
            image = cv2.GaussianBlur(image, (3, 3), 0)
            image = image.astype(np.float32) / 255.0
            
            features = {}
            
            # 1. Multi-scale LBP features
            lbp_features = []
            for radius in [1, 2, 3, 4, 5]:
                for n_points in [8, 16]:
                    lbp = self.calculate_lbp(image, radius, n_points)
                    lbp_hist, _ = np.histogram(lbp.ravel(), bins=256, range=(0, 256))
                    lbp_hist = lbp_hist.astype(float)
                    lbp_hist /= (lbp_hist.sum() + 1e-7)
                    lbp_features.extend(lbp_hist)
            features['lbp'] = np.array(lbp_features)
            
            # 2. Enhanced gradient features
            grad_features = []
            for ksize in [3, 5, 7]:
                grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=ksize)
                grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=ksize)
                magnitude = np.sqrt(grad_x**2 + grad_y**2)
                direction = np.arctan2(grad_y, grad_x)
                
                # Magnitude histogram
                mag_hist, _ = np.histogram(magnitude.ravel(), bins=64, range=(0, 1))
                grad_features.extend(mag_hist / (mag_hist.sum() + 1e-7))
                
                # Direction histogram
                dir_hist, _ = np.histogram(direction.ravel(), bins=36, range=(-np.pi, np.pi))
                grad_features.extend(dir_hist / (dir_hist.sum() + 1e-7))
            features['gradient'] = np.array(grad_features)
            
            # 3. Regional intensity features (detailed grid)
            regional_features = []
            h, w = image.shape
            grid_size = 16  # 16x16 grid
            for i in range(0, h, h//grid_size):
                for j in range(0, w, w//grid_size):
                    region = image[i:i+h//grid_size, j:j+w//grid_size]
                    if region.size > 0:
                        # Statistical moments
                        regional_features.extend([
                            np.mean(region),
                            np.std(region),
                            np.min(region),
                            np.max(region),
                            np.median(region),
                            np.percentile(region, 25),
                            np.percentile(region, 75)
                        ])
            features['regional'] = np.array(regional_features)
            
            # 4. Texture features using Gabor filters
            gabor_features = []
            for theta in [0, 45, 90, 135]:  # Different orientations
                for frequency in [0.1, 0.3, 0.5]:  # Different frequencies
                    gabor_kernel = cv2.getGaborKernel((21, 21), 5, np.radians(theta), 
                                                    2*np.pi*frequency, 0.5, 0, ktype=cv2.CV_32F)
                    gabor_response = cv2.filter2D(image, cv2.CV_8UC3, gabor_kernel)
                    gabor_hist, _ = np.histogram(gabor_response.ravel(), bins=32, range=(0, 1))
                    gabor_features.extend(gabor_hist / (gabor_hist.sum() + 1e-7))
            features['gabor'] = np.array(gabor_features)
            
            # 5. Edge density features
            edge_features = []
            for threshold1, threshold2 in [(50, 150), (100, 200), (150, 250)]:
                edges = cv2.Canny((image * 255).astype(np.uint8), threshold1, threshold2)
                edge_density = np.sum(edges > 0) / edges.size
                edge_features.append(edge_density)
            features['edges'] = np.array(edge_features)
            
            return features
            
        except Exception as e:
            logging.error(f"Error extracting ultra-robust features: {e}")
            return None
    
    def calculate_lbp(self, image: np.ndarray, radius: int, n_points: int) -> np.ndarray:
        """Calculate Local Binary Pattern with improved implementation"""
        try:
            if image.dtype != np.uint8:
                image = (image * 255).astype(np.uint8)
                
            rows, cols = image.shape
            lbp = np.zeros((rows, cols), dtype=np.uint8)
            
            # Precompute neighbor coordinates
            angles = [2 * np.pi * p / n_points for p in range(n_points)]
            dx = [int(radius * np.cos(angle)) for angle in angles]
            dy = [int(radius * np.sin(angle)) for angle in angles]
            
            for i in range(radius, rows - radius):
                for j in range(radius, cols - radius):
                    center = image[i, j]
                    pattern = 0
                    
                    for p in range(n_points):
                        x = max(0, min(rows-1, i + dx[p]))
                        y = max(0, min(cols-1, j + dy[p]))
                        
                        if image[x, y] >= center:
                            pattern |= (1 << p)
                    
                    lbp[i, j] = pattern
            
            return lbp
            
        except Exception as e:
            logging.error(f"Error calculating LBP: {e}")
            return np.zeros_like(image, dtype=np.uint8)
    
    def calculate_multi_metric_similarity(self, features1: Dict[str, np.ndarray], 
                                        features2: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Calculate multiple similarity metrics for each feature type"""
        try:
            similarities = {}
            
            for feature_type in ['lbp', 'gradient', 'regional', 'gabor', 'edges']:
                if feature_type in features1 and feature_type in features2:
                    f1 = features1[feature_type]
                    f2 = features2[feature_type]
                    
                    # Normalize features
                    f1 = f1 / (np.linalg.norm(f1) + 1e-7)
                    f2 = f2 / (np.linalg.norm(f2) + 1e-7)
                    
                    # Calculate multiple similarity metrics
                    cosine_sim = np.dot(f1, f2)
                    euclidean_dist = np.linalg.norm(f1 - f2)
                    euclidean_sim = 1.0 / (1.0 + euclidean_dist)
                    
                    # Correlation
                    correlation = np.corrcoef(f1, f2)[0, 1] if f1.size > 1 else 0.0
                    if np.isnan(correlation):
                        correlation = 0.0
                    correlation_sim = (correlation + 1.0) / 2.0
                    
                    # Store best similarity for this feature type
                    similarities[feature_type] = max(cosine_sim, euclidean_sim, correlation_sim)
            
            return similarities
            
        except Exception as e:
            logging.error(f"Error calculating multi-metric similarity: {e}")
            return {}
    
    def validate_recognition_with_consensus(self, similarities: Dict[str, float], 
                                          student_id: str) -> Dict:
        """Ultra-strict validation with consensus requirements"""
        
        if not similarities:
            return {
                'accept': False,
                'reason': 'No similarity metrics calculated',
                'confidence_level': 'ERROR'
            }
        
        # Calculate overall similarity score
        similarity_values = list(similarities.values())
        overall_similarity = np.mean(similarity_values)
        similarity_variance = np.var(similarity_values)
        
        # Count how many metrics pass each threshold
        ultra_high_count = sum(1 for sim in similarity_values if sim >= self.ULTRA_HIGH_THRESHOLD)
        high_count = sum(1 for sim in similarity_values if sim >= self.HIGH_THRESHOLD)
        medium_count = sum(1 for sim in similarity_values if sim >= self.MEDIUM_THRESHOLD)
        minimum_count = sum(1 for sim in similarity_values if sim >= self.MINIMUM_THRESHOLD)
        
        # Consensus validation
        total_metrics = len(similarity_values)
        consensus_achieved = minimum_count >= self.MIN_CONSENSUS_COUNT
        low_variance = similarity_variance < self.MAX_VARIANCE
        
        # Determine acceptance and confidence level
        if (ultra_high_count >= 3 and overall_similarity >= self.ULTRA_HIGH_THRESHOLD and 
            consensus_achieved and low_variance):
            return {
                'accept': True,
                'confidence_level': 'ULTRA_HIGH',
                'overall_similarity': overall_similarity,
                'consensus_count': minimum_count,
                'variance': similarity_variance,
                'reason': f'Ultra-high consensus: {ultra_high_count}/{total_metrics} metrics above 95%'
            }
        elif (high_count >= 3 and overall_similarity >= self.HIGH_THRESHOLD and 
              consensus_achieved and low_variance):
            return {
                'accept': True,
                'confidence_level': 'HIGH',
                'overall_similarity': overall_similarity,
                'consensus_count': minimum_count,
                'variance': similarity_variance,
                'reason': f'High consensus: {high_count}/{total_metrics} metrics above 85%'
            }
        elif (medium_count >= 4 and overall_similarity >= self.MEDIUM_THRESHOLD and 
              consensus_achieved and low_variance):
            return {
                'accept': True,
                'confidence_level': 'MEDIUM',
                'overall_similarity': overall_similarity,
                'consensus_count': minimum_count,
                'variance': similarity_variance,
                'reason': f'Medium consensus: {medium_count}/{total_metrics} metrics above 75%'
            }
        else:
            return {
                'accept': False,
                'confidence_level': 'REJECTED',
                'overall_similarity': overall_similarity,
                'consensus_count': minimum_count,
                'variance': similarity_variance,
                'reason': f'Insufficient consensus: {minimum_count}/{total_metrics} metrics, variance: {similarity_variance:.3f}'
            }
    
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
        """Extract and save ultra-robust face features"""
        try:
            # Download image
            image = self.download_image_from_url(photo_url)
            if image is None:
                return False
            
            # Save temporary image
            temp_path = self.faces_dir / f"temp_ultra_{student_id}.jpg"
            cv2.imwrite(str(temp_path), image)
            
            # Extract ultra-robust features
            features = self.extract_ultra_robust_features(str(temp_path))
            if features is None:
                return False
            
            # Save permanent face image
            face_path = self.faces_dir / f"ultra_student_{student_id}.jpg"
            cv2.imwrite(str(face_path), image)
            
            # Store features and data
            self.face_encodings[student_id] = features
            self.face_data[student_id] = {
                'face_path': str(face_path),
                'photo_url': photo_url,
                'feature_types': list(features.keys()),
                'total_features': sum(len(f) for f in features.values())
            }
            
            # Save to files
            self.save_face_encodings()
            self.save_face_data()
            
            # Clean up
            if temp_path.exists():
                temp_path.unlink()
            
            logging.info(f"✅ Ultra-robust features extracted for student {student_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error extracting face for student {student_id}: {e}")
            return False
    
    def recognize_face_from_image(self, image: np.ndarray) -> Optional[Dict]:
        """Ultra-robust face recognition with strict validation"""
        try:
            # Save temporary image
            temp_path = self.faces_dir / "temp_ultra_recognition.jpg"
            cv2.imwrite(str(temp_path), image)
            
            # Extract features
            uploaded_features = self.extract_ultra_robust_features(str(temp_path))
            if uploaded_features is None:
                return {
                    'match_found': False,
                    'reason': 'Could not extract features from uploaded image'
                }
            
            # Compare with all stored features
            best_match = None
            best_validation = None
            all_results = {}
            
            for student_id, stored_features in self.face_encodings.items():
                similarities = self.calculate_multi_metric_similarity(uploaded_features, stored_features)
                validation = self.validate_recognition_with_consensus(similarities, student_id)
                
                all_results[student_id] = {
                    'similarities': similarities,
                    'validation': validation,
                    'overall_similarity': validation.get('overall_similarity', 0.0)
                }
                
                if (validation['accept'] and 
                    (best_validation is None or 
                     validation['overall_similarity'] > best_validation['overall_similarity'])):
                    best_match = student_id
                    best_validation = validation
            
            # Clean up
            if temp_path.exists():
                temp_path.unlink()
            
            # Return result
            if best_match and best_validation['accept']:
                student_details = self.get_student_details(best_match)
                return {
                    'match_found': True,
                    'student_id': best_match,
                    'confidence': best_validation['overall_similarity'] * 100,
                    'confidence_level': best_validation['confidence_level'],
                    'validation_details': best_validation,
                    'student_details': student_details,
                    'all_similarities': {sid: result['validation']['overall_similarity'] 
                                       for sid, result in all_results.items()}
                }
            else:
                # Find best rejected match
                best_rejected = max(all_results.items(), 
                                  key=lambda x: x[1]['overall_similarity']) if all_results else None
                
                return {
                    'match_found': False,
                    'reason': 'No student passed ultra-robust validation',
                    'best_rejected_match': {
                        'student_id': best_rejected[0],
                        'confidence': best_rejected[1]['overall_similarity'] * 100,
                        'validation': best_rejected[1]['validation'],
                        'student_details': self.get_student_details(best_rejected[0])
                    } if best_rejected else None,
                    'all_similarities': {sid: result['validation']['overall_similarity'] 
                                       for sid, result in all_results.items()}
                }
                
        except Exception as e:
            logging.error(f"Error in ultra-robust recognition: {e}")
            return {
                'match_found': False,
                'reason': f'Error during recognition: {str(e)}'
            }
    
    def get_student_details(self, student_id: str) -> Optional[Dict]:
        """Get student details from database"""
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT student_id, roll_number, name, class_name, section, branch, 
                       photo_url, is_active, created_at, updated_at
                FROM students WHERE student_id = ?
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
        """Load face encodings"""
        if self.encodings_file.exists():
            try:
                with open(self.encodings_file, 'r') as f:
                    data = json.load(f)
                    self.face_encodings = {}
                    for k, v in data.items():
                        self.face_encodings[k] = {
                            feature_type: np.array(features) 
                            for feature_type, features in v.items()
                        }
            except Exception as e:
                logging.error(f"Error loading encodings: {e}")
                self.face_encodings = {}
    
    def save_face_encodings(self):
        """Save face encodings"""
        try:
            data = {}
            for k, v in self.face_encodings.items():
                data[k] = {
                    feature_type: features.tolist() 
                    for feature_type, features in v.items()
                }
            with open(self.encodings_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logging.error(f"Error saving encodings: {e}")
    
    def load_face_data(self):
        """Load face data"""
        if self.face_data_file.exists():
            try:
                with open(self.face_data_file, 'r') as f:
                    self.face_data = json.load(f)
            except Exception as e:
                logging.error(f"Error loading face data: {e}")
                self.face_data = {}
    
    def save_face_data(self):
        """Save face data"""
        try:
            with open(self.face_data_file, 'w') as f:
                json.dump(self.face_data, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving face data: {e}")

# Initialize ultra-robust recognizer
ultra_robust_recognizer = UltraRobustFaceRecognition()