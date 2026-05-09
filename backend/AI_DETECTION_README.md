# AI-Based Cheating Detection System

## Overview

This AI detection system provides real-time cheating detection for the online proctoring system using computer vision and machine learning techniques. It integrates seamlessly with the existing webcam pipeline to monitor student behavior during exams.

## Features

### Detection Capabilities

1. **Face Detection**
   - No face detected
   - Multiple faces in frame
   - Face visibility tracking

2. **Head Pose Estimation**
   - Looking away detection
   - Head movement tracking
   - Excessive movement analysis

3. **Behavioral Analysis**
   - Suspicious object detection
   - Abnormal behavior patterns
   - Compliance scoring

### Real-time Performance

- **Frame Processing**: Optimized for 10 FPS processing
- **Memory Management**: Efficient resource usage
- **Scalability**: Supports multiple concurrent sessions
- **Alert System**: Real-time WebSocket notifications

## Architecture

### Core Components

```
app/
├── models/
│   └── ai_detection.py          # AI detection data models
├── services/
│   ├── ai_detection.py          # Main AI detection service
│   └── performance.py           # Performance monitoring
├── routes/
│   └── ai_detection.py          # AI detection API endpoints
└── core/
    └── ws.py                    # WebSocket management
```

### Data Flow

1. **Frame Input**: Webcam frames received via WebSocket
2. **AI Processing**: Face detection and analysis
3. **Event Generation**: Suspicious activity detection
4. **Alert Broadcasting**: Real-time notifications
5. **Data Storage**: Results stored in MongoDB

## Installation

### Dependencies

Add these packages to your `requirements.txt`:

```txt
opencv-python
mediapipe
numpy
pillow
psutil  # For performance monitoring
```

### Installation Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install additional system dependencies if needed
# On Ubuntu/Debian:
sudo apt-get update
sudo apt-get install python3-opencv
```

## Configuration

### AI Detection Settings

```python
from app.models.ai_detection import AIDetectionConfig

config = AIDetectionConfig(
    # Enable/disable features
    enable_face_detection=True,
    enable_head_pose_estimation=True,
    enable_multiple_face_detection=True,
    enable_looking_away_detection=True,
    enable_head_movement_tracking=True,
    
    # Detection thresholds
    no_face_threshold_seconds=3.0,
    multiple_faces_threshold=2,
    looking_away_threshold_degrees=45.0,
    head_movement_threshold_pixels=50.0,
    head_movement_window_seconds=5.0,
    
    # Performance settings
    max_processing_fps=10,
    frame_skip_count=2,
    confidence_threshold=0.5,
    
    # Alert settings
    auto_alert_threshold=70,
    event_cooldown_seconds=2.0
)
```

## API Endpoints

### Configuration Management

```http
POST /ai/config
Content-Type: application/json
Authorization: Bearer <token>

{
  "enable_face_detection": true,
  "confidence_threshold": 0.7,
  "auto_alert_threshold": 80
}
```

```http
GET /ai/config
Authorization: Bearer <token>
```

### Frame Analysis

```http
POST /ai/analyze-frame
Content-Type: multipart/form-data
Authorization: Bearer <token>

session_id: "session_123"
student_id: "student_456"
exam_id: "exam_789"
frame_data: <binary_jpeg_data>
```

### Analytics

```http
GET /ai/analytics/{session_id}
Authorization: Bearer <token>
```

### Alert Management

```http
GET /ai/alerts?session_id=session_123&severity_threshold=50
Authorization: Bearer <token>

POST /ai/alerts/{alert_id}/acknowledge
Authorization: Bearer <token>
```

## WebSocket Integration

### AI Alerts WebSocket

```javascript
// Connect to AI alerts WebSocket
const ws = new WebSocket('ws://localhost:8000/ai/ws/alerts');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'ai_alert') {
        console.log('AI Alert:', data);
        // Handle alert in UI
        showSuspiciousActivityAlert(data);
    }
};
```

### Alert Message Format

```json
{
    "type": "ai_alert",
    "session_id": "session_123",
    "student_id": "student_456",
    "exam_id": "exam_789",
    "alert_type": "looking_away",
    "severity": 75,
    "confidence": 0.85,
    "message": "Student looking away from screen",
    "details": {
        "head_pose": {"yaw": 52.3, "pitch": 0.0, "roll": 0.0},
        "threshold": 45.0
    },
    "timestamp": "2024-01-15T10:30:45.123Z",
    "suspicious_score": 82
}
```

## Performance Optimization

### Monitoring

The system includes built-in performance monitoring:

```python
from app.services.performance import get_performance_monitor

monitor = get_performance_monitor()
metrics = monitor.get_current_metrics()
suggestions = monitor.get_optimization_suggestions()
```

### Optimization Strategies

1. **Frame Skipping**: Process every Nth frame
2. **Resolution Reduction**: Lower input resolution
3. **Feature Toggling**: Disable non-essential features
4. **Threshold Adjustment**: Increase detection thresholds

### Performance Metrics

- **Processing Time**: Milliseconds per frame
- **FPS**: Frames processed per second
- **Memory Usage**: RAM consumption in MB
- **CPU Usage**: Processor utilization percentage

## Database Schema

### AI Detections Collection

```javascript
{
    "_id": ObjectId,
    "session_id": "string",
    "student_id": "string", 
    "exam_id": "string",
    "frame_timestamp": ISODate,
    "face_detection": {
        "face_count": 1,
        "face_rects": [[x, y, w, h]],
        "confidence": 0.95,
        "head_pose": {"yaw": 0.0, "pitch": 0.0, "roll": 0.0}
    },
    "ai_events": [
        {
            "detection_type": "looking_away",
            "confidence": 0.85,
            "severity": 40,
            "details": {...},
            "timestamp": ISODate
        }
    ],
    "processing_time_ms": 45.2,
    "suspicious_score": 75
}
```

## Integration Guide

### Frontend Integration

1. **Connect to AI Alerts WebSocket**
2. **Handle Real-time Alerts**
3. **Display Suspicious Activity**
4. **Update Compliance Score**

### Backend Integration

1. **Initialize AI Service**
2. **Process Webcam Frames**
3. **Store Detection Results**
4. **Broadcast Alerts**

## Testing

### Unit Tests

```bash
# Run AI detection tests
python -m pytest tests/test_ai_detection.py

# Run performance tests
python -m pytest tests/test_performance.py
```

### Integration Tests

```bash
# Test full pipeline
python -m pytest tests/test_ai_integration.py
```

## Troubleshooting

### Common Issues

1. **MediaPipe Initialization Error**
   - Ensure proper dependencies installed
   - Check system permissions for camera access

2. **High Memory Usage**
   - Reduce frame processing frequency
   - Enable frame skipping
   - Lower input resolution

3. **Slow Processing**
   - Check CPU usage
   - Optimize detection thresholds
   - Reduce enabled features

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('app.services.ai_detection').setLevel(logging.DEBUG)
```

## Security Considerations

1. **Data Privacy**: Frame data processed in memory only
2. **Storage Limits**: Automatic cleanup of old data
3. **Access Control**: JWT-based authentication
4. **Network Security**: WebSocket connection validation

## Future Enhancements

1. **Advanced Object Detection**: YOLO integration
2. **Behavioral Biometrics**: Typing patterns analysis
3. **Voice Analysis**: Audio monitoring capabilities
4. **Machine Learning**: Custom model training

## Support

For issues and questions:
- Check system logs for error messages
- Verify dependencies are properly installed
- Ensure MongoDB connection is active
- Review configuration settings
