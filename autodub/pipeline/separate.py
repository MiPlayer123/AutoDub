import subprocess
from pathlib import Path
from typing import Tuple
import torch
import torchaudio
from demucs.pretrained import get_model
from demucs.apply import apply_model
from ..config import TEMP_DIR

def separate_audio(audio_path: Path, use_separation: bool = True) -> Tuple[Path, Path]:
    """
    Separate audio into vocals and background using Demucs.
    
    Args:
        audio_path: Path to input audio file
        use_separation: If True, use Demucs. If False, create simple copies.
    
    Returns:
        Tuple of (vocals_path, background_path)
    """
    vocals_path = TEMP_DIR / "vocals.wav"
    background_path = TEMP_DIR / "background.wav"
    
    if not use_separation:
        print("Source separation disabled, using original audio for both vocals and background")
        # Just copy the original file
        subprocess.run([
            'ffmpeg', '-i', str(audio_path),
            '-ar', '44100', '-ac', '2',
            '-y', str(vocals_path)
        ], capture_output=True, check=True)
        
        # Create quiet background
        subprocess.run([
            'ffmpeg', '-i', str(audio_path),
            '-ar', '44100', '-ac', '2',
            '-filter:a', 'volume=0.1',
            '-y', str(background_path)
        ], capture_output=True, check=True)
        
        return vocals_path, background_path
    
    try:
        print(f"Separating audio using Demucs: {audio_path}")
        print("Loading Demucs model...")
        
        # Load the pretrained model
        model = get_model('htdemucs')
        device = 'cpu'
        model.to(device)
        
        print("Processing audio...")
        # Load audio with torchaudio
        waveform, sample_rate = torchaudio.load(audio_path)
        
        # Ensure stereo audio
        if waveform.shape[0] == 1:
            waveform = waveform.repeat(2, 1)
        
        # Resample if needed
        if sample_rate != model.samplerate:
            resampler = torchaudio.transforms.Resample(sample_rate, model.samplerate)
            waveform = resampler(waveform)
            sample_rate = model.samplerate
        
        # Move to device
        waveform = waveform.to(device)
        
        print("Running source separation...")
        # Apply the model
        with torch.no_grad():
            waveform_batch = waveform.unsqueeze(0)
            sources = apply_model(model, waveform_batch, device=device)
        
        # Extract vocals and accompaniment
        # htdemucs outputs: [bass, drums, other, vocals]
        vocals = sources[0, 3]  # vocals are at index 3
        accompaniment = sources[0, 0] + sources[0, 1] + sources[0, 2]  # sum others
        
        # Save vocals
        torchaudio.save(vocals_path, vocals.cpu(), sample_rate)
        
        # Save background/accompaniment
        torchaudio.save(background_path, accompaniment.cpu(), sample_rate)
        
        print(f"Audio separated successfully:")
        print(f"  Vocals: {vocals_path}")
        print(f"  Background: {background_path}")
        
        return vocals_path, background_path
        
    except Exception as e:
        print(f"Source separation failed: {e}")
        print("Falling back to simple method...")
        return separate_audio(audio_path, use_separation=False)