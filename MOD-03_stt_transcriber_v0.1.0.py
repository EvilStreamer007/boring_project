# MOD-03_stt_transcriber_v0.1.0.py
import sounddevice as sd
import numpy as np
import queue
import time

class SpeechTranscriber:
    """
    A Speech-to-Text layer utilizing a Voice Activity Detection (VAD) algorithm 
    based on Root Mean Square (RMS) energy calculations to segment continuous 
    audio streams into discrete speech events.
    """
    
    def __init__(self, sample_rate=16000, channels=1, energy_threshold=0.02, silence_timeout=1.5):
        # Audio configuration parameters
        self.sample_rate = sample_rate
        self.channels = channels
        
        # VAD Logic parameters
        # energy_threshold: The volume level required to trigger the 'recording' state
        self.energy_threshold = energy_threshold
        # silence_timeout: Seconds of continuous silence required to finalize a speech event
        self.silence_timeout = silence_timeout

        # A thread-safe queue to pass audio chunks from the callback thread to the main thread
        self.audio_queue = queue.Queue()
        
        # State tracking variables
        self.is_recording = False
        self.silence_start_time = None
        self.audio_buffer = []

    def _audio_callback(self, indata, frames, time_info, status):
        """
        Callback invoked by sounddevice for each audio block.
        This runs in a separate C-level thread, so it must be fast and non-blocking.
        """
        if status:
            # Print overruns or other hardware-level stream errors
            print(f"[Audio Hardware Status] {status}")
            
        # We must copy the indata array because the original memory is reused 
        # by the sounddevice backend as soon as this callback returns.
        self.audio_queue.put(indata.copy())

    def _calculate_rms(self, audio_chunk):
        """
        Calculates the Root Mean Square (RMS) energy of an audio chunk.
        
        Mathematics:
        1. audio_chunk**2: Squares every amplitude value in the array. This makes all 
           values positive (since audio waves oscillate above and below 0) and 
           disproportionately weights louder sounds.
        2. np.mean(...): Calculates the average of these squared values.
        3. np.sqrt(...): Takes the square root to return the value back to the 
           original linear scale of the audio amplitudes.
        """
        return np.sqrt(np.mean(audio_chunk**2))

    def _mock_transcribe(self, audio_data):
        """
        Stub method representing the final STT API call.
        """
        # We print the length of the array to prove the buffer successfully 
        # collected and concatenated the individual chunks.
        print(f"[STT Stub] Captured speech segment of length {len(audio_data)} samples.")
        return "USER_SAID: [Mocked Transcription]"

    def listen_and_transcribe(self):
        """
        Main processing loop. Opens the hardware stream, reads chunks from the queue,
        applies the RMS Voice Activity Detection logic, and processes complete speech events.
        """
        # Initialize the hardware audio stream using the context manager to ensure 
        # it is properly closed even if an exception occurs.
        stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=self._audio_callback
        )
        
        with stream:
            print(f"[STT] Stream active (Sample Rate: {self.sample_rate}Hz). Listening...")
            
            while True:
                # Blocking call: waits here until the callback puts a chunk in the queue
                chunk = self.audio_queue.get()
                
                # Calculate the energy of the current chunk
                rms = self._calculate_rms(chunk)

                if rms > self.energy_threshold:
                    # User is actively speaking. 
                    # Set recording flag, reset silence timer, and buffer the audio.
                    self.is_recording = True
                    self.silence_start_time = None
                    self.audio_buffer.append(chunk)
                    
                elif self.is_recording:
                    # User was speaking, but the current chunk is quiet.
                    # We still append the chunk so the final audio doesn't cut off abruptly.
                    self.audio_buffer.append(chunk)
                    
                    # If this is the first quiet chunk after speaking, start the stopwatch.
                    if self.silence_start_time is None:
                        self.silence_start_time = time.time()
                    
                    # Check if the silence has persisted longer than our timeout threshold.
                    if time.time() - self.silence_start_time > self.silence_timeout:
                        print("\n[STT] Speech pause detected, processing audio...")
                        
                        # np.concatenate joins the list of smaller 2D arrays into one large 
                        # contiguous 2D array representing the entire spoken phrase.
                        # axis=0 means we join them vertically (end-to-end in time).
                        complete_audio = np.concatenate(self.audio_buffer, axis=0)
                        
                        # Pass the complete speech segment to the mock STT engine
                        transcription = self._mock_transcribe(complete_audio)
                        print(f"[STT Result] {transcription}\n")
                        print("[STT] Listening for next phrase...")
                        
                        # Reset the VAD state trackers for the next phrase
                        self.is_recording = False
                        self.silence_start_time = None
                        self.audio_buffer = []


if __name__ == "__main__":
    # Instantiate the transcriber with default configurations
    transcriber = SpeechTranscriber()
    
    print("[Standalone] STT Transcriber v0.1.0 testing started.")
    print("[Standalone] Speak into your default microphone. Press Ctrl+C to quit.")
    
    try:
        # Enter the infinite listening loop
        transcriber.listen_and_transcribe()
        
    except KeyboardInterrupt:
        # Gracefully handle the Ctrl+C interruption from the terminal
        print("\n[Standalone] Keyboard interrupt received. Shutting down STT layer...")
        print("[Standalone] Cleanup complete.")