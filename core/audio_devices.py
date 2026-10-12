import sounddevice as sd
import numpy as np
import logging

logger = logging.getLogger("AudioDevices")

def query_clean_devices():
    """
    Returns a filtered, deduplicated list of audio input (mic) and output (speaker) devices.
    Skips pseudo-devices (like Sound Mapper) and maps clean names.
    """
    devices = sd.query_devices()
    host_apis = sd.query_hostapis()
    
    mics = []
    speakers = []

    for idx, dev in enumerate(devices):
        name = dev['name']
        # Filter out pseudo-devices
        if "mapper" in name.lower() or "primary sound driver" in name.lower():
            continue
            
        if dev['max_input_channels'] > 0:
            mics.append({"id": idx, "name": name, "channels": dev['max_input_channels']})
            
        if dev['max_output_channels'] > 0:
            speakers.append({"id": idx, "name": name, "channels": dev['max_output_channels']})
            
    return mics, speakers

def get_device_index_by_name(name, kind='input'):
    """Finds the device index matching a stored name, falling back to default if not found."""
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        if name and name.lower() in dev['name'].lower():
            if kind == 'input' and dev['max_input_channels'] > 0:
                return idx
            elif kind == 'output' and dev['max_output_channels'] > 0:
                return idx
    return None