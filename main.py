from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Union, Tuple
import os
import tempfile
import uvicorn
from lip_sync_system import LipSyncSystem

class TextRequest(BaseModel):
    text: str
    mode: str = "simple"

app = FastAPI(
    title="Lip Sync API", 
    description="API for converting text and audio to lip sync visemes",
    version="1.0.0"
)

lip_sync = LipSyncSystem("static_viseme_map.json")

@app.get("/")
async def root():
    return {
        "api": "Lip Sync System API",
        "version": "1.0.0",
        "endpoints": [
            {"path": "/process/text", "method": "POST", "description": "Process text to phonemes"},
            {"path": "/process/audio", "method": "POST", "description": "Process audio file to visemes"},
            {"path": "/generate/audio", "method": "POST", "description": "Generate phoneme timing from text"}
        ]
    }

@app.post("/process/text")
async def process_text(request: TextRequest):
    try:
        if request.mode not in ["simple", "predictive"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid mode: {request.mode}. Must be 'simple' or 'predictive'"
            )
        
        lip_sync.set_mode(request.mode)
        phonemes = lip_sync.convert_phoneme_sequence(request.text)
        
        return {
            "success": True,
            "input_text": request.text,
            "phonemes": phonemes,
            "mode": request.mode
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/audio")
async def process_audio(
    audio_file: UploadFile = File(...),
    rhubarb_path: str = Form(...),
    output_format: str = Form("json")
):
    try:
        lip_sync.set_rhubarb_path(rhubarb_path)
        lip_sync.set_mode("rhubarb")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1]) as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file.flush()
            
            temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".txt").name
            
            viseme_data = lip_sync.process_audio_file(temp_file.name, temp_output)
            
            if output_format == "json":
                result = {
                    "success": True,
                    "viseme_data": [{"timestamp": t, "viseme": v} for t, v in viseme_data]
                }
            elif output_format == "timeline":
                timeline = "\n".join([f"{t:.3f} {v}" for t, v in viseme_data])
                result = {
                    "success": True,
                    "timeline": timeline
                }
            else:
                result = {
                    "success": True,
                    "viseme_data": viseme_data
                }
                
            os.unlink(temp_file.name)
            os.unlink(temp_output)
            
            return result
            
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/audio")
async def generate_audio(text: str = Form(...)):
    try:
        phonemes = lip_sync.generate_phoneme_timing(text)
        
        # This would be where you'd call a text-to-speech service
        # For demonstration, we're just creating a placeholder URL
        audio_url = f"C:\\Users\\dell\\Downloads\\harvard.mp3"
        
        return {
            "text": text,
            "phonemes": phonemes,
            "audio_url": audio_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)