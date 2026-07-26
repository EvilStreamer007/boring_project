# MOD-03_stt_transcriber_v0.1.2.py
import numpy as np
import queue
import time
import speech_recognition as sr

# ARM OS Error Guard: sounddevice can throw OS-level errors on architectures
# like Raspberry Pi if underlying audio libraries (e.g., portaudio) are missing.
try:
    import sounddevice as sd
except OSError as e:
    print(f"[Error] OS Audio issue detected (common on ARM architectures): {e}")
    print("Ensure underlying audio dependencies like 'libportaudio2' are installed.")
    exit(1)

class SpeechTranscriber:
    """
    A completely free Speech-to-Text layer utilizing a Voice Activity Detection (VAD) 
    algorithm based on RMS energy calculations. Transcribes segmented speech using 
    Google's free Web Speech API via the speech_recognition library.
    """
    
    def __init__(self, sample_rate=16000, channels=1, energy_threshold=0.02, silence_timeout=1.5):
        # Audio configuration parameters
        self.sample_rate = sample_rate
        self.channels = channels
        
        # VAD Logic parameters
        self.energy_threshold = energy_threshold
        self.silence_timeout = silence_timeout

        # Thread-safe queue to pass audio chunks from the callback to the main thread
        self.audio_queue = queue.Queue()
        
        # State tracking variables
        self.is_recording = False
        self.silence_start_time = None
        self.audio_buffer = []
        
        # Initialize the speech_recognition recognizer object
        self.recognizer = sr.Recognizer()

    def _audio_callback(self, indata, frames, time_info, status):
        """
        Callback invoked by sounddevice for each audio block.
        Runs in a separate C-level thread; must be fast and non-blocking.
        """
        if status:
            print(f"[Audio Hardware Status] {status}")
            
        # Copy indata to avoid memory overwrite by the sounddevice backend
        self.audio_queue.put(indata.copy())

    def _calculate_rms(self, audio_chunk):
        """
        Calculates the Root Mean Square (RMS) energy of an audio chunk.
        """
        return np.sqrt(np.mean(audio_chunk**2))

    def _transcribe_audio(self, audio_data):
        """
        Converts the buffered numpy float array into PCM bytes and sends it 
        to the free Google Web Speech API for transcription.
        """
        # Mathematics of Float to PCM16:
        # The audio_data from sounddevice is a float32 array normalized between -1.0 and 1.0.
        # 16-bit PCM audio represents amplitudes as integers from -32768 to 32767.
        # We multiply by 32767 and cast to np.int16 to map the floats to standard PCM space.
        pcm_audio = np.int16(audio_data * 32767)
        
        # Extract the raw bytes from the numpy array
        byte_data = pcm_audio.tobytes()
        
        # Instantiate the sr.AudioData object required by the recognizer.
        # The '2' represents the sample width in bytes (16-bit audio = 2 bytes per sample).
        audio = sr.AudioData(byte_data, self.sample_rate, 2)
        
        try:
            # Make the free network call to the Google Web Speech API
            text = self.recognizer.recognize_google(audio)
            return f"USER_SAID: {text}"
            
        except sr.UnknownValueError:
            # Triggered if the audio contains no intelligible speech
            print("[STT Warning] Could not understand the audio.")
            return None
            
        except sr.RequestError as e:
            # Triggered if the API is unreachable (e.g., no internet connection)
            print(f"[STT Error] Could not request results from Google Speech Recognition service; {e}")
            return None

    def listen_and_transcribe(self):
        """
        Main processing loop. Opens the hardware stream, applies VAD logic,
        and dispatches complete speech events for transcription.
        """
        # Context manager ensures stream is cleanly closed on exit
        stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=self._audio_callback
        )
        
        with stream:
            print(f"[STT] Stream active (Sample Rate: {self.sample_rate}Hz). Listening...")
            
            while True:
                # Block until a chunk is available
                chunk = self.audio_queue.get()
                
                rms = self._calculate_rms(chunk)

                if rms > self.energy_threshold:
                    # Active speech detected
                    self.is_recording = True
                    self.silence_start_time = None
                    self.audio_buffer.append(chunk)
                    
                elif self.is_recording:
                    # Speech stopped, but append the quiet tail
                    self.audio_buffer.append(chunk)
                    
                    if self.silence_start_time is None:
                        self.silence_start_time = time.time()
                    
                    # Check if silence timeout is reached
                    if time.time() - self.silence_start_time > self.silence_timeout:
                        print("\n[STT] Speech pause detected, processing audio...")
                        
                        # Concatenate chunks vertically (axis=0) into a single phrase array
                        complete_audio = np.concatenate(self.audio_buffer, axis=0)
                        
                        # Transcribe the complete phrase
                        transcription = self._transcribe_audio(complete_audio)
                        if transcription:
                            print(f"[STT Result] {transcription}\n")
                        else:
                            print("[STT Result] (No transcription generated)\n")
                            
                        print("[STT] Listening for next phrase...")
                        
                        # Reset VAD trackers
                        self.is_recording = False
                        self.silence_start_time = None
                        self.audio_buffer = []


if __name__ == "__main__":
    transcriber = SpeechTranscriber()
    
    print("[Standalone] STT Transcriber v0.1.2 testing started (Free Google API).")
    print("[Standalone] Speak into your default microphone. Press Ctrl+C to quit.")
    
    try:
        transcriber.listen_and_transcribe()
        
    except KeyboardInterrupt:
        print("\n[Standalone] Keyboard interrupt received. Shutting down STT layer...")
        print("[Standalone] Cleanup complete.")