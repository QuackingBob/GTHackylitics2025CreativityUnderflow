# app/consumers.py
import json
import io
import numpy as np
import torch
from channels.generic.websocket import AsyncWebsocketConsumer
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
model_id = "openai/whisper-large-v3-turbo"  # Or your chosen model

class TranscriptionConsumer(AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = None
        self.processor = None
        self.pipe = None
        self.audio_buffer = []  # Buffer for audio chunks

    async def connect(self):
        await self.accept()
        # Initialize Whisper when a client connects (lazy loading)
        if self.model is None:
            self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
                model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
            )
            self.model.to(device)
            self.processor = AutoProcessor.from_pretrained(model_id)
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=self.model,
                tokenizer=self.processor.tokenizer,
                feature_extractor=self.processor.feature_extractor,
                torch_dtype=torch_dtype,
                device=device,
                chunk_length_s=5, # Process 5 second chunks, adjust as needed.
                batch_size=8,  # Batch size for processing
            )

    async def disconnect(self, close_code):
        # Clean up if needed (e.g., release model resources)
        pass


    async def receive(self, text_data=None, bytes_data=None):
        if bytes_data:
            # Convert bytes to NumPy array
            audio_chunk = np.frombuffer(bytes_data, dtype=np.float32)
            self.audio_buffer.append(audio_chunk)

            # Check if we have enough data to process (e.g., ~1 second)
            if len(self.audio_buffer) * 0.02 >= 1.0:  # Assuming 0.02s chunks, adjust as needed
                combined_audio = np.concatenate(self.audio_buffer)
                self.audio_buffer = []  # Clear the buffer
                try:
                    # Process the audio using your pipeline
                    result = self.pipe(combined_audio, generate_kwargs={"language":"english"})  # Add language and other kwargs
                    transcription = result["text"]

                    # Send the transcription back to the client
                    await self.send(text_data=json.dumps({"transcription": transcription}))
                except Exception as e:
                    await self.send(text_data=json.dumps({"error": str(e)}))

        elif text_data:
            text_data_json = json.loads(text_data)
            if 'stop' in text_data_json:
                # Handle stop command, potentially process remaining audio
                if self.audio_buffer:
                    combined_audio = np.concatenate(self.audio_buffer)
                    self.audio_buffer = []
                    result = self.pipe(combined_audio, generate_kwargs={"language":"english"}) # Adjust parameters.
                    transcription = result["text"]
                    await self.send(text_data=json.dumps({"transcription": transcription, 'final': True}))
                await self.send(text_data=json.dumps({'status': 'stopped'}))