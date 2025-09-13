"""
Facial Recognition module for student self-attendance
"""
import cv2
import face_recognition
import numpy as np
import json
import os
from typing import List, Tuple, Optional
from PIL import Image
import base64
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class FaceRecognitionSystem:
    """Face recognition system for attendance management"""
    
    def __init__(self):
        self.known_faces = {}
        self.tolerance = 0.6  # Face recognition tolerance (lower = more strict)
    
    def encode_face_from_image(self, image_path: str) -> Optional[List[float]]:
        """
        Extract face encoding from an image file
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Face encoding as a list of floats, or None if no face found
        """
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) > 0:
                # Return the first face encoding found
                return face_encodings[0].tolist()
            else:
                logger.warning(f"No face found in image: {image_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            return None
    
    def encode_face_from_base64(self, base64_image: str) -> Optional[List[float]]:
        """
        Extract face encoding from base64 encoded image
        
        Args:
            base64_image: Base64 encoded image string
            
        Returns:
            Face encoding as a list of floats, or None if no face found
        """
        try:
            # Decode base64 image
            image_data = base64.b64decode(base64_image.split(',')[1] if ',' in base64_image else base64_image)
            image = Image.open(BytesIO(image_data))
            
            # Convert PIL image to numpy array
            image_array = np.array(image)
            
            # If image is RGBA, convert to RGB
            if image_array.shape[2] == 4:
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGBA2RGB)
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(image_array)
            
            if len(face_encodings) > 0:
                return face_encodings[0].tolist()
            else:
                logger.warning("No face found in uploaded image")
                return None
                
        except Exception as e:
            logger.error(f"Error processing base64 image: {str(e)}")
            return None
    
    def encode_face_from_webcam_frame(self, frame: np.ndarray) -> Optional[List[float]]:
        """
        Extract face encoding from webcam frame
        
        Args:
            frame: OpenCV frame from webcam
            
        Returns:
            Face encoding as a list of floats, or None if no face found
        """
        try:
            # Convert BGR to RGB (OpenCV uses BGR, face_recognition uses RGB)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(rgb_frame)
            
            if len(face_encodings) > 0:
                return face_encodings[0].tolist()
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error processing webcam frame: {str(e)}")
            return None
    
    def compare_faces(self, known_encoding: List[float], unknown_encoding: List[float]) -> Tuple[bool, float]:
        """
        Compare two face encodings
        
        Args:
            known_encoding: Previously stored face encoding
            unknown_encoding: New face encoding to compare
            
        Returns:
            Tuple of (is_match, confidence_score)
        """
        try:
            # Convert lists back to numpy arrays
            known_encoding_np = np.array(known_encoding)
            unknown_encoding_np = np.array(unknown_encoding)
            
            # Calculate face distance (lower = more similar)
            distance = face_recognition.face_distance([known_encoding_np], unknown_encoding_np)[0]
            
            # Calculate confidence score (higher = more confident)
            confidence = 1 - distance
            
            # Determine if it's a match
            is_match = distance <= self.tolerance
            
            return is_match, round(confidence * 100, 2)
            
        except Exception as e:
            logger.error(f"Error comparing faces: {str(e)}")
            return False, 0.0
    
    def load_student_faces(self, db_session):
        """
        Load all student face encodings from database
        
        Args:
            db_session: Database session
        """
        from backend.models import Student
        
        try:
            students = db_session.query(Student).filter(
                Student.is_active == True,
                Student.face_encoding.isnot(None)
            ).all()
            
            self.known_faces = {}
            for student in students:
                try:
                    face_encoding = json.loads(student.face_encoding)
                    self.known_faces[student.student_id] = {
                        'encoding': face_encoding,
                        'name': student.name,
                        'roll_number': student.roll_number
                    }
                except json.JSONDecodeError:
                    logger.warning(f"Invalid face encoding for student {student.student_id}")
            
            logger.info(f"Loaded {len(self.known_faces)} student face encodings")
            
        except Exception as e:
            logger.error(f"Error loading student faces: {str(e)}")
    
    def recognize_student(self, frame: np.ndarray, db_session) -> Optional[dict]:
        """
        Recognize student from webcam frame
        
        Args:
            frame: OpenCV frame from webcam
            db_session: Database session
            
        Returns:
            Dictionary with student info and confidence, or None if no match
        """
        try:
            # Extract face encoding from frame
            face_encoding = self.encode_face_from_webcam_frame(frame)
            
            if face_encoding is None:
                return None
            
            # Load known faces if not already loaded
            if not self.known_faces:
                self.load_student_faces(db_session)
            
            best_match = None
            best_confidence = 0.0
            
            # Compare with all known faces
            for student_id, student_data in self.known_faces.items():
                is_match, confidence = self.compare_faces(
                    student_data['encoding'], 
                    face_encoding
                )
                
                if is_match and confidence > best_confidence:
                    best_match = {
                        'student_id': student_id,
                        'name': student_data['name'],
                        'roll_number': student_data['roll_number'],
                        'confidence': confidence
                    }
                    best_confidence = confidence
            
            return best_match
            
        except Exception as e:
            logger.error(f"Error recognizing student: {str(e)}")
            return None
    
    def save_student_face_encoding(self, student_id: int, image_path: str, db_session):
        """
        Save face encoding for a student
        
        Args:
            student_id: Student ID
            image_path: Path to the student's photo
            db_session: Database session
        """
        from backend.models import Student
        
        try:
            # Extract face encoding
            face_encoding = self.encode_face_from_image(image_path)
            
            if face_encoding is None:
                raise ValueError("No face found in the image")
            
            # Update student record with face encoding
            student = db_session.query(Student).filter(Student.student_id == student_id).first()
            if student:
                student.face_encoding = json.dumps(face_encoding)
                db_session.commit()
                logger.info(f"Face encoding saved for student {student_id}")
                return True
            else:
                raise ValueError(f"Student with ID {student_id} not found")
                
        except Exception as e:
            logger.error(f"Error saving face encoding for student {student_id}: {str(e)}")
            return False


# Global face recognition instance
face_recognition_system = FaceRecognitionSystem()


def detect_faces_in_frame(frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """
    Detect faces in a frame and return bounding boxes
    
    Args:
        frame: OpenCV frame
        
    Returns:
        List of face bounding boxes as (top, right, bottom, left)
    """
    try:
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find face locations
        face_locations = face_recognition.face_locations(rgb_frame)
        
        return face_locations
        
    except Exception as e:
        logger.error(f"Error detecting faces: {str(e)}")
        return []


def draw_face_boxes(frame: np.ndarray, face_locations: List[Tuple[int, int, int, int]], 
                   names: List[str] = None) -> np.ndarray:
    """
    Draw bounding boxes around detected faces
    
    Args:
        frame: OpenCV frame
        face_locations: List of face bounding boxes
        names: Optional list of names for each face
        
    Returns:
        Frame with drawn bounding boxes
    """
    for i, (top, right, bottom, left) in enumerate(face_locations):
        # Draw rectangle around face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        
        # Draw name if provided
        if names and i < len(names):
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, names[i], (left + 6, bottom - 6), font, 0.8, (255, 255, 255), 1)
    
    return frame
