# Fruits and Vegetables Fresh and Rotten Detection Web App

This project is a web application for detecting the freshness of fruits and vegetables using deep learning. Users can upload images to assess whether produce is fresh or rotten, view scan history, and get storage recommendations.

## Features

- Upload images of fruits and vegetables for freshness detection
- User authentication (register, login, profile)
- Scan history and saved results
- Storage recommendations and shelf life info
- Modern, responsive UI

## Tech Stack

- Python 3.12
- Flask (backend web framework)
- SQLite (database)
- PyTorch (deep learning model)
- Docker (containerization)

## Project Structure

```
.
├── main.py                # Entry point for the app
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker build instructions
├── best.pt                # Trained PyTorch model
├── instance/
│   └── database.db        # SQLite database
└── website/
    ├── app.py             # Flask app
    ├── auth.py            # Authentication routes
    ├── models.py          # Database models
    ├── utils.py           # Utility functions
    ├── views.py           # Main routes
    ├── static/            # Static files (images, uploads, results)
    └── templates/         # HTML templates
```
