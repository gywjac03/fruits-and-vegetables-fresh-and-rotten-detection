# Fresh Detection Web Application

A Flask-based web application for detecting produce freshness using YOLO object detection model.

## Features

- User authentication system (register, login, profile management)
- Upload images or capture with camera for freshness detection
- Object detection for produce using YOLO model
- Track scan history and results
- Mark items as rotten
- Storage recommendations based on detection results
- Responsive web interface

## Project Structure

```
freshness-detection/
├── main.py                 # Main entry point
├── best.pt                 # YOLO model weights file
├── requirements.txt        # Python dependencies
├── instance/               # SQLite database directory
│   └── database.db         # SQLite database file
└── website/                # Application package
    ├── __init__.py         # Flask application factory
    ├── app.py              # Object detection logic and routes
    ├── auth.py             # Authentication routes
    ├── views.py            # Main web routes
    ├── models.py           # Database models
    ├── utils.py            # Utility functions
    ├── static/             # Static files (CSS, JS, images)
    │   ├── uploads/        # Uploaded images
    │   ├── results/        # Detection result images
    │   └── saved_results/  # Saved detection results
    └── templates/          # HTML templates
```

## Setup and Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Make sure the YOLO model file (`best.pt`) is in the project root directory
4. Run the application:
   ```
   python main.py
   ```
5. Access the application at http://127.0.0.1:5000/

## Technologies Used

- Flask: Web framework
- SQLAlchemy: ORM for database interactions
- Flask-Login: User authentication
- YOLO (You Only Look Once): Object detection model
- OpenCV: Image processing
- SQLite: Database

## Requirements

See requirements.txt for the full list of dependencies.

## Development Mode

The application runs in debug mode by default, which enables:
- Auto-reload on code changes
- Detailed error pages
- Debug logging

For production deployment, set `debug=False` in main.py.

## Repository Name

fruits-and-vegetables-fresh-and-rotten-detection
