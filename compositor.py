import subprocess
import os
import httpx
import tempfile

async def compose_video(
    character_url: str,
    background_url: str, 
    lip_sync_video_url: str,
    audio_bytes: bytes,
    output_path: str
) -> str:
    """Compose final video with background, character, and audio"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Download all assets
        bg_path = os.path.join(tmpdir, "background.png")
        lipsync_path = os.path.join(tmpdir, "lipsync.mp4")
        audio_path = os.path.join(tmpdir, "audio.mp3")

        async with httpx.AsyncClient() as client:
            # Background
            r = await client.get(background_url, timeout=60)
            with open(bg_path, "wb") as f:
                f.write(r.content)

            # Lip sync video
            r = await client.get(lip_sync_video_url, timeout=60)
            with open(lipsync_path, "wb") as f:
                f.write(r.content)

        # Audio
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)

        # Get audio duration
        result = subprocess.run([
            "ffprobe", "-v", "quiet", "-show_entries",
            "format=duration", "-of", "csv=p=0", audio_path
        ], capture_output=True, text=True)
        audio_duration = float(result.stdout.strip())

        # Loop character video to match audio duration
        looped_path = os.path.join(tmpdir, "looped.mp4")
        subprocess.run([
            "ffmpeg", "-stream_loop", "-1",
            "-i", lipsync_path,
            "-t", str(audio_duration),
            "-c", "copy", looped_path, "-y"
        ], check=True)

        # Compose: background + character overlay + audio + Ken Burns zoom
        final_path = os.path.join(tmpdir, "final.mp4")
        subprocess.run([
            "ffmpeg",
            "-i", bg_path,
            "-i", looped_path,
            "-i", audio_path,
            "-filter_complex",
            "[0:v]scale=1920:1080,zoompan=z='min(zoom+0.0005,1.2)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080[bg];"
            "[1:v]scale=600:-1[char];"
            "[bg][char]overlay=(W-w)/2:H-h-50[out]",
            "-map", "[out]",
            "-map", "2:a",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            final_path, "-y"
        ], check=True)

        # Copy to output
        import shutil
        shutil.copy(final_path, output_path)

    return output_path
