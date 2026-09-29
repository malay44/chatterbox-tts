#!/usr/bin/env python
"""Local text-to-speech with Chatterbox-Turbo (Resemble AI, MIT).

One line:
  tts "Hello there." -o hello.wav
Many lines (e.g. video narration), JSON object {key: text}:
  tts --json lines.json --out-dir vo/        # vo/<key>.wav + vo/durations.json
Options:
  --voice ref.wav    clone a voice from a >5 s reference clip (default: built-in voice)
  --nano             110M Nano model instead of 350M Turbo (faster, a bit lower quality)
  --device cpu|mps|cuda   default: mps if available, else cpu

Text may contain Turbo's paralinguistic tags: [laugh] [chuckle] [cough] [sigh] …
Output: 24 kHz mono WAV. Chatterbox embeds an inaudible Perth watermark.
"""
import argparse
import json
import pathlib
import sys
import time


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("text", nargs="?", help="text to speak (or '-' for stdin)")
    p.add_argument("-o", "--out", default="out.wav", help="output WAV for single-text mode")
    p.add_argument("--json", help="JSON file {key: text}; writes <out-dir>/<key>.wav")
    p.add_argument("--out-dir", default=".", help="output folder for --json mode")
    p.add_argument("--voice", help="reference WAV (>5 s) for voice cloning")
    p.add_argument("--nano", action="store_true", help="use Chatterbox-Nano")
    p.add_argument("--device", help="cpu | mps | cuda")
    a = p.parse_args()

    if a.json:
        lines = json.loads(pathlib.Path(a.json).read_text())
    elif a.text:
        lines = {pathlib.Path(a.out).stem: sys.stdin.read().strip() if a.text == "-" else a.text}
    else:
        p.error("give TEXT or --json FILE")

    import soundfile as sf  # torchaudio 2.11's save() needs torchcodec; soundfile doesn't
    import torch
    from chatterbox.tts_turbo import ChatterboxTurboTTS

    device = a.device or ("mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
    t = time.time()
    # nano= exists on chatterbox's master branch but not in PyPI 0.1.7 (installed here).
    kwargs = {"nano": True} if a.nano else {}
    try:
        model = ChatterboxTurboTTS.from_pretrained(device=device, **kwargs)  # weights cached in ~/.cache/huggingface
    except TypeError as e:
        if a.nano:
            sys.exit("--nano needs a newer chatterbox than PyPI 0.1.7 (pip install git+https://github.com/resemble-ai/chatterbox --no-deps into the venv)")
        raise
    print(f"loaded {'nano' if a.nano else 'turbo'} on {device} in {time.time() - t:.1f}s", file=sys.stderr)

    if a.voice:
        model.prepare_conditionals(a.voice)

    out_dir = pathlib.Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    durations = {}
    for key, text in lines.items():
        t = time.time()
        wav = model.generate(text)
        path = out_dir / f"{key}.wav" if a.json else pathlib.Path(a.out)
        sf.write(path, wav.squeeze().cpu().numpy(), model.sr)
        durations[key] = round(wav.shape[-1] / model.sr, 3)
        print(f"{path}  {durations[key]:.2f}s audio  ({time.time() - t:.1f}s)", flush=True)

    if a.json:
        (out_dir / "durations.json").write_text(json.dumps(durations, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
