import os
import sys
import time
import io
import wave
import json
import numpy as np
import sounddevice as sd
import soundfile as sf
from openai import OpenAI

from memory.config_manager import load_config, get_openai_key
from core.audio_devices import get_device_index_by_name
from actions.pc_tools import TOOLS_SCHEMA, execute_tool

print("Initializing Nova with Computer Control Tools...")

class AssistantCore:
    def __init__(self):
        self.config = load_config()
        self.api_key = get_openai_key()
        self.assistant_name = self.config.get("assistant_name", "Nova")
        self.voice = self.config.get("voice", "alloy")
        
        self.sample_rate = 16000
        self.channels = 1
        self.client = OpenAI(api_key=self.api_key)
        self.running = True

    def load_system_prompt(self):
        prompt_path = os.path.join("core", "prompt.txt")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                template = f.read()
            return template.format(
                name=self.assistant_name,
                os_name=sys.platform,
                tools_list="open_application, search_web, get_system_info"
            )
        return f"You are {self.assistant_name}, a helpful personal assistant with computer control tools."

    def record_audio(self):
        mic_device_idx = get_device_index_by_name(self.config.get("mic_device"), 'input')
        print(f"\n🎙️ [{self.assistant_name}] is listening... Speak now (Press Ctrl+C to exit).")
        
        silence_threshold = 0.015
        silence_limit = 1.5
        chunk_duration = 0.1
        chunk_samples = int(self.sample_rate * chunk_duration)
        
        audio_frames = []
        silent_chunks = 0
        max_silent_chunks = int(silence_limit / chunk_duration)
        recording_started = False

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype='float32',
            device=mic_device_idx
        ) as stream:
            while self.running:
                data, overflowed = stream.read(chunk_samples)
                volume = np.linalg.norm(data) * 10 / np.sqrt(chunk_samples)
                
                if volume > silence_threshold:
                    if not recording_started:
                        print("🔴 Speech detected, recording...")
                        recording_started = True
                    audio_frames.append(data.copy())
                    silent_chunks = 0
                elif recording_started:
                    audio_frames.append(data.copy())
                    silent_chunks += 1
                    if silent_chunks > max_silent_chunks:
                        print("⏹️ Speech ended. Processing...")
                        break

        if not audio_frames:
            return None

        audio_data = np.concatenate(audio_frames, axis=0)
        wav_buffer = io.BytesIO()
        audio_int16 = (audio_data * 32767).astype(np.int16)
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())
        wav_buffer.seek(0)
        wav_buffer.name = "voice_input.wav"
        return wav_buffer

    def transcribe_audio(self, audio_file):
        print("📝 Transcribing audio with Whisper...")
        transcript = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        return transcript.text

    def get_gpt_response(self, user_text):
        print(f"🤖 Thinking (GPT-4o Mini): \"{user_text}\"")
        messages = [
            {"role": "system", "content": self.load_system_prompt()},
            {"role": "user", "content": user_text}
        ]
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        # Check if model wants to call a tool
        if response_message.tool_calls:
            messages.append(response_message)
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"🛠️ Executing tool [{function_name}] with args {function_args}...")
                tool_result = execute_tool(function_name, function_args)
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": tool_result
                })
            
            # Second call to get final conversational response after tool execution
            second_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            return second_response.choices[0].message.content
            
        return response_message.content

    def speak_response(self, text):
        print(f"🗣️ [{self.assistant_name}]: {text}")
        speaker_device_idx = get_device_index_by_name(self.config.get("speaker_device"), 'output')
        
        speech_response = self.client.audio.speech.create(
            model="tts-1",
            voice=self.voice,
            input=text
        )
        
        audio_stream = io.BytesIO(speech_response.content)
        data, samplerate = sf.read(audio_stream)
        sd.play(data, samplerate=samplerate, device=speaker_device_idx)
        sd.wait()

    def start(self):
        print(f"✨ Nova is online with computer control enabled!")
        while self.running:
            try:
                audio_file = self.record_audio()
                if not audio_file:
                    continue
                
                user_text = self.transcribe_audio(audio_file)
                if not user_text.strip():
                    print("⚠️ No speech recognized. Try again.")
                    continue
                
                print(f"You: {user_text}")
                
                reply_text = self.get_gpt_response(user_text)
                self.speak_response(reply_text)
                
            except Exception as e:
                print(f"❌ Error in conversation loop: {e}")
                time.sleep(1)

if __name__ == "__main__":
    assistant = AssistantCore()
    try:
        assistant.start()
    except KeyboardInterrupt:
        print("\nAssistant stopped by user.")