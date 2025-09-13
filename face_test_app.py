#!/usr/bin/env python3
"""
Simple web interface for testing face recognition with uploaded photos
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import cv2
import numpy as np
import io
from PIL import Image
from backend.secure_face_recognition import secure_face_recognizer

app = FastAPI(title="Face Recognition Test")

# HTML template for photo upload
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Face Recognition Test</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0; }
        .result { margin: 20px 0; padding: 20px; border-radius: 5px; }
        .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .info { background-color: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        button:hover { background: #0056b3; }
        img { max-width: 200px; margin: 10px; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <h1>🎯 Face Recognition Test</h1>
    
    <div class="info">
        <h3>🔒 SECURE Face Recognition Test:</h3>
        <p><strong>⚠️ HIGH SECURITY MODE ENABLED</strong></p>
        <p>• Minimum 85% confidence required for high confidence matches</p>
        <p>• Multiple validation metrics must agree</p>
        <p>• Face quality checks enforced</p>
        <p>• Unknown persons will be REJECTED</p>
        <p>• Current database: 5 students (Sumit, Aaditya, Ashri, Shilpi, Vicky Kumar)</p>
    </div>
    
    <form id="uploadForm" enctype="multipart/form-data">
        <div class="upload-area">
            <input type="file" id="photoFile" name="file" accept="image/*" required>
            <br><br>
            <button type="submit">🔍 Test Face Recognition</button>
        </div>
    </form>
    
    <div id="result"></div>
    
    <script>
        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData();
            const fileInput = document.getElementById('photoFile');
            formData.append('file', fileInput.files[0]);
            
            document.getElementById('result').innerHTML = '<div class="info">Processing...</div>';
            
            try {
                const response = await fetch('/test-face-recognition', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                let resultHtml = '';
                if (data.match_found) {
                    resultHtml = `
                        <div class="success">
                            <h3>✅ SECURE Match Found!</h3>
                            <p><strong>Student ID:</strong> ${data.student_id}</p>
                            <p><strong>Confidence:</strong> ${data.confidence.toFixed(1)}%</p>
                            <p><strong>Security Level:</strong> ${data.confidence_level}</p>
                            <p><strong>Ensemble Score:</strong> ${data.ensemble_score.toFixed(3)}</p>
                            <details>
                                <summary>Security Details</summary>
                                <p><strong>Similarities:</strong></p>
                                <ul>
                                    <li>Cosine: ${data.similarities.cosine.toFixed(3)}</li>
                                    <li>Euclidean: ${data.similarities.euclidean.toFixed(3)}</li>
                                    <li>Correlation: ${data.similarities.correlation.toFixed(3)}</li>
                                    <li>Chi-square: ${data.similarities.chi_square.toFixed(3)}</li>
                                </ul>
                            </details>
                        </div>
                    `;
                } else {
                    resultHtml = `
                        <div class="error">
                            <h3>🔒 ACCESS DENIED - Security Validation Failed</h3>
                            <p><strong>Reason:</strong> ${data.reason}</p>
                            <p><strong>Security Level:</strong> ${data.confidence_level}</p>
                            ${data.best_rejected_match ? `
                                <p><strong>Best Rejected Match:</strong> Student ${data.best_rejected_match.student_id} (${data.best_rejected_match.confidence_percentage.toFixed(1)}% - ${data.best_rejected_match.confidence_level})</p>
                                <p style="color: #dc3545; font-weight: bold;">⚠️ This person is NOT recognized as a valid student!</p>
                            ` : '<p><strong>No matches found in database</strong></p>'}
                        </div>
                    `;
                }
                
                if (data.faces_detected) {
                    resultHtml += `<p><strong>Faces detected:</strong> ${data.faces_detected}</p>`;
                }
                
                document.getElementById('result').innerHTML = resultHtml;
                
            } catch (error) {
                document.getElementById('result').innerHTML = `
                    <div class="error">
                        <h3>Error</h3>
                        <p>${error.message}</p>
                    </div>
                `;
            }
        });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_upload_page():
    """Serve the photo upload page"""
    return HTML_TEMPLATE

@app.post("/test-face-recognition")
async def test_face_recognition(file: UploadFile = File(...)):
    """Test face recognition with uploaded photo"""
    
    try:
        # Read uploaded file
        contents = await file.read()
        
        # Convert to PIL Image
        image = Image.open(io.BytesIO(contents))
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        # Convert to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Try secure recognition
        result = secure_face_recognizer.recognize_face_from_image(cv_image)
        
        # Count faces detected
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        response_data = {
            "faces_detected": len(faces),
        }
        
        # Handle result properly
        if result and result.get('match_found'):
            response_data["match_found"] = True
            response_data["student_id"] = result['student_id']
            response_data["confidence"] = result['confidence_percentage']
            response_data["confidence_level"] = result['confidence_level']
            response_data["ensemble_score"] = result['ensemble_score']
            response_data["similarities"] = result['similarities']
            response_data["security_checks"] = result['security_checks']
        else:
            response_data["match_found"] = False
            if result:
                response_data["reason"] = result.get('reason', 'Unknown error')
                response_data["confidence_level"] = result.get('confidence_level', 'UNKNOWN')
                response_data["best_rejected_match"] = result.get('best_rejected_match')
            else:
                response_data["reason"] = "No result returned"
                response_data["confidence_level"] = "ERROR"
        
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Face Recognition Test Server...")
    print("📱 Open your browser to: http://localhost:8003")
    print("📸 Upload a photo to test face recognition!")
    uvicorn.run(app, host="0.0.0.0", port=8003)