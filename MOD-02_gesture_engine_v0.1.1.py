# MOD-02_gesture_engine_v0.1.1.py
import cv2
import mediapipe as mp
# Import the modern Tasks API components from MediaPipe
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class GestureEngine:
    """
    A gesture detection engine utilizing the modern MediaPipe Tasks API
    to track hand landmarks, paired with a finite state machine (FSM) 
    logic for debouncing detections.
    """
    
    def __init__(self):
        # Configure the BaseOptions to point to the required model asset file.
        # This requires 'hand_landmarker.task' to be present in the working directory.
        base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
        
        # Configure the HandLandmarkerOptions. We pass the base_options and restrict
        # the detection to a single hand to optimize processing speed.
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1
        )
        
        # Create the HandLandmarker detector instance using the configured options
        self.detector = vision.HandLandmarker.create_from_options(options)
        
        # FSM state trackers for debouncing
        self.palm_frame_count = 0
        # CONSTANT defining the number of consecutive frames required to confirm the gesture
        self.PALM_THRESHOLD = 10

    def _is_open_palm(self, landmarks):
        """
        Helper method to evaluate if a given set of hand landmarks represents an Open Palm.
        """
        # Define the MediaPipe landmark indices for the fingertips
        tips = [8, 12, 16, 20]
        # Define the corresponding landmark indices for the lower joints (PIP joints)
        joints = [6, 10, 14, 18]

        # zip() pairs the elements from the two lists into an iterable of tuples
        for tip_idx, joint_idx in zip(tips, joints):
            # In the Tasks API, landmarks is a list of NormalizedLandmark objects.
            # We access the 'y' attribute directly. 
            # In image coordinates, 0.0 is the top of the image and 1.0 is the bottom.
            # A numerically smaller 'y' means it is visually higher on the screen.
            # If any tip is >= its joint, the finger is curled, returning False.
            if landmarks[tip_idx].y >= landmarks[joint_idx].y:
                return False
                
        # If the loop completes without returning False, all fingers are extended upwards
        return True

    def process_frame(self, frame):
        """
        Processes a single BGR frame, converts it for MediaPipe, runs inference, 
        and applies the FSM debouncing logic.
        """
        # cv2.cvtColor converts the OpenCV BGR image format to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert the NumPy RGB array into a MediaPipe Image object, 
        # which is the required input format for the Tasks API.
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # .detect() performs synchronous inference on the MediaPipe Image
        detection_result = self.detector.detect(mp_image)

        # Check if the result contains any detected hand landmarks
        if detection_result.hand_landmarks:
            # detection_result.hand_landmarks is a list of hands. 
            # We grab index 0 for the first (and only, based on num_hands=1) detected hand.
            landmarks = detection_result.hand_landmarks[0]
            
            # Evaluate the extracted landmarks using our rule logic
            if self._is_open_palm(landmarks):
                # Increment FSM counter if the open palm condition holds
                self.palm_frame_count += 1
            else:
                # Reset FSM counter if the condition breaks
                self.palm_frame_count = 0
        else:
            # Reset FSM counter if no hands are visible in the frame
            self.palm_frame_count = 0

        # Check if the gesture has been held for the required number of frames
        if self.palm_frame_count >= self.PALM_THRESHOLD:
            return "GESTURE_PALM"

        # Return None if the gesture threshold has not been met
        return None


if __name__ == "__main__":
    # Initialize the default camera (index 0)
    cap = cv2.VideoCapture(0)
    
    # Check if the camera hardware was successfully acquired
    if not cap.isOpened():
        print("[Error] Could not open video device.")
        # Terminate the script if the camera fails
        exit()

    # Instantiate the GestureEngine. 
    # NOTE: This will throw an error if 'hand_landmarker.task' is missing.
    engine = GestureEngine()
    
    print("[Standalone] Gesture Engine v0.1.1 testing started.")
    print("[Standalone] Show an open palm to the camera.")
    print("[Standalone] Press 'q' or use Ctrl+C in terminal to quit.")

    try:
        # Main continuous video processing loop
        while True:
            # .read() fetches the latest frame from the camera
            ret, frame = cap.read()
            if not ret:
                print("[Error] Failed to grab frame.")
                break

            # Pass the frame into the engine for inference and debouncing
            gesture = engine.process_frame(frame)

            # If a gesture string is returned (not None), render it on the frame
            if gesture:
                # cv2.putText draws text over the image array in-place.
                cv2.putText(
                    frame, 
                    gesture, 
                    (50, 50),                      # Origin (x, y) coordinates
                    cv2.FONT_HERSHEY_SIMPLEX,      # Font style
                    1.5,                           # Font scale
                    (0, 255, 0),                   # Color in BGR (Green)
                    3                              # Line thickness
                )

            # Render the frame in a GUI window
            cv2.imshow('Gesture Testing', frame)

            # cv2.waitKey(1) allows the GUI to process events for 1 millisecond.
            # & 0xFF extracts the lowest 8 bits for cross-platform compatibility.
            # ord('q') converts the character 'q' to its ASCII integer value.
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[Standalone] 'q' pressed. Exiting loop...")
                break
                
    except KeyboardInterrupt:
        # Catching KeyboardInterrupt (Ctrl+C) gracefully breaks the loop
        print("\n[Standalone] Keyboard interrupt received. Shutting down...")
    finally:
        # The finally block ensures hardware and GUI resources are freed 
        # regardless of how the execution loop ended.
        cap.release()
        cv2.destroyAllWindows()
        print("[Standalone] Cleanup complete.")