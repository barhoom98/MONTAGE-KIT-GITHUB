"""حفظ إطارات الستيكر كفيديو شفاف عبر ffmpeg."""
import subprocess


def write_video(frames, path, size, fps=30):
    """يحفظ إطارات RGBA كملف شفاف. الصيغة من الامتداد: .webm أو .mov"""
    if path.endswith(".mov"):
        codec = ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le"]
    else:
        codec = ["-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "28",
                 "-auto-alt-ref", "0", "-row-mt", "1"]
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
           "-s", f"{size}x{size}", "-r", str(fps), "-i", "-", *codec, path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in frames:
        proc.stdin.write(f.tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError(f"ffmpeg فشل في كتابة {path}")
