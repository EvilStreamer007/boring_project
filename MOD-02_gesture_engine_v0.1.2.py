# MOD-02_gesture_engine_v0.1.2.py
import cv2
import math
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class GestureEngine:
    """
    A gesture detection engine utilizing the modern MediaPipe Tasks API
    to track hand landmarks. Features scale-invariant pinch detection 
    and open palm detection with finite state machine (FSM) debouncing.
    """
    
    def __init__(self):
        # Configure MediaPipe HandLandmarker with the required model asset
        base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
        
        # Restrict to a single hand for optimized processing speed
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1
        )
        
        # Initialize the detector
        self.detector = vision.HandLandmarker.create_from_options(options)
        
        # FSM state trackers for debouncing mutually exclusive gestures
        self.palm_frame_count = 0
        self.pinch_frame_count = 0
        
        # Constants defining the number of consecutive frames required to confirm a gesture
        self.PALM_THRESHOLD = 10
        self.PINCH_THRESHOLD = 10

    def _calculate_distance(self, p1, p2):
        """
        Calculates the 2D Euclidean distance between two MediaPipe landmark objects.
        """
        # math.hypot computes the hypotenuse of a right-angled triangle.
        # Mathematically, this is equivalent to the Euclidean distance formula: 
        # sqrt((x2 - x1)^2 + (y2 - y1)^2)
        return math.hypot(p1.x - p2.x, p1.y - p2.y)

    def _is_pinch(self, landmarks):
        """
        Evaluates if the hand is in a pinched state using a scale-invariant ratio.
        This ensures the gesture works regardless of how close the hand is to the camera.
        """
        # Extract the relevant landmarks for the pinch
        thumb_tip = landmarks[4]  # Index 4 is the tip of the thumb
        index_tip = landmarks[8]  # Index 8 is the tip of the index finger
        
        # Extract landmarks for our reference distance
        wrist = landmarks[0]      # Index 0 is the wrist root
        pinky_mcp = landmarks[17] # Index 17 is the base knuckle (MCP) of the pinky
        
        # Calculate the raw pixel distance between the thumb and index finger
        pinch_dist = self._calculate_distance(thumb_tip, index_tip)
        
        # Calculate the reference distance across the palm.
        # We use Wrist to Pinky MCP because this structural distance remains 
        # relatively rigid and constant regardless of how the fingers are bent.
        ref_dist = self._calculate_distance(wrist, pinky_mcp)
        
        # Prevent zero-division errors in edge cases where the reference points overlap
        if ref_dist == 0:
            return False
            
        # The ratio normalizes the pinch distance against the overall size of the hand.
        # If the hand moves closer to the camera, both distances increase proportionally,
        # keeping the ratio stable (scale invariance).
        ratio = pinch_dist / ref_dist
        
        # A ratio < 0.15 mathematically defines that the thumb and index are 
        # very close to each other relative to the anatomical size of the user's hand.
        return ratio < 0.15

    def _is_open_palm(self, landmarks):
        """
        Evaluates if a given set of hand landmarks represents an Open Palm.
        """
        # Fingertip indices
        tips = [8, 12, 16, 20]
        # Corresponding lower joint (PIP) indices
        joints = [6, 10, 14, 18]

        for tip_idx, joint_idx in zip(tips, joints):
            # In image coordinates, y=0.0 is the top. 
            # If the tip 'y' is >= the joint 'y', the finger is curled downwards.
            if landmarks[tip_idx].y >= landmarks[joint_idx].y:
                return False
                
        return True

    def process_frame(self, frame):
        """
        Processes a BGR frame, runs MediaPipe inference, and applies FSM logic
        to return mutually exclusive debounced gestures.
        """
        # Convert OpenCV BGR format to RGB for MediaPipe processing
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # Perform synchronous inference
        detection_result = self.detector.detect(mp_image)

        if detection_result.hand_landmarks:
            # Extract landmarks for the first detected hand
            landmarks = detection_result.hand_landmarks[0]
            
            # Prioritize pinch detection first per architectural directives
            if self._is_pinch(landmarks):
                self.pinch_frame_count += 1
                # Mutually exclusive: resetting palm counter
                self.palm_frame_count = 0 
                
            elif self._is_open_palm(landmarks):
                self.palm_frame_count += 1
                # Mutually exclusive: resetting pinch counter
                self.pinch_frame_count = 0
                
            else:
                # Reset both counters if no defined gesture matches
                self.palm_frame_count = 0
                self.pinch_frame_count = 0
        else:
            # Reset both counters if no hands are visible in the frame
            self.palm_frame_count = 0
            self.pinch_frame_count = 0

        # Evaluate FSM thresholds to return the locked-in gesture
        if self.pinch_frame_count >= self.PINCH_THRESHOLD:
            return "GESTURE_PINCH"
        elif self.palm_frame_count >= self.PALM_THRESHOLD:
            return "GESTURE_PALM"

        # Return None implicitly if no threshold is met
        return None


if __name__ == "__main__":
    # Initialize hardware camera stream
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("[Error] Could not open video device.")
        exit()

    # Instantiate engine (requires 'hand_landmarker.task' in working directory)
    engine = GestureEngine()
    
    print("[Standalone] Gesture Engine v0.1.2 testing started.")
    print("[Standalone] Supported: Open Palm, Pinch.")
    print("[Standalone] Press 'q' or use Ctrl+C to quit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[Error] Failed to grab frame.")
                break

            # Evaluate frame
            gesture = engine.process_frame(frame)

            # Draw the resulting gesture string to the screen if one is detected
            if gesture:
                cv2.putText(
                    frame, 
                    gesture, 
                    (50, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    1.5, 
                    (0, 255, 0), 
                    3
                )

            # Render the UI window
            cv2.imshow('Gesture Testing', frame)

            # Graceful exit condition on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[Standalone] 'q' pressed. Exiting loop...")
                break
                
    except KeyboardInterrupt:
        print("\n[Standalone] Keyboard interrupt received. Shutting down...")
    finally:
        # Release hardware and destroy GUI bindings
        cap.release()
        cv2.destroyAllWindows()
        print("[Standalone] Cleanup complete.")