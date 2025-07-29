from flask import request, render_template, send_from_directory, Blueprint, jsonify, send_file
from flask_login import current_user, login_required
from ultralytics import YOLO
import cv2
import os
import shutil
from datetime import datetime, timezone, timedelta
import logging
import base64
import numpy as np
import traceback
import json
import sys
from werkzeug.utils import secure_filename

app = Blueprint('app', __name__)
UPLOAD_FOLDER = os.path.join('website', 'static', 'uploads')
RESULT_FOLDER = os.path.join('website', 'static', 'results')
SAVED_RESULTS_FOLDER = os.path.join('website', 'static', 'saved_results')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)
os.makedirs(SAVED_RESULTS_FOLDER, exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Malaysia timezone object (UTC+8)
malaysia_tz = timezone(timedelta(hours=8))

# Configure handler to output to console
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Log all directories to help with debugging
logger.info(f"UPLOAD_FOLDER: {os.path.abspath(UPLOAD_FOLDER)}")
logger.info(f"RESULT_FOLDER: {os.path.abspath(RESULT_FOLDER)}")
logger.info(f"SAVED_RESULTS_FOLDER: {os.path.abspath(SAVED_RESULTS_FOLDER)}")

# Load the YOLO model
model = None
try:
    # Try different potential model paths
    model_paths = [
        'best.pt',                            # Current directory
        './best.pt',                          # Current directory (explicit)
        'website/best.pt',                    # Website folder
        'C:/Users/ganye/Desktop/FYP Web App/best.pt'  # Absolute path
    ]
    
    for model_path in model_paths:
        logger.info(f"Attempting to load YOLO model from: {model_path}")
        if os.path.exists(model_path):
            model = YOLO(model_path)
            logger.info(f"YOLO model loaded successfully from {model_path}")
            break
        else:
            logger.warning(f"Model file not found at: {model_path}")
    
    if model is None:
        logger.error("Could not find YOLO model at any of the expected paths")
except Exception as e:
    logger.error(f"Error loading YOLO model: {str(e)}")
    logger.error(traceback.format_exc())

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/scan', methods=['GET'])
def scan_page():
    return render_template('scan.html', user=current_user)

@app.route('/predict', methods=['POST'])
def predict():
    logger.info("Predict endpoint called")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request content type: {request.content_type}")
    logger.info(f"Request files: {request.files}")
    
    # Print detailed debugging for multipart/form-data
    if request.content_type and 'multipart/form-data' in request.content_type:
        logger.info("Processing multipart/form-data")
        for key in request.files:
            file = request.files[key]
            logger.info(f"File '{key}': {file.filename}, {file.content_type}, {file.content_length} bytes")
    
    logger.info(f"Request form: {request.form}")
    
    try:
        logger.info(f"Request JSON: {request.json}")
    except:
        logger.info("No JSON data in request")
    
    if model is None:
        logger.error("YOLO model not loaded")
        return jsonify({"success": False, "error": "YOLO model not loaded. Please contact the administrator."}), 500

    try:
        # Check if this is a file upload or a base64 image from the camera
        if 'file' in request.files:
            # Handle file upload
            file = request.files['file']
            if file.filename == '':
                logger.error("No file selected")
                return jsonify({"success": False, "error": "No file selected"}), 400
            
            if not allowed_file(file.filename):
                logger.error(f"Invalid file type: {file.filename}")
                return jsonify({"success": False, "error": "Invalid file type"}), 400

            # Generate unique filename
            timestamp = get_malaysia_time().strftime('%Y%m%d_%H%M%S')
            filename = f"upload_{timestamp}_{file.filename}"
            file_location = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_location)
            logger.info(f"File saved to {file_location}")
            
            # Process the uploaded image
            return process_image(file_location, timestamp)
            
        elif request.json and 'image' in request.json:
            # Handle base64 image data from the camera
            try:
                # Decode the base64 image
                base64_data = request.json['image'].split(',')[1] if ',' in request.json['image'] else request.json['image']
                img_data = base64.b64decode(base64_data)
                
                # Convert to numpy array
                nparr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                # Generate unique filename
                timestamp = get_malaysia_time().strftime('%Y%m%d_%H%M%S')
                filename = f"camera_{timestamp}.jpg"
                file_location = os.path.join(UPLOAD_FOLDER, filename)
                
                # Save the image
                cv2.imwrite(file_location, img)
                logger.info(f"Camera image saved to {file_location}")
                
                # Process the camera image
                return process_image(file_location, timestamp)
                
            except Exception as e:
                logger.error(f"Error processing base64 image: {str(e)}")
                logger.error(traceback.format_exc())
                return jsonify({"success": False, "error": f"Error processing image: {str(e)}"}), 500
        else:
            logger.error("No file or image data provided")
            return jsonify({"success": False, "error": "No file or image data provided"}), 400

    except Exception as e:
        logger.error(f"Error in predict route: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

def process_image(image_path, timestamp):
    """
    Process an image with YOLO model and return the results
    """
    try:
        # Check if the image file exists
        if not os.path.exists(image_path):
            logger.error(f"Image file not found at: {image_path}")
            return jsonify({"success": False, "error": f"Image file not found at: {image_path}"}), 404
        
        # Check if the model is loaded
        if model is None:
            logger.error("YOLO model not loaded")
            return jsonify({"success": False, "error": "YOLO model not loaded. Please contact the administrator."}), 500
        
        # Run YOLO inference
        logger.info(f"Starting YOLO inference on {image_path}")
        try:
            results = model.predict(
                source=image_path,
                conf=0.25,  
                save=True,  
                project=RESULT_FOLDER,
                name=timestamp,  
                line_thickness=1,  
                boxes=True,  
                show_labels=True,  
                show_conf=True, 
                max_det=300,  
                exist_ok=True 
            )
            logger.info("YOLO inference completed successfully")
        except Exception as e:
            logger.error(f"Error during YOLO inference: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"success": False, "error": f"Error during YOLO inference: {str(e)}"}), 500
        
        if not results or len(results) == 0:
            logger.error("YOLO inference did not return any results")
            return jsonify({"success": False, "error": "No results from YOLO inference"}), 500
        
        # Get detection information
        detections = []
        for result in results:
            for box in result.boxes:
                detection = {
                    "class": result.names[int(box.cls[0])],
                    "confidence": float(box.conf[0]),
                    "box": {
                        "x1": float(box.xyxy[0][0]),
                        "y1": float(box.xyxy[0][1]),
                        "x2": float(box.xyxy[0][2]),
                        "y2": float(box.xyxy[0][3])
                    }
                }
                detections.append(detection)
        
        try:
            # Get the path to the result image and normalize it
            result_image_path = str(results[0].path)
            logger.info(f"Raw result image path: {result_image_path}")
            
            if not os.path.exists(result_image_path):
                logger.error(f"Result image not found at: {result_image_path}")
                return jsonify({"success": False, "error": f"Result image not found at: {result_image_path}"}), 404
                
            # Get the result filename and secure it
            result_filename = os.path.basename(result_image_path)
            secure_result_filename = secure_filename(result_filename)
            
            # Get the actual file extension from the saved file
            result_dir = os.path.join(RESULT_FOLDER, timestamp)
            actual_files = os.listdir(result_dir)
            if actual_files:
                actual_file = actual_files[0]  # Get the first file in the directory
                actual_ext = os.path.splitext(actual_file)[1]
                # Update the secure filename with the actual extension
                secure_result_filename = os.path.splitext(secure_result_filename)[0] + actual_ext
            
            # Create a standard URL path with proper encoding
            result_image_url = f'/static/results/{timestamp}/{secure_result_filename}'
            
            # Create a direct file serving URL as a fallback method
            result_path_for_direct = f'results/{timestamp}/{secure_result_filename}'
            direct_url = f'/serve-file?path={result_path_for_direct}'
            
            # Log URLs
            logger.info(f"Standard URL: {result_image_url}")
            logger.info(f"Direct URL: {direct_url}")
            
            # Verify file exists
            if not os.path.exists(result_image_path):
                logger.error(f"Result image not found at: {result_image_path}")
                return jsonify({"success": False, "error": f"Result image not found at: {result_image_path}"}), 404
            else:
                logger.info(f"Result image verified at: {result_image_path}")
                
        except Exception as e:
            logger.error(f"Error handling result image: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"success": False, "error": f"Error handling result image: {str(e)}"}), 500

        # Prepare and send response
        try:
            response_data = {
                "success": True,
                "result_image": result_image_url,
                "direct_image_url": direct_url,  # Include direct URL as fallback
                "detections": detections,
                "image_size": {
                    "width": results[0].orig_shape[1],
                    "height": results[0].orig_shape[0]
                },
                "original_image": image_path.replace('\\', '/')  # Normalize path separators
            }
            logger.info(f"Sending response: {response_data}")
            return jsonify(response_data)
        except Exception as e:
            logger.error(f"Error preparing response: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"success": False, "error": f"Error preparing response: {str(e)}"}), 500

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/static/results/<path:filename>')
def serve_result_image(filename):
    """Serve result images directly from the results folder."""
    try:
        # Normalize the path separators
        filename = filename.replace('\\', '/')
        logger.info(f"Request to serve result image: {filename}")
        
        # Split the path into components
        parts = filename.split('/')
        
        # Use Flask's send_file for more direct file serving
        from flask import send_file
        
        # Check if the path has a timestamp directory structure (e.g., 20250414_235223/filename.jpg)
        if len(parts) > 1:
            timestamp_dir = parts[0]
            file = parts[1]
            logger.info(f"Parsed timestamp directory: {timestamp_dir}, file: {file}")
            
            # Construct absolute path
            abs_file_path = os.path.abspath(os.path.join('website', 'static', 'results', timestamp_dir, file))
            logger.info(f"Absolute file path: {abs_file_path}")
            
            # Check if the file exists with the exact path
            if os.path.exists(abs_file_path):
                logger.info(f"File exists: {abs_file_path}")
                return send_file(abs_file_path)
            
            # If file doesn't exist, try to find it in the directory
            result_dir = os.path.abspath(os.path.join('website', 'static', 'results', timestamp_dir))
            logger.info(f"Checking directory: {result_dir}")
            
            if os.path.exists(result_dir):
                files_in_dir = os.listdir(result_dir)
                logger.info(f"Files in directory: {files_in_dir}")
                
                # Try to find a matching file by comparing the base names
                requested_base = os.path.splitext(file)[0]
                logger.info(f"Looking for file with base name: {requested_base}")
                
                for actual_file in files_in_dir:
                    actual_base = os.path.splitext(actual_file)[0]
                    logger.info(f"Comparing with actual file base: {actual_base}")
                    
                    # Compare the base names, ignoring spaces and underscores
                    if actual_base.replace(' ', '_') == requested_base.replace(' ', '_'):
                        actual_path = os.path.join(result_dir, actual_file)
                        logger.info(f"Found matching file: {actual_path}")
                        return send_file(actual_path)
            
            logger.error(f"File does not exist: {abs_file_path} or any alternatives")
            return jsonify({"error": f"File not found: {file}"}), 404
        else:
            # Handle direct file access (no subdirectory)
            abs_file_path = os.path.abspath(os.path.join('website', 'static', 'results', filename))
            logger.info(f"Direct file absolute path: {abs_file_path}")
            
            if os.path.exists(abs_file_path):
                logger.info(f"Direct file exists: {abs_file_path}")
                return send_file(abs_file_path)
            else:
                logger.error(f"Direct file does not exist: {abs_file_path}")
                return jsonify({"error": f"File not found: {filename}"}), 404
                
    except Exception as e:
        logger.error(f"Error serving result image: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Error serving image: {str(e)}"}), 500

@app.route('/static/uploads/<path:filename>')
def serve_upload_image(filename):
    """Serve uploaded images directly from the uploads folder."""
    try:
        # Normalize the path separators
        filename = filename.replace('\\', '/')
        
        # Log the request for debugging
        logger.info(f"Serving uploaded image: {filename}")
        
        # Split the path into components to handle subdirectories
        parts = filename.split('/')
        if len(parts) > 1:
            # If the path has multiple components, handle it accordingly
            directory = '/'.join(parts[:-1])
            file = parts[-1]
            
            # For profile pictures, use a direct path
            if 'profile_pics' in directory:
                logger.info(f"Serving profile picture: {file} from {directory}")
                return send_from_directory('website/static/uploads/profile_pics', file)
            
            full_path = os.path.join('website', 'static', 'uploads', directory)
            logger.info(f"Checking directory: {full_path}")
            if not os.path.exists(full_path):
                logger.error(f"Directory does not exist: {full_path}")
                return jsonify({"error": "Directory not found"}), 404
            
            logger.info(f"Serving file from {full_path}: {file}")
            return send_from_directory(full_path, file)
        else:
            # Otherwise, serve directly from the uploads folder
            full_path = os.path.join('website', 'static', 'uploads')
            logger.info(f"Serving file from uploads root: {filename}")
            return send_from_directory(full_path, filename)
    except Exception as e:
        logger.error(f"Error serving uploaded image: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Image not found: {str(e)}"}), 404

@app.route('/static/uploads/profile_pics/<filename>')
def serve_profile_pic(filename):
    """Serve profile pictures directly."""
    try:
        # Log the request
        logger.info(f"Serving profile picture: {filename}")
        
        # Create absolute path for checking
        profile_pics_dir = os.path.join(os.getcwd(), 'website', 'static', 'uploads', 'profile_pics')
        file_path = os.path.join(profile_pics_dir, filename)
        
        # Check if the file exists
        if os.path.exists(file_path):
            logger.info(f"Profile picture found at: {file_path}")
            # Use absolute path to avoid issues
            return send_from_directory(profile_pics_dir, filename)
        else:
            logger.warning(f"Profile picture not found at: {file_path}, using default")
            return send_from_directory(profile_pics_dir, 'default.jpg')
    except Exception as e:
        logger.error(f"Error serving profile picture: {str(e)}")
        logger.error(traceback.format_exc())
        try:
            profile_pics_dir = os.path.join(os.getcwd(), 'website', 'static', 'uploads', 'profile_pics')
            return send_from_directory(profile_pics_dir, 'default.jpg')
        except:
            return jsonify({"error": "Could not serve default profile picture"}), 500

@app.route('/save-result', methods=['POST'])
@login_required
def save_result():
    try:
        data = request.get_json()
        if not data:
            logger.error("No data provided for saving")
            return jsonify({"error": "No data provided"}), 400

        # Generate unique filename for saved result
        timestamp = get_malaysia_time().strftime('%Y%m%d_%H%M%S')
        
        # Import shelf life calculation utilities
        from .utils import calculate_expiry_date
        
        # Save the original image to a permanent location
        original_image = data.get('original_image')
        saved_image_path = ""
        result_image_path = ""
        
        if original_image and os.path.exists(original_image):
            saved_image_filename = f"saved_{timestamp}_{os.path.basename(original_image)}"
            saved_image_path = os.path.join(SAVED_RESULTS_FOLDER, saved_image_filename)
            shutil.copy(original_image, saved_image_path)
            logger.info(f"Original image saved to {saved_image_path}")
            
            # Get the result image path if available
            if "result_image" in data:
                result_image = data.get('result_image')
                if result_image and result_image.startswith('/static/'):
                    # Extract the path after /static/
                    result_path = result_image[8:]  # Remove '/static/' prefix
                    source_path = os.path.join('website/static', result_path)
                    if os.path.exists(source_path):
                        result_image_filename = f"result_{timestamp}_{os.path.basename(source_path)}"
                        result_image_path = os.path.join(SAVED_RESULTS_FOLDER, result_image_filename)
                        shutil.copy(source_path, result_image_path)
                        logger.info(f"Result image saved to {result_image_path}")
        
        # Parse detection data
        detections = data.get('detections', [])
        
        # Determine produce type and freshness
        produce_classes = {}
        for detection in detections:
            class_name = detection.get('class', '')
            confidence = detection.get('confidence', 0)
            
            # Count occurrences of each class
            if class_name not in produce_classes:
                produce_classes[class_name] = {
                    'count': 0,
                    'total_confidence': 0,
                    'is_fresh': 'fresh' in class_name.lower()
                }
            
            produce_classes[class_name]['count'] += 1
            produce_classes[class_name]['total_confidence'] += confidence
        
        # Find the dominant produce (highest confidence × count)
        dominant_produce = None
        highest_score = 0
        
        for class_name, info in produce_classes.items():
            score = info['count'] * info['total_confidence']
            if score > highest_score:
                highest_score = score
                dominant_produce = class_name
        
        # Calculate expiry date and storage recommendation
        expiry_date = None
        storage_recommendation = None
        
        # Check if client already calculated expiry
        if data.get('expiry_date') and data.get('storage_tip'):
            try:
                # Parse the ISO date string
                expiry_date = datetime.fromisoformat(data.get('expiry_date').replace('Z', '+00:00'))
                
                # Ensure expiry_date is timezone-aware in Malaysia timezone
                from .views import to_malaysia_time
                expiry_date = to_malaysia_time(expiry_date)
                
                storage_recommendation = data.get('storage_tip')
                
                # Remove any existing date information from storage recommendation to avoid duplicates
                if storage_recommendation and "Expected to stay fresh until" in storage_recommendation:
                    # Keep only the first part of the recommendation, before the expiry date mention
                    storage_recommendation = storage_recommendation.split("Expected to stay fresh until")[0].strip()
                
                # Update dominant produce if client provided it
                if data.get('dominant_produce'):
                    dominant_produce = data.get('dominant_produce')
                
                logger.info(f"Using client-provided expiry information: {expiry_date}, {storage_recommendation}")
            except Exception as e:
                logger.error(f"Error parsing client expiry date: {e}")
                # Fall back to server calculation
                expiry_date = None
        
        # If no client expiry or parsing failed, calculate on server
        if expiry_date is None and dominant_produce and 'fresh' in dominant_produce.lower():
            # Use current time as detection date
            detection_date = get_malaysia_time()
            
            # Default to refrigerated storage for most produce except potato
            storage_type = "room_temp" if "potato" in dominant_produce.lower() else "refrigerated"
            
            # Calculate expiry date
            expiry_date, storage_recommendation = calculate_expiry_date(
                dominant_produce, detection_date, storage_type
            )
        
        # Save the result data to JSON
        result_filename = f"result_{timestamp}.json"
        result_path = os.path.join(SAVED_RESULTS_FOLDER, result_filename)

        with open(result_path, 'w') as f:
            json.dump({
                'user_id': current_user.id,
                'timestamp': timestamp,
                'detections': data.get('detections', []),
                'image_size': data.get('image_size', {}),
                'image_path': saved_image_path.replace('\\', '/'),  # Normalize path
                'dominant_produce': dominant_produce,
                'expiry_date': expiry_date.isoformat() if expiry_date else None,
                'storage_recommendation': storage_recommendation
            }, f, indent=4)

        logger.info(f"Result data saved to {result_path}")
        
        # Save to database
        from .models import ScanResult, db
        
        try:
            # Store paths relative to the static folder for easier web access
            db_image_path = saved_image_path.replace('\\', '/')
            db_result_image_path = result_image_path.replace('\\', '/') if result_image_path else None
            
            # Generate a default title based on detection results
            default_title = "Unnamed Scan"
            if dominant_produce:
                default_title = dominant_produce + " - " + timestamp
                
                # Make sure the title isn't too long
                if len(default_title) > 95:  # Leave room for the varchar(100) limit
                    default_title = default_title[:95] + "..."
            
            # Create new scan result
            scan_result = ScanResult(
                user_id=current_user.id,
                title=default_title,
                image_path=db_image_path,
                result_image_path=db_result_image_path,
                expected_expiry=expiry_date,
                storage_recommendation=storage_recommendation
            )
            
            # Set detection results
            scan_result.set_detection_results({
                'detections': data.get('detections', []),
                'image_size': data.get('image_size', {})
            })
            
            # Save to database
            db.session.add(scan_result)
            db.session.commit()
            
            logger.info(f"Saved scan result to database with ID {scan_result.id}")
            
            return jsonify({
                "success": True, 
                "scan_result_id": scan_result.id,
                "expiry_date": expiry_date.isoformat() if expiry_date else None,
                "storage_recommendation": storage_recommendation
            })
            
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"success": True, "error": f"Saved images but database error: {str(e)}"})
            
    except Exception as e:
        logger.error(f"Error saving result: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/serve-file')
def serve_file_by_path():
    path = request.args.get('path')
    if not path:
        return jsonify({'error': 'No path provided'}), 400
    
    # Normalize path separators
    path = path.replace('/', os.sep)
    
    # Construct absolute path
    absolute_path = os.path.join(app.root_path, 'static', path)
    
    if not os.path.exists(absolute_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(absolute_path)

# Function to get current time in Malaysia timezone
def get_malaysia_time():
    # Get current time in UTC and add 8 hours for Malaysia
    return datetime.now(malaysia_tz)
