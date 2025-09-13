#!/usr/bin/env python3
"""
SECURE Face Recognition Test Interface - HIGH SECURITY MODE
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
import cv2
import numpy as np
import io
from PIL import Image
from typing import Dict, Any
from backend.secure_face_recognition import secure_face_recognizer

app = FastAPI(title="🔒 SECURE Face Recognition Test")

# Secure HTML template
SECURE_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🔒 SECURE Face Recognition Test</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 50px auto; padding: 20px; background: #f8f9fa; }
        .header { background: #dc3545; color: white; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px; }
        .upload-area { border: 3px dashed #dc3545; padding: 40px; text-align: center; margin: 20px 0; background: white; border-radius: 10px; }
        .result { margin: 20px 0; padding: 20px; border-radius: 10px; }
        .success { background-color: #d4edda; color: #155724; border: 2px solid #c3e6cb; }
        .error { background-color: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }
        .warning { background-color: #fff3cd; color: #856404; border: 2px solid #ffeaa7; }
        .info { background-color: #d1ecf1; color: #0c5460; border: 2px solid #bee5eb; }
        button { background: #dc3545; color: white; border: none; padding: 15px 30px; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold; }
        button:hover { background: #c82333; }
        .security-badge { background: #dc3545; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold; font-size: 12px; }
        details { margin-top: 10px; }
        summary { cursor: pointer; font-weight: bold; }
        ul { margin: 10px 0; }
        .metric { margin: 5px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ SECURE FACE RECOGNITION SYSTEM</h1>
        <span class="security-badge">HIGH SECURITY MODE ACTIVE</span>
    </div>
    
    <div class="warning">
        <h3>⚠️ SECURITY NOTICE:</h3>
        <ul>
            <li><strong>85% Minimum Confidence</strong> required for acceptance</li>
            <li><strong>Multiple Validation Metrics</strong> must agree</li>
            <li><strong>Face Quality Checks</strong> enforced</li>
            <li><strong>Unknown Persons REJECTED</strong> - No false positives allowed</li>
            <li><strong>Database:</strong> 5 authorized students only</li>
        </ul>
    </div>
    
    <form id="uploadForm" enctype="multipart/form-data">
        <div class="upload-area">
            <h3>🔍 Test Face Recognition Security</h3>
            <input type="file" id="photoFile" name="file" accept="image/*" required>
            <br><br>
            <button type="submit">🔒 VALIDATE IDENTITY</button>
        </div>
    </form>
    
    <div id="result"></div>
    
    <script>
        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData();
            const fileInput = document.getElementById('photoFile');
            formData.append('file', fileInput.files[0]);
            
            document.getElementById('result').innerHTML = '<div class="info">🔍 Running security validation...</div>';
            
            try {
                const response = await fetch('/secure-validation', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                let resultHtml = '';
                if (data.match_found) {
                    resultHtml = `
                        <div class="success">
                            <h3>✅ IDENTITY VERIFIED - ACCESS GRANTED</h3>
                            <p><strong>Student ID:</strong> ${data.student_id}</p>
                            <p><strong>Confidence:</strong> ${data.confidence.toFixed(1)}%</p>
                            <p><strong>Security Level:</strong> <span class="security-badge">${data.confidence_level}</span></p>
                            <p><strong>Ensemble Score:</strong> ${data.ensemble_score.toFixed(3)}</p>
                            <details>
                                <summary>🔒 Security Validation Details</summary>
                                <div class="metric"><strong>Similarity Metrics:</strong></div>
                                <ul>
                                    <li>Cosine Similarity: ${data.similarities.cosine.toFixed(3)}</li>
                                    <li>Euclidean Similarity: ${data.similarities.euclidean.toFixed(3)}</li>
                                    <li>Correlation: ${data.similarities.correlation.toFixed(3)}</li>
                                    <li>Chi-square: ${data.similarities.chi_square.toFixed(3)}</li>
                                </ul>
                                <div class="metric"><strong>Security Checks:</strong></div>
                                <ul>
                                    <li>High Confidence: ${data.security_checks.high_confidence ? '✅' : '❌'}</li>
                                    <li>Cosine Check: ${data.security_checks.cosine_check ? '✅' : '❌'}</li>
                                    <li>Correlation Check: ${data.security_checks.correlation_check ? '✅' : '❌'}</li>
                                    <li>Consistent Metrics: ${data.security_checks.consistent_metrics ? '✅' : '❌'}</li>
                                </ul>
                            </details>
                        </div>
                    `;
                } else {
                    resultHtml = `
                        <div class="error">
                            <h3>🚫 ACCESS DENIED - IDENTITY NOT VERIFIED</h3>
                            <p><strong>Reason:</strong> ${data.reason}</p>
                            <p><strong>Security Status:</strong> <span class="security-badge">${data.confidence_level}</span></p>
                            <p style="color: #dc3545; font-weight: bold; font-size: 18px;">⚠️ UNAUTHORIZED PERSON DETECTED</p>
                            ${data.best_rejected_match ? `
                                <details>
                                    <summary>Best Rejected Match (Still Insufficient)</summary>
                                    <p>Student ${data.best_rejected_match.student_id}: ${data.best_rejected_match.confidence_percentage.toFixed(1)}% (${data.best_rejected_match.confidence_level})</p>
                                    <p style="color: #dc3545;">This person does not meet security requirements!</p>
                                </details>
                            ` : '<p><strong>No similar faces found in authorized database</strong></p>'}
                        </div>
                    `;
                }
                
                if (data.faces_detected !== undefined) {
                    resultHtml += `<p><strong>Faces Detected:</strong> ${data.faces_detected}</p>`;
                }
                
                document.getElementById('result').innerHTML = resultHtml;
                
            } catch (error) {
                document.getElementById('result').innerHTML = `
                    <div class="error">
                        <h3>🔥 System Error</h3>
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
async def get_secure_page():
    """Serve the secure face validation page"""
    return SECURE_HTML_TEMPLATE

@app.post("/secure-validation")
async def secure_face_validation(file: UploadFile = File(...)):
    """Secure face validation with strict security measures"""
    
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
        
        # Secure recognition
        result = secure_face_recognizer.recognize_face_from_image(cv_image)
        
        # Count faces detected using OpenCV directly
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        import cv2
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        # Prepare secure response
        response: Dict[str, Any] = {
            "faces_detected": len(faces),
        }
        
        # Handle result
        if result and result.get('match_found'):
            response.update({
                "match_found": True,
                "student_id": result['student_id'],
                "confidence": result['confidence_percentage'],
                "confidence_level": result['confidence_level'],
                "ensemble_score": result['ensemble_score'],
                "similarities": result['similarities'],
                "security_checks": result['security_checks']
            })
        else:
            response.update({
                "match_found": False,
                "reason": result.get('reason', 'Security validation failed') if result else "No result returned",
                "confidence_level": result.get('confidence_level', 'ERROR') if result else "ERROR"
            })
            
            # Include best rejected match if available
            if result and result.get('best_rejected_match'):
                response["best_rejected_match"] = result['best_rejected_match']
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🔒 Starting SECURE Face Recognition Validation Server...")
    print("🛡️ HIGH SECURITY MODE - False positives BLOCKED")
    print("📱 Open your browser to: http://localhost:8004")
    print("⚠️ Only authorized students will be recognized!")
    uvicorn.run(app, host="0.0.0.0", port=8004)