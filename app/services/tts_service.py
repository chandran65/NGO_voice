import os
import io
import sys
import asyncio
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import Tuple
from app.config import AUDIO_DIR, BASE_DIR
from app.services.elevenlabs_tts import ElevenLabsTTSService

logger = logging.getLogger(__name__)

TTS_AUDIO_DIR = AUDIO_DIR / "tts"
TTS_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

class DynamicTTSService:
    @staticmethod
    def generate_piper_tamil_tts(text: str, output_mp3_path: Path, voice: str = "HemaLatha") -> bool:
        """
        Synthesizes natural Tamil speech using Hugging Face Piper ONNX models:
        - ta_IN-HemaLatha-medium (Female)
        - ta_IN-ValluvarNeural-medium (Male)
        """
        try:
            model_name = "ta_IN-HemaLatha-medium" if voice == "HemaLatha" else "ta_IN-ValluvarNeural-medium"
            model_path = BASE_DIR / "piper_voices" / model_name / f"{model_name}.onnx"
            if not model_path.exists():
                return False

            piper_bin = BASE_DIR / ".venv" / "bin" / "piper"
            if not piper_bin.exists():
                piper_bin = "piper"

            wav_path = output_mp3_path.with_suffix(".wav")
            cmd = [str(piper_bin), "--model", str(model_path), "--output_file", str(wav_path)]

            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = p.communicate(input=text)

            if p.returncode == 0 and wav_path.exists() and wav_path.stat().st_size > 0:
                try:
                    import imageio_ffmpeg
                    from pydub import AudioSegment
                    AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()
                    sound = AudioSegment.from_wav(str(wav_path))
                    sound.export(str(output_mp3_path), format="mp3")
                    if os.path.exists(wav_path):
                        os.unlink(str(wav_path))
                    return True
                except Exception as e:
                    logger.warning(f"Piper wav->mp3 conversion note: {e}")
                    # Rename wav to output path if mp3 fails
                    if wav_path.exists():
                        wav_path.rename(output_mp3_path)
                        return True
        except Exception as ex:
            logger.warning(f"Piper TTS synthesis note: {ex}")
        return False

    @staticmethod
    def generate_tts_audio(text: str, language: str = "ta", voice: str = "HemaLatha") -> Tuple[str, str]:
        """
        Generates dynamic studio-quality human voice audio for personalized responses.
        Uses Piper Tamil ONNX Models / ElevenLabs / Microsoft Edge Neural Voice / gTTS.
        Returns (relative_url, absolute_path).
        """
        if not text:
            return "audio/ta/greeting.mp3", str(AUDIO_DIR / "ta" / "greeting.mp3")

        # Compute hash of text for caching
        text_hash = hashlib.md5(f"{language}:{voice}:{text}".encode("utf-8")).hexdigest()[:12]
        filename = f"tts_{language}_{text_hash}.mp3"
        abs_path = TTS_AUDIO_DIR / filename
        rel_path = f"audio/tts/{filename}"

        if abs_path.exists():
            return rel_path, str(abs_path)

        # 1. Try Hugging Face Piper Tamil ONNX Neural Voice for Tamil
        if language == "ta":
            success = DynamicTTSService.generate_piper_tamil_tts(text, abs_path, voice=voice)
            if success and abs_path.exists():
                logger.info(f"Generated Piper Tamil Neural Speech [{voice}] for '{text[:30]}...' -> {rel_path}")
                return rel_path, str(abs_path)

        # 2. Try ElevenLabs Voice Cloning if API key present
        eleven_labs = ElevenLabsTTSService()
        if eleven_labs.is_available():
            try:
                audio_bytes = eleven_labs.generate_speech_mp3(text, output_path=abs_path)
                if audio_bytes and abs_path.exists():
                    logger.info(f"Generated ElevenLabs human cloned speech for '{text[:30]}...' -> {rel_path}")
                    return rel_path, str(abs_path)
            except Exception as e:
                logger.warning(f"ElevenLabs synthesis note: {e}")

        # 3. Try Microsoft Edge Neural Voice
        try:
            import edge_tts
            voice_name = "ta-IN-PallaviNeural" if language == "ta" else "en-IN-NeerjaNeural"
            
            async def _synthesize():
                communicate = edge_tts.Communicate(text, voice_name)
                await communicate.save(str(abs_path))
                
            asyncio.run(_synthesize())
            if abs_path.exists():
                logger.info(f"Generated Edge Neural Speech ({voice_name}) -> {rel_path}")
                return rel_path, str(abs_path)
        except Exception as e:
            logger.warning(f"Edge-TTS synthesis note ({e}), falling back to gTTS.")

        # 4. Fallback gTTS
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(str(abs_path))
            logger.info(f"Generated dynamic gTTS audio -> {rel_path}")
            return rel_path, str(abs_path)
        except Exception as e:
            logger.warning(f"gTTS audio generation note: {e}")

        default_rel = f"audio/{language}/greeting.mp3"
        default_abs = AUDIO_DIR / language / "greeting.mp3"
        return default_rel, str(default_abs)
