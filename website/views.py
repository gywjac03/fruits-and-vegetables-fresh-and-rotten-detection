from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import current_user, login_required
from .models import ScanResult
from . import db
import json
import os
from datetime import datetime, timezone, timedelta

# Create a Malaysia timezone object (UTC+8)
malaysia_tz = timezone(timedelta(hours=8))

# Function to get current time in Malaysia timezone
def get_malaysia_time():
    return datetime.now(malaysia_tz)

# Function to convert datetime to Malaysia time if it's naive
def to_malaysia_time(dt):
    if dt.tzinfo is None:  # Naive datetime
        # Assume it's UTC and convert to Malaysia time
        return dt.replace(tzinfo=timezone.utc).astimezone(malaysia_tz)
    return dt.astimezone(malaysia_tz)  # Already timezone-aware

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
def home():
    recent_results = []
    now = get_malaysia_time()  # Get current date and time in Malaysia timezone
    
    if current_user.is_authenticated:
        # Retrieve the user's most recent scan results (limit to 4)
        scan_results = ScanResult.query.filter_by(
            user_id=current_user.id
        ).order_by(
            ScanResult.created_date.desc()
        ).limit(4).all()
        
        for scan in scan_results:
            # Get the detection data
            detection_data = scan.get_detection_results()
            
            # Count objects by class
            detection_counts = {}
            if 'detections' in detection_data:
                for detection in detection_data['detections']:
                    class_name = detection.get('class', 'Unknown')
                    detection_counts[class_name] = detection_counts.get(class_name, 0) + 1
            
            # Format the summary
            summary = ", ".join([f"{count} {name}" for name, count in detection_counts.items()])
            
            # Process image paths
            result_image_path = None
            if scan.result_image_path:
                result_image_path = scan.result_image_path.replace('\\', '/')
                
                if 'website/static/' in result_image_path:
                    result_image_path = '/static/' + result_image_path.split('website/static/')[1]
                elif not result_image_path.startswith('/static/'):
                    if result_image_path.startswith('/'):
                        result_image_path = '/static' + result_image_path
                    else:
                        result_image_path = '/static/' + result_image_path
                
                # Special handling for saved_results paths
                if 'saved_results' in result_image_path and '/' in result_image_path:
                    filename = result_image_path.split('/')[-1]
                    result_image_path = f'/static/saved_results/{filename}'
            
            # Ensure created_date is timezone-aware
            scan_date = scan.created_date
            if scan_date and scan_date.tzinfo is None:
                scan_date = scan_date.replace(tzinfo=malaysia_tz)
            else:
                scan_date = to_malaysia_time(scan.created_date)
            
            # Ensure expected_expiry is timezone-aware
            expected_expiry = None
            if scan.expected_expiry:
                if scan.expected_expiry.tzinfo is None:
                    expected_expiry = scan.expected_expiry.replace(tzinfo=malaysia_tz)
                else:
                    expected_expiry = to_malaysia_time(scan.expected_expiry)
            
            # Add to results list
            recent_results.append({
                'id': scan.id,
                'title': scan.title,
                'date': scan_date,
                'created_date': scan_date,  # Adding created_date to match the template
                'summary': summary if summary else "No objects detected",
                'result_image_path': result_image_path,
                'detection_count': sum(detection_counts.values()),
                'expected_expiry': expected_expiry,
                'storage_recommendation': scan.storage_recommendation,
                'is_rotten': scan.is_rotten
            })
    
    return render_template("home.html", user=current_user, recent_results=recent_results, now=now)

@views.route('/about')
def about():
    return render_template("about.html", user=current_user)

@views.route('/how-it-works')
def how_it_works():
    return render_template("how_it_works.html", user=current_user)

@views.route('/profile')
@login_required
def profile():
    return render_template("profile.html", user=current_user)

@views.route('/scan')
def scan():
    return render_template("scan.html", user=current_user)

