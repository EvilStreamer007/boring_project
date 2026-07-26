# boring_project
wanted to play some music but my phone ran out of battery and the laptop was too far- the only feasible solution? build a voice assistant to control the laptop handsfree from afar but without the privacy concerns or the hassle of having to use different tools to accomplish certain tasks. One true tool for it all.

# Project State: Windows Voice & Vision Assistant
**Last Updated:** Phase 1 Initialization

## Active Modules
*   **Module 01:** `MOD-01_dual_input_v0.1.0.py`
    *   **Status:** Scaffolding & Process Isolation.
    *   **Core Tech:** `multiprocessing`, `multiprocessing.Queue`, `cv2`.
    *   **Design Pattern:** Main Coordinator with Daemon Workers.

## Inter-Module Interfaces
*   `event_queue` (multiprocessing.Queue): 
    *   *Format:* Dict `{"source": str, "event": str}`
    *   *Producers:* `audio_worker`, `vision_worker`
    *   *Consumer:* Main Coordinator Loop

## Pending / Next Steps
*   Integrate Picovoice Porcupine into `audio_worker` (Phase 2).
*   Integrate MediaPipe into `vision_worker` (Phase 3).
*   Design the LLM Intent Router (Phase 4).
  
-----------------------------------------------------------------------------------------------

# Project State: Windows Voice & Vision Assistant
**Last Updated:** Phase 2 - Gesture Engine

## Active Modules
*   **Module 01:** `MOD-01_dual_input_v0.1.0.py`
    *   **Status:** Scaffolding complete. Dual multiprocessing daemons running.
*   **Module 02:** `MOD-02_gesture_engine_v0.1.0.py`
    *   **Status:** Core logic constructed. Standalone testing active.
    *   **Core Tech:** `mediapipe`, Euclidean geometry, Temporal Debouncing.
    *   **Design Pattern:** Finite State Machine / Class Wrapper.

## Inter-Module Interfaces
*   `GestureEngine` (Class):
    *   *Input:* Raw BGR video frame (`numpy.ndarray`).
    *   *Output:* String (`"GESTURE_PALM"`) or `None` (filtered via 10-frame debounce).

## Pending / Next Steps
*   Inject `MOD-02` into the `vision_worker` of `MOD-01` (Phase 2.5).
*   Integrate Picovoice Porcupine into `audio_worker` (Phase 3).

-----------------------------------------------------------------------------------------------

In MOD-02_gesture_engine_v0.1.1.py, the palm detection works perfectly, but the pinch gesture is failing to register. The output logs (like feedback tensor warnings) look normal, so this is a logic issue with the pinch math. I suspect the Euclidean distance threshold for the pinch is not scale-invariant.

To achieve scale invariance, we must shift from calculating absolute distance to calculating a distance ratio. We need to find a biomechanically stable part of the hand that does not bend or stretch, calculate its length, and use that as our denominator. While bounding box normalisation could've been a suitable fix, If you open your fingers wide, the bounding box grows. If you curl them, it shrinks. The denominator would be unstable, causing our ratio $R$ to fluctuate wildly based on what the other fingers are doing. Hence the Biomechanical Anchor Normalization, in which the metacarpal bones in the palm are rigidly connected. The distance between the wrist and the knuckle does not physically change, no matter how the fingers flex. By using the Wrist (0) to Pinky MCP (17) distance as $D_{\text{ref}}$, we get an incredibly stable denominator that scales perfectly as the hand moves closer or further from the camera.

# Project State: Windows Voice & Vision Assistant
**Last Updated:** Phase 2 - Gesture Engine (Hotfix)

## Active Modules
*   **Module 01:** `MOD-01_dual_input_v0.1.0.py`
    *   **Status:** Scaffolding complete. Dual multiprocessing daemons running.
*   **Module 02:** `MOD-02_gesture_engine_v0.1.1.py` (UPDATED)
    *   **Status:** Refactored to bypass legacy API `AttributeError`. Standalone testing active.
    *   **Core Tech:** `mediapipe.tasks.python.vision`, `hand_landmarker.task`, Euclidean geometry, Temporal Debouncing.
    *   **Design Pattern:** Finite State Machine / Class Wrapper.

-----------------------------------------------------------------------------------------------


