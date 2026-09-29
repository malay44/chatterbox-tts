---
name: chatterbox-tts
description: "Local, offline text-to-speech with Resemble AI's Chatterbox-Turbo (MIT) in a shared, ready-made Python venv. Use when asked to generate speech, voice-over, narration, audio for a video, read text aloud to a file, or clone a voice from a reference clip. Produces 24 kHz WAV files; nothing is sent to a cloud TTS service."
---

# chatterbox-tts

Natural-sounding English TTS that runs on this Mac (Apple GPU via MPS). About 2.5× faster than real time with Turbo.

## Use it

One entry point. It creates the venv on first use, so there's nothing to activate:

```sh
T=~/.claude/skills/chatterbox-tts/scripts/tts

$T "Hello from Chatterbox." -o hello.wav              # one line
echo "Read this aloud." | $T - -o read.wav            # from stdin
$T --json lines.json --out-dir vo/                     # many lines → vo/<key>.wav + vo/durations.json
$T "Same text, my voice." --voice me.wav -o me.wav     # clone from a >5 s reference WAV
$T "Quick draft." --nano -o draft.wav                  # 110M Nano: faster; needs chatterbox from git, not PyPI 0.1.7
```

`lines.json` is a JSON object `{"intro": "text…", "outro": "text…"}`. Keys become file names. Use `durations.json` to pace video or slides to the audio.

**Text tips**
- Write words the way they're spoken; Turbo reads "PDF.js", "DynamoDB" and "HTTP" fine.
- Spell out numbers where the reading could be ambiguous ("four hundred and twenty megabytes").
- Paralinguistic tags work inline: `[laugh]`, `[chuckle]`, `[cough]`, `[sigh]`. Leave them out of professional narration.
- Keep each line to one or two sentences. Long paragraphs drift. Split them and concatenate.

**Adding audio to a video (ffmpeg)**: offset each clip to its cue time and mix:
`-filter_complex "[1:a]adelay=1500|1500[a1];[2:a]adelay=10600|10600[a2];[a1][a2]amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-1.5,apad[a]" -map 0:v -map "[a]" -c:a aac -b:a 96k -shortest`

## Layout

| What | Where |
|---|---|
| venv (Python 3.11, ~1.4 GB) | `~/.local/share/chatterbox-tts/venv` (override with `CHATTERBOX_HOME`) |
| model weights | `~/.cache/huggingface/hub/models--ResembleAI--chatterbox-turbo` (downloaded on first run) |
| scripts | `scripts/tts` (entry point), `scripts/tts.py` (CLI), `scripts/setup.sh` (build or repair the venv) |
| dependency pins | `requirements.txt` |

To use it from your own Python, run with the venv interpreter:
`~/.local/share/chatterbox-tts/venv/bin/python` → `from chatterbox.tts_turbo import ChatterboxTurboTTS`.

## Gotchas

- **Don't `pip install chatterbox-tts` normally.** Upstream pins torch 2.6.0, transformers 5.2.0 and diffusers 0.29.0. All three have OSV advisories, and the `savvas-scfw` pip firewall blocks them. `setup.sh` installs chatterbox with `--no-deps`, then the patched set in `requirements.txt`, and still goes through scfw. `gradio` is left out: only chatterbox's demo web apps use it.
- **Saving audio:** torchaudio 2.11's `save()` needs `torchcodec`, so the CLI writes files with `soundfile`.
- **`PYTORCH_ENABLE_MPS_FALLBACK=1`** is set by the entry point; a few ops don't run on the Mac GPU.
- **Output carries an inaudible Perth watermark**, added by Resemble AI.
- **Broken venv** (for example after a Python upgrade): `rm -rf ~/.local/share/chatterbox-tts/venv && scripts/setup.sh`.
