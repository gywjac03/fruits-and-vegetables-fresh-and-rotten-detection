from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
import json
from datetime import datetime, timezone, timedelta

# Malaysian timezone (GMT+8)
malaysia_tz = timezone(timedelta(hours=8))

def get_malaysia_time():
    return datetime.now(malaysia_tz)

class User(db.Model, UserMixin):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    userName = db.Column(db.String(150), unique=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    profile_pic = db.Column(db.String(200), default='default.jpg')
    scan_results = db.relationship('ScanResult', backref='user', lazy=True)
    

class ScanResult(db.Model):
    __tablename__ = 'scan_results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    title = db.Column(db.String(100), default="Unnamed Scan")  # Title for the scan
    image_path = db.Column(db.String(255), nullable=False)  # Path to the saved image
    result_image_path = db.Column(db.String(255), nullable=True)  # Path to the image with detections
    detection_results = db.Column(db.Text, nullable=False)  # JSON string of detections
    created_date = db.Column(db.DateTime(timezone=True), default=get_malaysia_time)
    expected_expiry = db.Column(db.DateTime(timezone=True), nullable=True)  # Expected expiration date
    storage_recommendation = db.Column(db.Text, nullable=True)  # Storage recommendations
    is_rotten = db.Column(db.Boolean, default=False)  # Flag to mark produce as rotten
    marked_rotten_date = db.Column(db.DateTime(timezone=True), nullable=True)  # When the item was marked as rotten
    
    def set_detection_results(self, detection_data):
        """Store detection results as a JSON string"""
        self.detection_results = json.dumps(detection_data)
        
    def get_detection_results(self):
        """Get detection results as a Python object"""
        return json.loads(self.detection_results) if self.detection_results else {}
    
    def __repr__(self):
        return f"<ScanResult {self.id} by user {self.user_id} on {self.created_date}>"