@views.route('/my-scans')
@login_required
def my_scans():
    user_id = current_user.id
    # Get date filter from query parameter
    filter_date = request.args.get('date', None)
    
    # Get all scan results for this user, sorted by date (newest first)
    query = ScanResult.query.filter_by(user_id=user_id).order_by(ScanResult.created_date.desc())
    
    # If date filter is provided, filter by date
    if filter_date:
        try:
            # Parse the date string to a datetime object
            filter_date_obj = datetime.strptime(filter_date, '%Y-%m-%d')
            
            # Create start and end of the day for comparison
            start_of_day = filter_date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = filter_date_obj.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Make start_of_day and end_of_day timezone-aware if they're not
            if start_of_day.tzinfo is None:
                start_of_day = start_of_day.replace(tzinfo=malaysia_tz)
            if end_of_day.tzinfo is None:
                end_of_day = end_of_day.replace(tzinfo=malaysia_tz)
            
            # Filter query to only include scans from this day
            query = query.filter(ScanResult.created_date >= start_of_day, ScanResult.created_date <= end_of_day)
            
        except ValueError:
            # If date is invalid, ignore the filter
            flash('Invalid date format. Showing all scans.', 'warning')
    
    # Get the results and ensure all have appropriate timezone
    scan_results = query.all()
    
    # Process each result for display
    for result in scan_results:
        # Ensure created_date is timezone-aware
        if result.created_date and result.created_date.tzinfo is None:
            result.created_date = result.created_date.replace(tzinfo=malaysia_tz)
        
        # Ensure expected_expiry is timezone-aware
        if result.expected_expiry and result.expected_expiry.tzinfo is None:
            result.expected_expiry = result.expected_expiry.replace(tzinfo=malaysia_tz)
        
        # Process image paths
        if result.result_image_path:
            result.result_image_path = result.result_image_path.replace('\\', '/')
            
            # Correctly format paths for web
            if 'website/static/' in result.result_image_path:
                result.result_image_path = '/static/' + result.result_image_path.split('website/static/')[1]
            elif not result.result_image_path.startswith('/static/'):
                if result.result_image_path.startswith('/'):
                    result.result_image_path = '/static' + result.result_image_path
                else:
                    result.result_image_path = '/static/' + result.result_image_path
            
            # Special handling for saved_results paths
            if 'saved_results' in result.result_image_path and '/' in result.result_image_path:
                filename = result.result_image_path.split('/')[-1]
                result.result_image_path = f'/static/saved_results/{filename}'
        
        # Process original image path
        if result.image_path:
            result.image_path = result.image_path.replace('\\', '/')
            
            if 'website/static/' in result.image_path:
                result.image_path = '/static/' + result.image_path.split('website/static/')[1]
            elif not result.image_path.startswith('/static/'):
                if result.image_path.startswith('/'):
                    result.image_path = '/static' + result.image_path
                else:
                    result.image_path = '/static/' + result.image_path
        
        # Get detection counts for display
        detection_data = result.get_detection_results()
        detection_count = 0
        if 'detections' in detection_data:
            detection_count = len(detection_data['detections'])
        result.detection_count = detection_count
        
        # Add summary field if not present
        if not hasattr(result, 'summary'):
            # Create summary from detection results
            if detection_count > 0:
                # Count objects by class
                detection_counts = {}
                for detection in detection_data.get('detections', []):
                    class_name = detection.get('class', 'Unknown')
                    detection_counts[class_name] = detection_counts.get(class_name, 0) + 1
                
                # Format the summary
                summary = ", ".join([f"{count} {name}" for name, count in detection_counts.items()])
                result.summary = summary if summary else "No objects detected"
            else:
                result.summary = "No objects detected"
    
    # Get current time in Malaysia timezone for template use
    now = get_malaysia_time()
    
    return render_template('my_scans.html', scan_results=scan_results, user=current_user, now=now, filter_date=filter_date)

@views.route('/update-scan-title', methods=['POST'])
@login_required
def update_scan_title():
    try:
        data = request.json
        scan_id = data.get('scan_id')
        new_title = data.get('title')
        
        if not scan_id or not new_title:
            return jsonify({"success": False, "error": "Missing scan_id or title"}), 400
            
        # Get the scan result
        scan_result = ScanResult.query.get(scan_id)
        
        if not scan_result:
            return jsonify({"success": False, "error": "Scan not found"}), 404
            
        # Ensure user owns this scan
        if scan_result.user_id != current_user.id:
            return jsonify({"success": False, "error": "Unauthorized"}), 403
            
        # Update the title
        scan_result.title = new_title
        db.session.commit()
        
        return jsonify({"success": True, "message": "Title updated successfully"})
    except Exception as e:
        print(f"Error updating scan title: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@views.route('/delete-scan', methods=['POST'])
@login_required
def delete_scan():
    try:
        data = request.json
        scan_id = data.get('scan_id')
        
        if not scan_id:
            return jsonify({"success": False, "error": "Missing scan_id"}), 400
            
        # Get the scan result
        scan_result = ScanResult.query.get(scan_id)
        
        if not scan_result:
            return jsonify({"success": False, "error": "Scan not found"}), 404
            
        # Ensure user owns this scan
        if scan_result.user_id != current_user.id:
            return jsonify({"success": False, "error": "Unauthorized"}), 403
            
        # Delete the image files if they exist
        if scan_result.image_path and os.path.exists(scan_result.image_path):
            try:
                os.remove(scan_result.image_path)
            except Exception as e:
                print(f"Error deleting image file: {str(e)}")
                
        if scan_result.result_image_path and os.path.exists(scan_result.result_image_path):
            try:
                os.remove(scan_result.result_image_path)
            except Exception as e:
                print(f"Error deleting result image file: {str(e)}")
                
        # Delete the scan record from the database
        db.session.delete(scan_result)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Scan deleted successfully"})
    except Exception as e:
        print(f"Error deleting scan: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@views.route('/toggle-rotten-status', methods=['POST'])
@login_required
def toggle_rotten_status():
    try:
        data = request.json
        scan_id = data.get('scan_id')
        is_rotten = data.get('is_rotten', False)
        
        if not scan_id:
            return jsonify({"success": False, "error": "Missing scan_id"}), 400
            
        # Get the scan result
        scan_result = ScanResult.query.get(scan_id)
        
        if not scan_result:
            return jsonify({"success": False, "error": "Scan not found"}), 404
            
        # Ensure user owns this scan
        if scan_result.user_id != current_user.id:
            return jsonify({"success": False, "error": "Unauthorized"}), 403
            
        # Update the rotten status
        scan_result.is_rotten = is_rotten
        
        # If marking as rotten, set the date
        if is_rotten:
            scan_result.marked_rotten_date = get_malaysia_time()
        
        db.session.commit()
        
        return jsonify({"success": True, "message": "Rotten status updated successfully"})
    except Exception as e:
        print(f"Error updating rotten status: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500