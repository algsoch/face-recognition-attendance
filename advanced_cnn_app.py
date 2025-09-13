#!/usr/bin/env python3
"""
Advanced CNN Face Recognition Web Interface
Professional system with detailed student information display
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
import cv2
import numpy as np
import io
from PIL import Image
from typing import Dict, Any
from backend.advanced_cnn_recognition import advanced_cnn_recognizer
import sqlite3

app = FastAPI(title="🧠 Advanced CNN Face Recognition System")

# Professional HTML template with detailed display
ADVANCED_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🧠 Advanced CNN Face Recognition</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            max-width: 1200px; 
            margin: 20px auto; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        .header { 
            background: linear-gradient(135deg, #667eea, #764ba2); 
            color: white; 
            padding: 25px; 
            border-radius: 15px; 
            text-align: center; 
            margin-bottom: 30px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }
        
        .upload-area { 
            border: 3px dashed #667eea; 
            padding: 40px; 
            text-align: center; 
            margin: 20px 0; 
            background: #f8f9ff; 
            border-radius: 15px;
            transition: all 0.3s ease;
        }
        
        .upload-area:hover {
            border-color: #764ba2;
            background: #f0f2ff;
        }
        
        .result { 
            margin: 30px 0; 
            padding: 25px; 
            border-radius: 15px; 
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .success { 
            background: linear-gradient(135deg, #d4edda, #c3e6cb); 
            color: #155724; 
            border: 2px solid #28a745; 
        }
        
        .error { 
            background: linear-gradient(135deg, #f8d7da, #f5c6cb); 
            color: #721c24; 
            border: 2px solid #dc3545; 
        }
        
        .info { 
            background: linear-gradient(135deg, #d1ecf1, #bee5eb); 
            color: #0c5460; 
            border: 2px solid #17a2b8; 
        }
        
        button { 
            background: linear-gradient(135deg, #667eea, #764ba2); 
            color: white; 
            border: none; 
            padding: 15px 30px; 
            border-radius: 10px; 
            cursor: pointer; 
            font-size: 16px; 
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        }
        
        .student-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            border-left: 5px solid #667eea;
        }
        
        .student-photo {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            object-fit: cover;
            border: 4px solid #667eea;
            margin: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .details-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .detail-item {
            background: #f8f9ff;
            padding: 15px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }
        
        .detail-label {
            font-weight: bold;
            color: #667eea;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .detail-value {
            font-size: 16px;
            color: #333;
            margin-top: 5px;
        }
        
        .confidence-meter {
            background: #e9ecef;
            border-radius: 10px;
            height: 20px;
            margin: 10px 0;
            overflow: hidden;
        }
        
        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            border-radius: 10px;
            transition: width 0.5s ease;
        }
        
        .tech-details {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            border: 1px solid #dee2e6;
        }
        
        .similarity-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            margin: 15px 0;
        }
        
        .similarity-item {
            text-align: center;
            padding: 10px;
            background: white;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }
        
        details {
            margin: 15px 0;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            overflow: hidden;
        }
        
        summary {
            padding: 15px;
            background: #f8f9fa;
            cursor: pointer;
            font-weight: bold;
            color: #667eea;
        }
        
        summary:hover {
            background: #e9ecef;
        }
        
        .details-content {
            padding: 20px;
        }
        
        .badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .badge-high { background: #28a745; color: white; }
        .badge-medium { background: #ffc107; color: #000; }
        .badge-low { background: #dc3545; color: white; }
        .badge-cnn { background: #667eea; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 Advanced CNN Face Recognition System</h1>
            <p>State-of-the-art deep learning powered face recognition</p>
            <span class="badge badge-cnn">CNN POWERED</span>
        </div>
        
        <div class="info">
            <h3>🚀 System Features:</h3>
            <ul>
                <li><strong>CNN Deep Learning Models</strong> - VGG-Face, FaceNet, ArcFace</li>
                <li><strong>Multi-Scale Feature Extraction</strong> - Advanced facial pattern analysis</li>
                <li><strong>Adaptive Thresholds</strong> - 65% verification, 75% high confidence</li>
                <li><strong>Comprehensive Student Profiles</strong> - Complete database integration</li>
                <li><strong>Real-time Recognition</strong> - Instant face matching and verification</li>
            </ul>
        </div>
        
        <form id="uploadForm" enctype="multipart/form-data">
            <div class="upload-area">
                <h3>📸 Upload Photo for CNN Recognition</h3>
                <input type="file" id="photoFile" name="file" accept="image/*" required>
                <br><br>
                <button type="submit">🧠 ANALYZE WITH CNN</button>
            </div>
        </form>
        
        <div id="result"></div>
    </div>
    
    <script>
        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData();
            const fileInput = document.getElementById('photoFile');
            formData.append('file', fileInput.files[0]);
            
            document.getElementById('result').innerHTML = '<div class="info">🧠 Running CNN analysis...</div>';
            
            try {
                const response = await fetch('/cnn-recognition', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                let resultHtml = '';
                if (data.match_found) {
                    const student = data.student_details;
                    const confidence = data.confidence;
                    const level = data.confidence_level;
                    
                    resultHtml = `
                        <div class="success">
                            <h2>✅ STUDENT IDENTIFIED</h2>
                            
                            <div class="student-card">
                                <div style="display: flex; align-items: center; flex-wrap: wrap;">
                                    <img src="${student.photo_url}" alt="${student.name}" class="student-photo" onerror="this.style.display='none'">
                                    <div style="flex: 1; min-width: 300px;">
                                        <h2 style="color: #667eea; margin: 0;">${student.name}</h2>
                                        <p style="font-size: 18px; color: #666; margin: 5px 0;">Roll: ${student.roll_number}</p>
                                        <span class="badge badge-${level.toLowerCase()}">${level} CONFIDENCE</span>
                                        <span class="badge badge-cnn">${data.model_used}</span>
                                    </div>
                                </div>
                                
                                <div class="confidence-meter">
                                    <div class="confidence-fill" style="width: ${confidence}%"></div>
                                </div>
                                <p style="text-align: center; margin: 5px 0;"><strong>Confidence: ${confidence.toFixed(1)}%</strong></p>
                                
                                <div class="details-grid">
                                    <div class="detail-item">
                                        <div class="detail-label">Class & Section</div>
                                        <div class="detail-value">${student.class_name} - ${student.section}</div>
                                    </div>
                                    <div class="detail-item">
                                        <div class="detail-label">Branch</div>
                                        <div class="detail-value">${student.branch}</div>
                                    </div>
                                    <div class="detail-item">
                                        <div class="detail-label">Student Status</div>
                                        <div class="detail-value">${student.is_active ? '🟢 Active' : '🔴 Inactive'}</div>
                                    </div>
                                    <div class="detail-item">
                                        <div class="detail-label">Enrollment Date</div>
                                        <div class="detail-value">${new Date(student.created_at).toLocaleDateString()}</div>
                                    </div>
                                </div>
                            </div>
                            
                            <details>
                                <summary>🔬 Technical Analysis Details</summary>
                                <div class="details-content">
                                    <div class="tech-details">
                                        <h4>CNN Model Information</h4>
                                        <p><strong>Model:</strong> ${data.model_used}</p>
                                        <p><strong>Feature Vector Length:</strong> ${data.encoding_length}</p>
                                        <p><strong>Similarity Score:</strong> ${data.similarity_score.toFixed(4)}</p>
                                    </div>
                                    
                                    <h4>Similarity Scores with All Students</h4>
                                    <div class="similarity-grid">
                                        ${Object.entries(data.all_similarities).map(([id, sim]) => `
                                            <div class="similarity-item ${id === data.student_id ? 'detail-item' : ''}">
                                                <strong>ID ${id}</strong><br>
                                                ${(sim * 100).toFixed(1)}%
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                            </details>
                        </div>
                    `;
                } else {
                    resultHtml = `
                        <div class="error">
                            <h3>❌ NO MATCH FOUND</h3>
                            <p><strong>Reason:</strong> ${data.reason}</p>
                            <p><strong>Confidence:</strong> ${data.confidence.toFixed(1)}%</p>
                            
                            ${data.best_rejected_match ? `
                                <div class="tech-details">
                                    <h4>Best Rejected Match</h4>
                                    <p><strong>Student ID:</strong> ${data.best_rejected_match.student_id}</p>
                                    <p><strong>Similarity:</strong> ${(data.best_rejected_match.similarity * 100).toFixed(1)}%</p>
                                    ${data.best_rejected_match.student_details ? `
                                        <p><strong>Name:</strong> ${data.best_rejected_match.student_details.name}</p>
                                        <p><strong>Roll:</strong> ${data.best_rejected_match.student_details.roll_number}</p>
                                    ` : ''}
                                    <p style="color: #dc3545;"><strong>⚠️ Below verification threshold</strong></p>
                                </div>
                            ` : ''}
                            
                            ${data.all_similarities ? `
                                <details>
                                    <summary>📊 All Similarity Scores</summary>
                                    <div class="similarity-grid">
                                        ${Object.entries(data.all_similarities).map(([id, sim]) => `
                                            <div class="similarity-item">
                                                <strong>ID ${id}</strong><br>
                                                ${(sim * 100).toFixed(1)}%
                                            </div>
                                        `).join('')}
                                    </div>
                                </details>
                            ` : ''}
                        </div>
                    `;
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
async def get_advanced_page():
    """Serve the advanced CNN recognition page"""
    return ADVANCED_HTML_TEMPLATE

@app.post("/cnn-recognition")
async def cnn_face_recognition(file: UploadFile = File(...)):
    """Advanced CNN face recognition with comprehensive student details"""
    
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
        
        # CNN recognition
        result = advanced_cnn_recognizer.recognize_face_from_image(cv_image)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")

@app.get("/system-stats")
async def get_system_stats():
    """Get CNN system statistics"""
    return advanced_cnn_recognizer.get_statistics()

@app.post("/rebuild-cnn-database")
async def rebuild_cnn_database():
    """Rebuild CNN face database from student records"""
    try:
        # Get students from database
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        cursor.execute('SELECT student_id, name, photo_url FROM students WHERE photo_url IS NOT NULL ORDER BY student_id')
        students = cursor.fetchall()
        conn.close()
        
        results = {
            'total_students': len(students),
            'successful': 0,
            'failed': 0,
            'details': []
        }
        
        for student_id, name, photo_url in students:
            success = advanced_cnn_recognizer.extract_and_save_face(photo_url, str(student_id))
            if success:
                results['successful'] += 1
                results['details'].append(f"✅ {name} (ID: {student_id})")
            else:
                results['failed'] += 1
                results['details'].append(f"❌ {name} (ID: {student_id})")
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rebuilding database: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🧠 Starting Advanced CNN Face Recognition System...")
    print("🚀 Deep Learning Models: VGG-Face, FaceNet, ArcFace")
    print("📱 Open your browser to: http://localhost:8005")
    print("✨ Professional-grade face recognition with detailed student profiles!")
    uvicorn.run(app, host="0.0.0.0", port=8005)