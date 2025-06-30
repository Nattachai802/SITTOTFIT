# SIT TO FIT

## Project Overview
SIT TO FIT is a project designed to analyze and improve ergonomic sitting postures. It helps individuals identify poor sitting habits and offers recommendations to improve posture for better comfort and health. The system leverages advanced technologies such as computer vision, machine learning, and ergonomic analysis to provide users with valuable insights.

## Features
- **Sitting Posture Detection**: Analyzes the sitting posture using real-time video and provides feedback.
- **Posture Recommendations**: Provides advice to improve sitting habits based on detected posture.
- **User Dashboard**: Displays posture analysis results and track improvements over time.
- **Camera Integration**: Utilizes YOLOv8 and MediaPipe for detecting and analyzing sitting postures.
  
## Technologies Used
- **Python**: The primary programming language for backend development.
- **Django**: Web framework used for building the backend of the application.
- **OpenCV**: Computer vision library used for video processing and image analysis.
- **YOLOv8**: Used for object detection to identify persons and chairs in real-time.
- **MediaPipe**: Used for pose landmarks to detect body position and posture.
- **SQLite**: Database used to store user data and posture analysis results.
  
## Setup and Installation

### Prerequisites
- Python 3.x
- Django 3.x or higher
- OpenCV
- YOLOv8 (for posture detection)
- MediaPipe

### Installation Steps
1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/SITTOFIT.git
   cd SITTOFIT
