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
