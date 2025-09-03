# vision.py - Computer vision, OCR, and screen analysis for Sarah AI Assistant

import cv2
import pytesseract
import pyautogui
import numpy as np
from PIL import Image, ImageEnhance
import os
from datetime import datetime
from utils import log_message, speak, clean_filename
from config import *

# Set tesseract path if configured
if TESSERACT_PATH and os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

class VisionHandler:
    def __init__(self):
        self.screenshot_counter = 0
        self.face_cascade = None
        self.initialize_opencv()
    
    def initialize_opencv(self):
        """Initialize OpenCV components"""
        try:
            # Load face detection cascade
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            log_message("OpenCV initialized successfully")
        except Exception as e:
            log_message(f"OpenCV initialization warning: {e}", "WARNING")
    
    def take_screenshot(self, filename=None, region=None):
        """
        Take a screenshot of the screen
        Args:
            filename (str): Custom filename (optional)
            region (tuple): (left, top, width, height) to capture specific region
        Returns:
            str: Path to saved screenshot or None if failed
        """
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            
            # Ensure screenshots directory exists
            if not os.path.exists(SCREENSHOTS_DIR):
                os.makedirs(SCREENSHOTS_DIR)
            
            filepath = os.path.join(SCREENSHOTS_DIR, clean_filename(filename))
            
            # Take screenshot
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            # Save screenshot
            screenshot.save(filepath)
            
            self.screenshot_counter += 1
            log_message(f"Screenshot saved: {filepath}")
            return filepath
            
        except Exception as e:
            log_message(f"Failed to take screenshot: {e}", "ERROR")
            speak("Failed to take screenshot.")
            return None
    
    def read_text_from_image(self, image_path, language='eng', enhance=True):
        """
        Extract text from image using OCR
        Args:
            image_path (str): Path to image file
            language (str): Language code for OCR (e.g., 'eng', 'spa', 'fra')
            enhance (bool): Whether to enhance image before OCR
        Returns:
            str: Extracted text or empty string if failed
        """
        try:
            # Open image
            image = Image.open(image_path)
            
            # Enhance image for better OCR
            if enhance:
                image = self.enhance_image_for_ocr(image)
            
            # Perform OCR
            config = '--oem 3 --psm 6'  # OCR Engine Mode 3, Page Segmentation Mode 6
            text = pytesseract.image_to_string(image, lang=language, config=config)
            
            # Clean up text
            text = text.strip()
            
            log_message(f"OCR extracted {len(text)} characters from {image_path}")
            return text
            
        except Exception as e:
            log_message(f"OCR failed for {image_path}: {e}", "ERROR")
            return ""
    
    def read_screen_text(self, region=None, language='eng'):
        """
        Take screenshot and extract text from it
        Args:
            region (tuple): Screen region to capture (left, top, width, height)
            language (str): Language for OCR
        Returns:
            str: Extracted text from screen
        """
        # Take screenshot
        screenshot_path = self.take_screenshot(region=region)
        
        if not screenshot_path:
            return ""
        
        # Extract text from screenshot
        text = self.read_text_from_image(screenshot_path, language)
        
        if text:
            log_message(f"Screen text extracted: {len(text)} characters")
            return text
        else:
            speak("No text found on screen.")
            return ""
    
    def enhance_image_for_ocr(self, image):
        """
        Enhance image for better OCR results
        Args:
            image (PIL.Image): Input image
        Returns:
            PIL.Image: Enhanced image
        """
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Increase contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Increase sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            # Convert to numpy array for OpenCV operations
            img_array = np.array(image)
            
            # Apply noise reduction
            img_array = cv2.medianBlur(img_array, 3)
            
            # Apply threshold to get binary image
            _, img_array = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Convert back to PIL Image
            return Image.fromarray(img_array)
            
        except Exception as e:
            log_message(f"Image enhancement failed: {e}", "WARNING")
            return image
    
    def detect_faces(self, image_path):
        """
        Detect faces in an image
        Args:
            image_path (str): Path to image file
        Returns:
            list: List of face coordinates [(x, y, w, h), ...]
        """
        if not self.face_cascade:
            log_message("Face cascade not initialized", "ERROR")
            return []
        
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                log_message(f"Could not load image: {image_path}", "ERROR")
                return []
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            log_message(f"Detected {len(faces)} faces in {image_path}")
            return faces.tolist() if len(faces) > 0 else []
            
        except Exception as e:
            log_message(f"Face detection failed: {e}", "ERROR")
            return []
    
    def detect_faces_on_screen(self, region=None):
        """
        Take screenshot and detect faces
        Args:
            region (tuple): Screen region to capture
        Returns:
            list: List of face coordinates
        """
        # Take screenshot
        screenshot_path = self.take_screenshot(region=region)
        
        if not screenshot_path:
            return []
        
        # Detect faces in screenshot
        faces = self.detect_faces(screenshot_path)
        
        if faces:
            log_message(f"Found {len(faces)} faces on screen")
            speak(f"I found {len(faces)} face{'s' if len(faces) != 1 else ''} on the screen.")
        else:
            speak("No faces detected on screen.")
        
        return faces
    
    def find_text_on_screen(self, search_text, region=None):
        """
        Find specific text on screen and return its location
        Args:
            search_text (str): Text to search for
            region (tuple): Screen region to search in
        Returns:
            dict: Location information or None if not found
        """
        # Get screen text
        full_text = self.read_screen_text(region)
        
        if not full_text:
            return None
        
        # Simple text search (case-insensitive)
        search_text_lower = search_text.lower()
        full_text_lower = full_text.lower()
        
        if search_text_lower in full_text_lower:
            # Calculate approximate position (this is simplified)
            lines = full_text.split('\n')
            for i, line in enumerate(lines):
                if search_text_lower in line.lower():
                    return {
                        'found': True,
                        'line_number': i + 1,
                        'line_text': line.strip(),
                        'full_text': full_text
                    }
        
        return None
    
    def get_screen_colors(self, region=None, sample_points=9):
        """
        Get dominant colors from screen region
        Args:
            region (tuple): Screen region to analyze
            sample_points (int): Number of sample points to analyze
        Returns:
            list: List of dominant colors in RGB format
        """
        try:
            # Take screenshot
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            # Convert to numpy array
            img_array = np.array(screenshot)
            
            # Reshape for color analysis
            pixels = img_array.reshape(-1, 3)
            
            # Get unique colors and their counts
            unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
            
            # Sort by frequency and get top colors
            sorted_indices = np.argsort(counts)[::-1]
            top_colors = unique_colors[sorted_indices[:sample_points]]
            
            # Convert to list of tuples
            colors = [tuple(color) for color in top_colors]
            
            log_message(f"Extracted {len(colors)} dominant colors from screen")
            return colors
            
        except Exception as e:
            log_message(f"Color analysis failed: {e}", "ERROR")
            return []
    
    def analyze_image_content(self, image_path):
        """
        Analyze image content and provide description
        Args:
            image_path (str): Path to image file
        Returns:
            dict: Analysis results
        """
        results = {
            'text': '',
            'faces': [],
            'colors': [],
            'size': (0, 0),
            'format': '',
            'file_size': 0
        }
        
        try:
            # Get basic image info
            with Image.open(image_path) as img:
                results['size'] = img.size
                results['format'] = img.format
                results['file_size'] = os.path.getsize(image_path)
            
            # Extract text
            results['text'] = self.read_text_from_image(image_path)
            
            # Detect faces
            results['faces'] = self.detect_faces(image_path)
            
            # Analyze colors (simplified)
            with Image.open(image_path) as img:
                img_array = np.array(img)
                if len(img_array.shape) == 3:  # Color image
                    pixels = img_array.reshape(-1, 3)
                    unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
                    sorted_indices = np.argsort(counts)[::-1]
                    top_colors = unique_colors[sorted_indices[:5]]
                    results['colors'] = [tuple(color) for color in top_colors]
            
            log_message(f"Image analysis complete for {image_path}")
            return results
            
        except Exception as e:
            log_message(f"Image analysis failed: {e}", "ERROR")
            return results
    
    def create_annotated_image(self, image_path, annotations):
        """
        Create annotated version of image with text/shapes
        Args:
            image_path (str): Path to source image
            annotations (list): List of annotation dictionaries
        Returns:
            str: Path to annotated image or None if failed
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                return None
            
            # Process annotations
            for annotation in annotations:
                ann_type = annotation.get('type', 'text')
                
                if ann_type == 'text':
                    # Add text annotation
                    text = annotation.get('text', '')
                    position = annotation.get('position', (50, 50))
                    color = annotation.get('color', (0, 255, 0))  # Green
                    font_scale = annotation.get('font_scale', 1.0)
                    
                    cv2.putText(img, text, position, cv2.FONT_HERSHEY_SIMPLEX, 
                               font_scale, color, 2)
                
                elif ann_type == 'rectangle':
                    # Add rectangle
                    start_point = annotation.get('start', (0, 0))
                    end_point = annotation.get('end', (100, 100))
                    color = annotation.get('color', (255, 0, 0))  # Blue
                    thickness = annotation.get('thickness', 2)
                    
                    cv2.rectangle(img, start_point, end_point, color, thickness)
                
                elif ann_type == 'circle':
                    # Add circle
                    center = annotation.get('center', (50, 50))
                    radius = annotation.get('radius', 25)
                    color = annotation.get('color', (0, 0, 255))  # Red
                    thickness = annotation.get('thickness', 2)
                    
                    cv2.circle(img, center, radius, color, thickness)
            
            # Save annotated image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(SCREENSHOTS_DIR, f"annotated_{timestamp}.png")
            cv2.imwrite(output_path, img)
            
            log_message(f"Annotated image saved: {output_path}")
            return output_path
            
        except Exception as e:
            log_message(f"Image annotation failed: {e}", "ERROR")
            return None
    
    def compare_images(self, image1_path, image2_path, threshold=0.8):
        """
        Compare two images for similarity
        Args:
            image1_path (str): Path to first image
            image2_path (str): Path to second image
            threshold (float): Similarity threshold (0-1)
        Returns:
            dict: Comparison results
        """
        try:
            # Read images
            img1 = cv2.imread(image1_path, cv2.IMREAD_GRAYSCALE)
            img2 = cv2.imread(image2_path, cv2.IMREAD_GRAYSCALE)
            
            if img1 is None or img2 is None:
                return {'error': 'Could not load one or both images'}
            
            # Resize images to same size for comparison
            height = min(img1.shape[0], img2.shape[0])
            width = min(img1.shape[1], img2.shape[1])
            
            img1_resized = cv2.resize(img1, (width, height))
            img2_resized = cv2.resize(img2, (width, height))
            
            # Calculate similarity using normalized cross-correlation
            correlation = cv2.matchTemplate(img1_resized, img2_resized, cv2.TM_CCOEFF_NORMED)[0][0]
            
            # Calculate structural similarity (simplified)
            diff = cv2.absdiff(img1_resized, img2_resized)
            similarity = 1.0 - (np.sum(diff) / (255.0 * diff.size))
            
            is_similar = similarity >= threshold
            
            result = {
                'similarity': float(similarity),
                'correlation': float(correlation),
                'is_similar': is_similar,
                'threshold': threshold
            }
            
            log_message(f"Image comparison: {similarity:.3f} similarity")
            return result
            
        except Exception as e:
            log_message(f"Image comparison failed: {e}", "ERROR")
            return {'error': str(e)}
    
    def get_screen_region_info(self, x, y, width, height):
        """
        Get detailed information about a screen region
        Args:
            x, y (int): Top-left coordinates
            width, height (int): Region dimensions
        Returns:
            dict: Region information
        """
        region = (x, y, width, height)
        
        # Take screenshot of region
        screenshot_path = self.take_screenshot(region=region)
        
        if not screenshot_path:
            return {}
        
        # Analyze the region
        info = self.analyze_image_content(screenshot_path)
        info['coordinates'] = region
        
        return info
    
    def monitor_screen_changes(self, region=None, callback=None, interval=1.0):
        """
        Monitor screen for changes (simplified implementation)
        Args:
            region (tuple): Screen region to monitor
            callback (function): Function to call when change detected
            interval (float): Check interval in seconds
        """
        import threading
        import time
        
        def monitor_loop():
            previous_screenshot = None
            
            while True:
                try:
                    # Take current screenshot
                    current_screenshot = self.take_screenshot(region=region)
                    
                    if previous_screenshot and current_screenshot:
                        # Compare with previous screenshot
                        comparison = self.compare_images(previous_screenshot, current_screenshot, threshold=0.95)
                        
                        if not comparison.get('is_similar', True):
                            log_message("Screen change detected")
                            if callback:
                                callback(current_screenshot, previous_screenshot)
                    
                    previous_screenshot = current_screenshot
                    time.sleep(interval)
                    
                except Exception as e:
                    log_message(f"Screen monitoring error: {e}", "ERROR")
                    time.sleep(interval)
        
        # Start monitoring in separate thread
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        log_message("Screen monitoring started")
    
    def cleanup_old_screenshots(self, days_old=7):
        """
        Clean up old screenshots
        Args:
            days_old (int): Remove screenshots older than this many days
        """
        try:
            import time
            
            current_time = time.time()
            cutoff_time = current_time - (days_old * 24 * 60 * 60)
            
            removed_count = 0
            
            for filename in os.listdir(SCREENSHOTS_DIR):
                filepath = os.path.join(SCREENSHOTS_DIR, filename)
                
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    
                    if file_time < cutoff_time:
                        os.remove(filepath)
                        removed_count += 1
            
            log_message(f"Cleaned up {removed_count} old screenshots")
            
        except Exception as e:
            log_message(f"Screenshot cleanup failed: {e}", "ERROR")

# Create global vision handler instance
vision_handler = VisionHandler()

# Convenience functions for easy import
def take_screenshot(filename=None, region=None):
    """Take a screenshot"""
    return vision_handler.take_screenshot(filename, region)

def read_screen_text(region=None, language='eng'):
    """Read text from screen"""
    return vision_handler.read_screen_text(region, language)

def read_text_from_image(image_path, language='eng', enhance=True):
    """Read text from image file"""
    return vision_handler.read_text_from_image(image_path, language, enhance)

def detect_faces_on_screen(region=None):
    """Detect faces on screen"""
    return vision_handler.detect_faces_on_screen(region)

def detect_faces_in_image(image_path):
    """Detect faces in image"""
    return vision_handler.detect_faces(image_path)

def find_text_on_screen(search_text, region=None):
    """Find specific text on screen"""
    return vision_handler.find_text_on_screen(search_text, region)

def analyze_image(image_path):
    """Analyze image content"""
    return vision_handler.analyze_image_content(image_path)

def get_screen_colors(region=None, sample_points=9):
    """Get dominant colors from screen"""
    return vision_handler.get_screen_colors(region, sample_points)

def compare_images(image1_path, image2_path, threshold=0.8):
    """Compare two images"""
    return vision_handler.compare_images(image1_path, image2_path, threshold)

def cleanup_screenshots(days_old=7):
    """Clean up old screenshots"""
    vision_handler.cleanup_old_screenshots(days_old)

# Log successful module initialization
log_message("Vision module initialized successfully")