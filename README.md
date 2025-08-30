# SIT TO FIT

## Project Overview
SIT TO FIT is an ergonomic posture analysis system designed to help individuals improve their sitting habits. It enables users to identify poor sitting postures and provides practical recommendations to enhance comfort, reduce the risk of injury, and promote long-term health and well-being.

The system integrates advanced Computer Vision, Machine Learning, and Ergonomic Analysis to evaluate sitting posture in real time. By detecting body keypoints and applying mathematical models, it delivers accurate posture assessments using:

- Cosine Equation: Calculates sitting angles

- Gaussian 2MF Equation: Converts results into recommendation scores

- These scores reflect the appropriateness of a user’s sitting posture and generate tailored guidance for improvement based on ergonomic principles.

The web application is developed using Python and the Django Framework for both frontend and backend, ensuring flexibility, efficiency, and reliable performance.

## Features
- **Sitting Posture Detection**: Analyzes the sitting posture using real-time video and provides feedback.
- **Posture Recommendations**: Provides advice to improve sitting habits based on detected posture.
- **User Dashboard**: Displays posture analysis results and track improvements over time.
- **Camera Integration**: Utilizes YOLOv8 and MediaPipe for detecting and analyzing sitting postures.


## Workflow – Posture Estimation System  

The workflow of **SIT TO FIT** transforms webcam input into ergonomic insights through the following steps:  

1. **Camera Input (WebRTC)**  
   - Captures live video stream from the user’s webcam.  

2. **Preprocessing with MediaPipe + YOLOv8**  
   - Adjusts brightness/contrast automatically.  
   - Detects and extracts body keypoints.  

3. **Noise Filtering (Kalman Filter 2D)**  
   - Predicts and corrects noisy keypoint data.  

4. **Angle Calculation (Cosine Similarity)**  
   - Computes joint angles using the formula:  
     ```
     cos(θ) = (a · b) / (|a||b|)
     ```  

5. **Geometric Heuristic**  
   - Defines thresholds to classify posture correctness.  

6. **Gaussian 2-Membership Function**  
   - Converts deviation into a **posture recommendation score**.  

7. **Posture Risk Prediction (LightGBM)**  
   - Uses accumulated posture data to assess long-term spinal health risks.  

8. **Feedback & Notifications**  
   - Provides suggestions for posture correction.  
   - Sends reminders to stretch and maintain healthy sitting behavior.  
  
## 🛠️ Tech Stack  
- **Frontend & Backend**: Python, Django  
- **Computer Vision**: MediaPipe, YOLOv8  
- **Mathematical Models**: Cosine Similarity, Gaussian 2MF  
- **Noise Filtering**: Kalman Filter  
- **Machine Learning**: LightGBM  
- **Web Integration**: WebRTC (camera input) 
  
### Prerequisites
- Python 3.x
- Django 3.x or higher
- OpenCV
- YOLOv8 (for posture detection)
- MediaPipe
