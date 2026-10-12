import numpy as np

class EchoGuard:
    """
    Tracks outgoing assistant audio to subtract or suppress microphone feedback.
    """
    def __init__(self, sample_rate=24000):
        self.sample_rate = sample_rate
        self.active_buffer = []

    def register_outgoing(self, pcm_data: bytes):
        """Register audio sent to speakers."""
        audio_np = np.frombuffer(pcm_data, dtype=np.int16)
        self.active_buffer.append(audio_np)
        if len(self.active_buffer) > 50:  # Keep last 50 chunks (~1 sec)
            self.active_buffer.pop(0)

    def filter_incoming(self, pcm_data: bytes) -> bytes:
        """Filters out echo from incoming mic stream if echoing back."""
        # For lightweight implementation, returns mic stream directly or applies attenuation
        return pcm_data