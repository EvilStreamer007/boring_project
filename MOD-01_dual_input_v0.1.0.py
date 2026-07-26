# MOD-01_dual_input_v0.1.0.py
import multiprocessing
import time
import cv2

def audio_worker(event_queue):
    """
    Simulates an audio wake-word detection loop.
    :param event_queue: multiprocessing.Queue used to send events back to the main process.
    """
    try:
        # A continuous loop to simulate ongoing audio stream processing
        while True:
            # time.sleep() suspends execution for the given number of seconds
            time.sleep(5)
            
            # queue.put() safely adds an item to the queue from this worker process
            event_queue.put({"source": "audio", "event": "WAKE_WORD_DETECTED"})
            
    except KeyboardInterrupt:
        # Catching KeyboardInterrupt allows the thread to exit gracefully without printing a traceback
        pass

def vision_worker(event_queue):
    """
    Captures webcam frames, calculates FPS, and simulates gesture detection.
    :param event_queue: multiprocessing.Queue used to send events back to the main process.
    """
    # cv2.VideoCapture(0) initializes the primary webcam stream (index 0)
    cap = cv2.VideoCapture(0)
    
    # .isOpened() checks if the camera was successfully initialized
    if not cap.isOpened():
        print("[Vision Error] Could not open camera.")
        return

    frame_count = 0
    # time.time() returns the current time in seconds since the Epoch
    start_time = time.time()

    try:
        while True:
            # .read() grabs the next frame. 'ret' is a boolean indicating success.
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            
            # The modulo operator (%) checks if the frame_count is a multiple of 30
            if frame_count % 30 == 0:
                # Calculate elapsed time for the last 30 frames
                elapsed_time = time.time() - start_time
                fps = 30 / elapsed_time
                
                # Formatted string literal (f-string) formats the float to 2 decimal places
                print(f"[Vision] FPS: {fps:.2f}")
                
                # Reset the start time for the next batch of 30 frames
                start_time = time.time()
                
                # Stub out gesture detection by occasionally putting an event in the queue
                event_queue.put({"source": "vision", "event": "GESTURE_HAND_RAISED"})
                
    except KeyboardInterrupt:
        pass
    finally:
        # .release() frees the hardware resource so other applications can use the camera
        cap.release()
        # .destroyAllWindows() closes any GUI windows opened by OpenCV
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # multiprocessing.Queue() creates a thread- and process-safe FIFO queue
    event_queue = multiprocessing.Queue()
    
    # multiprocessing.Process() creates a new Python process. 
    # 'target' specifies the function to run, 'args' is a tuple of arguments to pass to it.
    audio_process = multiprocessing.Process(target=audio_worker, args=(event_queue,))
    vision_process = multiprocessing.Process(target=vision_worker, args=(event_queue,))
    
    # Setting .daemon = True means these child processes will automatically be killed
    # when the main parent process exits.
    audio_process.daemon = True
    vision_process.daemon = True
    
    # .start() spawns the process and calls the target function
    audio_process.start()
    vision_process.start()
    
    print("[Main] Coordinator started. Press Ctrl+C to terminate.")
    
    try:
        # Main event loop acting as the coordinator
        while True:
            # queue.get() is a blocking call. It halts execution here until an item
            # is placed into the queue by one of the worker processes.
            event = event_queue.get()
            print(f"[Main] Event Received: {event}")
            
    except KeyboardInterrupt:
        # Triggered when the user presses Ctrl+C
        print("\n[Main] Terminating daemons and shutting down...")
    finally:
        # Even though vision_worker cleans up its own windows, doing it here
        # provides a fallback guarantee that GUI windows close on main exit.
        cv2.destroyAllWindows()
        print("[Main] Shutdown complete.")