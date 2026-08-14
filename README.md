# 🏋️ AI Real-time GYM Coach

A Streamlit web application that acts as a virtual gym coach, using your webcam to provide real-time feedback on your exercise form, count reps, and track your workout progress.

## 🌟 Features

- **Real-time Form Analysis**: Get instant feedback on your exercise technique.
- **Multiple Exercise Support**: Currently supports a variety of common exercises.
- **Rep & Set Counting**: Automatically counts your repetitions and tracks completed sets.
- **Workout Planning**: Define your workout plan (exercise, sets, reps) before you start.
- **User Authentication**: A simple login wall to manage user sessions.
- **Live Metrics Display**: See key angles and form status updated in real-time on the dashboard.

### Supported Exercises & Metrics

- **Squats**:
  - Knee Angle
  - Back Angle
  - Depth Status
- **Push-ups**:
  - Elbow Angle
  - Body Alignment
  - Hip Position
- **Biceps Curl (Dumbbell)**:
  - Elbow Angle
  - Shoulder Stability
  - Swing Detection
- **Shoulder Press**:
  - Elbow Angle
  - Arm Extension
  - Back Arch
- **Lunges**:
  - Front Knee Angle
  - Torso Angle
  - Balance Status

## 🛠️ Tech Stack

- **Framework**: [Streamlit](https://streamlit.io/)
- **Language**: Python
- **Computer Vision (assumed)**: OpenCV, MediaPipe
- **Authentication**: Streamlit Authenticator (or a custom implementation)

## 📂 Project Structure

```
AI-REALTIME-GYM-COACH/
├── services/
│   ├── auth/
│   │   └── login_wall.py       # Handles user authentication UI
│   ├── config/
│   │   └── workout_config.py   # Exercise configurations
│   ├── state/
│   │   └── session_default.py  # Manages default session state
│   └── ui/
│       └── style_loader.py     # Loads custom CSS and fonts
├── static/
│   ├── AdobeClean.otf          # Custom font file
│   └── style.css               # Custom CSS styles
├── main.py                     # Main Streamlit application entrypoint
└── README.md                   # This file
```

## 🚀 Getting Started

Follow these instructions to get the project up and running on your local machine.

### Prerequisites

Make sure you have Python 3.8+ installed.

### Installation & Running

1.  **Clone the repository:**
    ```sh
    git clone <your-repository-url>
    cd AI-REALTIME-GYM-COACH
    ```

2.  **Set up environment variables:**
    Create a file named `.env` in the root of the project and add your API keys.
    ```
    # .env
    GROQ_API_KEY="your_groq_api_key_here"
    ```
    This file is ignored by Git to keep your secrets safe.

2.  **Install the required packages:**
    *(Assuming a `requirements.txt` file exists or will be created)*
    ```sh
    pip install -r requirements.txt
    ```

3.  **Run the Streamlit application:**
    ```sh
    streamlit run main.py
    ```

4.  Open your web browser and navigate to `http://localhost:8501`.
