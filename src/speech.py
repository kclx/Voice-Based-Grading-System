"""Speech recognition module for continuous audio capture and transcription."""

import speech_recognition as sr
from typing import Optional, Callable
import logging
from config import (
    SPEECH_ENGINE,
    LANGUAGE,
    ENERGY_THRESHOLD,
    PAUSE_THRESHOLD,
    PHRASE_TIME_LIMIT
)


class ContinuousSpeechRecognizer:
    """
    Continuous speech recognition system that listens without interruption.

    Key Features:
    - Single microphone initialization (no repeated setup)
    - Background listening with callback
    - Automatic energy threshold adjustment
    - Error recovery without crash
    """

    def __init__(self):
        """Initialize the speech recognizer with microphone."""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.logger = logging.getLogger(__name__)
        self.is_listening = False
        self.stop_listening = None

        # Configure recognizer
        self.recognizer.energy_threshold = ENERGY_THRESHOLD
        self.recognizer.pause_threshold = PAUSE_THRESHOLD
        self.recognizer.phrase_time_limit = PHRASE_TIME_LIMIT

        # Adjust for ambient noise on initialization
        self._calibrate_microphone()

    def _calibrate_microphone(self):
        """Calibrate microphone for ambient noise."""
        self.logger.info("Calibrating microphone for ambient noise...")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            self.logger.info(f"Microphone calibrated. Energy threshold: {self.recognizer.energy_threshold}")
        except Exception as e:
            self.logger.error(f"Microphone calibration failed: {e}")
            raise

    def _recognize_audio(self, audio) -> Optional[str]:
        """
        Convert audio to text using Google Speech Recognition.

        Args:
            audio: Audio data from microphone

        Returns:
            Optional[str]: Recognized text or None if recognition fails
        """
        try:
            text = self.recognizer.recognize_google(audio, language=LANGUAGE)
            self.logger.info(f"Recognized: {text}")
            return text
        except sr.UnknownValueError:
            self.logger.debug("Speech not understood")
            return None
        except sr.RequestError as e:
            self.logger.error(f"Could not request results from speech service: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error during recognition: {e}")
            return None

    def start_listening(self, callback: Callable[[str], None]):
        """
        Start continuous listening with callback for recognized text.

        Args:
            callback: Function to call with recognized text
        """
        if self.is_listening:
            self.logger.warning("Already listening")
            return

        def audio_callback(recognizer, audio):
            """Internal callback for processing audio."""
            text = self._recognize_audio(audio)
            if text:
                callback(text)

        try:
            self.logger.info("Starting continuous listening...")
            self.stop_listening = self.recognizer.listen_in_background(
                self.microphone,
                audio_callback,
                phrase_time_limit=PHRASE_TIME_LIMIT
            )
            self.is_listening = True
            self.logger.info("Listening started successfully")
        except Exception as e:
            self.logger.error(f"Failed to start listening: {e}")
            raise

    def stop(self):
        """Stop continuous listening and cleanup."""
        if self.stop_listening:
            self.stop_listening(wait_for_stop=False)
            self.is_listening = False
            self.logger.info("Listening stopped")

    def recalibrate(self):
        """Recalibrate microphone if environment noise changes."""
        was_listening = self.is_listening
        if was_listening:
            self.stop()

        self._calibrate_microphone()

        # Note: Cannot restart listening here as we need the callback
        # Caller should restart listening if needed
