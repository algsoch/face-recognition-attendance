#!/usr/bin/env python3
"""
Secure Face Recognition with strict validation and unknown person detection
"""

import cv2
import numpy as np
import logging
from typing import Optional, Dict, List, Tuple
import json
from pathlib import Path
import requests
from PIL import Image
from io import BytesIO

class SecureFaceRecognition:
    """Face recognition with strict security measures"""
    
    def __init__(self, faces_dir: str = "faces"):
        self.faces_dir = Path(faces_dir)
        self.faces_dir.mkdir(exist_ok=True)
        
        # Strict security thresholds
        self.HIGH_CONFIDENCE_THRESHOLD = 0.85  # 85% minimum for high confidence
        self.MEDIUM_CONFIDENCE_THRESHOLD = 0.75  # 75% for medium confidence  
        self.MINIMUM_THRESHOLD = 0.65  # 65% absolute minimum
        self.FACE_QUALITY_THRESHOLD = 0.7  # Face quality check
        
        # Multiple validation requirements
        self.REQUIRE_MULTIPLE_METRICS = True
        self.MIN_FACE_SIZE = 50  # Minimum face size in pixels
        
        self.face_data = {}
        self.face_features = {}
        
        # File paths
        self.face_data_file = Path("face_data_secure.json")
        self.features_file = Path("face_features_secure.json")
        
        # Load existing data
        self.load_face_data()
        self.load_face_features()
        
        # Initialize face cascade
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        logging.basicConfig(level=logging.INFO)
    
    def validate_face_quality(self, face_img: np.ndarray) -> Tuple[bool, float, str]:
        """Validate face image quality with multiple checks"""
        try:
            if face_img is None or face_img.size == 0:
                return False, 0.0, "Empty or invalid image"
            
            h, w = face_img.shape
            
            # Size check
            if h < self.MIN_FACE_SIZE or w < self.MIN_FACE_SIZE:
                return False, 0.0, f"Face too small: {h}x{w} (minimum {self.MIN_FACE_SIZE}x{self.MIN_FACE_SIZE})"
            
            # Blur detection using Laplacian variance
            laplacian_var = cv2.Laplacian(face_img, cv2.CV_64F).var()
            blur_threshold = 100  # Adjust based on testing
            
            if laplacian_var < blur_threshold:
                return False, laplacian_var/blur_threshold, f"Image too blurry: {laplacian_var:.1f} < {blur_threshold}"
            
            # Brightness check
            mean_brightness = np.mean(face_img)
            if mean_brightness < 30 or mean_brightness > 230:
                return False, 0.5, f"Poor lighting: brightness={mean_brightness:.1f}"
            
            # Contrast check
            contrast = np.std(face_img)
            if contrast < 20:
                return False, contrast/20, f"Low contrast: {contrast:.1f}"
            
            # Calculate overall quality score
            quality_score = min(1.0, (laplacian_var/blur_threshold) * 0.6 + (contrast/50) * 0.4)
            
            if quality_score < self.FACE_QUALITY_THRESHOLD:
                return False, quality_score, f"Overall quality too low: {quality_score:.2f} < {self.FACE_QUALITY_THRESHOLD}"
            
            return True, quality_score, "Face quality acceptable"
            
        except Exception as e:
            return False, 0.0, f"Error validating face quality: {e}"
    
    def extract_enhanced_features(self, face_img: np.ndarray) -> Optional[np.ndarray]:
        """Extract enhanced facial features with better discrimination"""
        try:
            # Validate face quality first
            is_valid, quality_score, message = self.validate_face_quality(face_img)
            if not is_valid:
                logging.warning(f"Face quality validation failed: {message}")
                return None
            
            # Resize to standard size
            face_img = cv2.resize(face_img, (100, 100))
            
            # Advanced preprocessing
            # 1. Histogram equalization for lighting normalization
            face_img = cv2.equalizeHist(face_img)
            
            # 2. Gaussian blur to reduce noise
            face_img = cv2.GaussianBlur(face_img, (3, 3), 0)
            
            # 3. Normalize pixel values
            face_img = cv2.normalize(face_img, None, 0, 255, cv2.NORM_MINMAX)
            
            # Extract multiple discriminative features
            features = []
            
            # 1. Enhanced LBP with multiple radii for better discrimination
            for radius in [1, 2, 3]:
                lbp = self.calculate_lbp(face_img, radius, 8)
                lbp_hist, _ = np.histogram(lbp.ravel(), bins=256, range=(0, 256))
                lbp_hist = lbp_hist.astype(float)
                lbp_hist /= (lbp_hist.sum() + 1e-7)
                features.extend(lbp_hist)
            
            # 2. Gradient features with multiple orientations
            grad_x = cv2.Sobel(face_img, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(face_img, cv2.CV_64F, 0, 1, ksize=3)
            grad_mag = np.sqrt(grad_x**2 + grad_y**2)
            grad_dir = np.arctan2(grad_y, grad_x)
            
            # Gradient magnitude histogram
            grad_hist, _ = np.histogram(grad_mag.ravel(), bins=50, range=(0, 255))
            grad_hist = grad_hist.astype(float)
            grad_hist /= (grad_hist.sum() + 1e-7)
            features.extend(grad_hist)
            
            # Gradient direction histogram
            dir_hist, _ = np.histogram(grad_dir.ravel(), bins=36, range=(-np.pi, np.pi))
            dir_hist = dir_hist.astype(float)
            dir_hist /= (dir_hist.sum() + 1e-7)
            features.extend(dir_hist)
            
            # 3. Regional intensity features (divide face into regions)
            h, w = face_img.shape
            regions = [
                face_img[:h//2, :w//2],    # Top-left
                face_img[:h//2, w//2:],    # Top-right
                face_img[h//2:, :w//2],    # Bottom-left
                face_img[h//2:, w//2:],    # Bottom-right
                face_img[h//4:3*h//4, w//4:3*w//4]  # Center region
            ]
            
            for region in regions:
                if region.size > 0:
                    region_hist, _ = np.histogram(region.ravel(), bins=32, range=(0, 255))
                    region_hist = region_hist.astype(float)
                    region_hist /= (region_hist.sum() + 1e-7)
                    features.extend(region_hist)
            
            return np.array(features)
            
        except Exception as e:
            logging.error(f"Error extracting enhanced features: {e}")
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
    
    def calculate_multi_metric_similarity(self, features1: np.ndarray, features2: np.ndarray) -> Dict[str, float]:
        """Calculate multiple similarity metrics for robust comparison"""
        try:
            # Normalize features
            features1 = features1 / (np.linalg.norm(features1) + 1e-7)
            features2 = features2 / (np.linalg.norm(features2) + 1e-7)
            
            # 1. Cosine similarity
            cosine_sim = np.dot(features1, features2)
            
            # 2. Euclidean distance (converted to similarity)
            euclidean_dist = np.linalg.norm(features1 - features2)
            euclidean_sim = 1.0 / (1.0 + euclidean_dist)
            
            # 3. Correlation coefficient
            correlation = np.corrcoef(features1, features2)[0, 1]
            if np.isnan(correlation):
                correlation = 0.0
            correlation_sim = (correlation + 1.0) / 2.0  # Convert to 0-1 range
            
            # 4. Chi-square similarity
            chi_square = np.sum((features1 - features2) ** 2 / (features1 + features2 + 1e-7))
            chi_square_sim = 1.0 / (1.0 + chi_square)
            
            return {
                'cosine': cosine_sim,
                'euclidean': euclidean_sim,
                'correlation': correlation_sim,
                'chi_square': chi_square_sim
            }
            
        except Exception as e:
            logging.error(f"Error calculating similarity metrics: {e}")
            return {'cosine': 0.0, 'euclidean': 0.0, 'correlation': 0.0, 'chi_square': 0.0}
    
    def validate_recognition_result(self, similarities: Dict[str, float], student_id: str) -> Dict:
        """Validate recognition result with strict security checks"""
        
        # Calculate weighted ensemble score
        weights = {
            'cosine': 0.3,
            'euclidean': 0.25,
            'correlation': 0.25,
            'chi_square': 0.2
        }
        
        ensemble_score = sum(similarities[metric] * weight for metric, weight in weights.items())
        
        # Security validation checks
        checks = {
            'high_confidence': ensemble_score >= self.HIGH_CONFIDENCE_THRESHOLD,
            'medium_confidence': ensemble_score >= self.MEDIUM_CONFIDENCE_THRESHOLD,
            'minimum_threshold': ensemble_score >= self.MINIMUM_THRESHOLD,
            'cosine_check': similarities['cosine'] >= 0.7,
            'correlation_check': similarities['correlation'] >= 0.6,
            'consistent_metrics': (max(similarities.values()) - min(similarities.values())) < 0.4
        }
        
        # Determine confidence level
        if checks['high_confidence'] and checks['cosine_check'] and checks['correlation_check']:
            confidence_level = "HIGH"
            accept_match = True
        elif checks['medium_confidence'] and checks['consistent_metrics']:
            confidence_level = "MEDIUM"
            accept_match = True
        elif checks['minimum_threshold']:
            confidence_level = "LOW"
            accept_match = False  # Reject low confidence matches for security
        else:
            confidence_level = "REJECTED"
            accept_match = False
        
        return {
            'student_id': student_id,
            'ensemble_score': ensemble_score,
            'confidence_level': confidence_level,
            'accept_match': accept_match,
            'similarities': similarities,
            'security_checks': checks,
            'confidence_percentage': ensemble_score * 100
        }
    
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
                return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            return None
        except Exception as e:
            logging.error(f"Error downloading image from {url}: {e}")
            return None
    
    def extract_and_save_face(self, photo_url: str, student_id: str) -> bool:
        """Extract face from photo URL and save features securely"""
        try:
            # Download image
            image = self.download_image_from_url(photo_url)
            if image is None:
                logging.error(f"Failed to download image for student {student_id}")
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
            
            # Extract enhanced features with quality validation
            features = self.extract_enhanced_features(face_img)
            if features is None:
                logging.warning(f"Failed to extract valid features for student {student_id}")
                return False
            
            # Save face image for debugging
            face_img_resized = cv2.resize(face_img, (100, 100))
            face_path = self.faces_dir / f"secure_student_{student_id}.jpg"
            cv2.imwrite(str(face_path), face_img_resized)
            
            # Store face data and features
            self.face_data[student_id] = {
                'face_path': str(face_path),
                'photo_url': photo_url
            }
            self.face_features[student_id] = features
            
            self.save_face_data()
            self.save_face_features()
            
            logging.info(f"Successfully extracted secure features for student {student_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error extracting face for student {student_id}: {e}")
            return False
    
    def recognize_face_from_image(self, image: np.ndarray) -> Optional[Dict]:
        """Securely recognize face from image with strict validation"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) == 0:
                return {
                    'match_found': False,
                    'reason': 'No faces detected in image',
                    'confidence_level': 'NO_FACE'
                }
            
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
            
            # Extract enhanced features with quality validation
            uploaded_features = self.extract_enhanced_features(uploaded_face)
            if uploaded_features is None:
                return {
                    'match_found': False,
                    'reason': 'Face quality validation failed',
                    'confidence_level': 'POOR_QUALITY'
                }
            
            # Compare with all stored features using strict validation
            best_result = None
            all_results = []
            
            for student_id, stored_features in self.face_features.items():
                similarities = self.calculate_multi_metric_similarity(uploaded_features, stored_features)
                result = self.validate_recognition_result(similarities, student_id)
                all_results.append(result)
                
                if result['accept_match'] and (best_result is None or result['ensemble_score'] > best_result['ensemble_score']):
                    best_result = result
            
            # Return the best valid match or rejection
            if best_result and best_result['accept_match']:
                return {
                    'match_found': True,
                    'student_id': best_result['student_id'],
                    'confidence_percentage': best_result['confidence_percentage'],
                    'confidence_level': best_result['confidence_level'],
                    'ensemble_score': best_result['ensemble_score'],
                    'similarities': best_result['similarities'],
                    'security_checks': best_result['security_checks']
                }
            else:
                # Find the best rejected match for information
                best_rejected = max(all_results, key=lambda x: x['ensemble_score']) if all_results else None
                
                return {
                    'match_found': False,
                    'reason': 'No student meets security validation requirements',
                    'confidence_level': 'REJECTED',
                    'best_rejected_match': {
                        'student_id': best_rejected['student_id'],
                        'confidence_percentage': best_rejected['confidence_percentage'],
                        'confidence_level': best_rejected['confidence_level']
                    } if best_rejected else None
                }
                
        except Exception as e:
            logging.error(f"Error recognizing face: {e}")
            return {
                'match_found': False,
                'reason': f'Error during recognition: {str(e)}',
                'confidence_level': 'ERROR'
            }

# Initialize secure face recognizer
secure_face_recognizer = SecureFaceRecognition()