"""Audio analysis with librosa: BPM, onsets, and mapping to R2Beat coords."""

import numpy as np

try:
    import librosa
    HAS_LIBROSA = True
except Exception:  # pragma: no cover
    HAS_LIBROSA = False


def _check():
    if not HAS_LIBROSA:
        raise RuntimeError(
            "librosa is not installed. Run: pip install librosa soundfile"
        )


def load(path, sr=44100, mono=True):
    _check()
    return librosa.load(path, sr=sr, mono=mono)


def detect_bpm(path, start_bpm=70, end_bpm=220):
    y, sr = load(path)
    tempo, _ = librosa.beat.beat_track(
        y=y, sr=sr, start_bpm=start_bpm, units="frames"
    )
    return float(np.atleast_1d(tempo)[0])


def detect_onsets(path, top_n=None, sr=44100, min_strength=0.1):
    y, sr = load(path, sr=sr)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    times = librosa.times_like(onset_env, sr=sr)
    peaks = librosa.util.peak_pick(
        onset_env,
        pre_max=5,
        post_max=5,
        pre_avg=5,
        post_avg=15,
        delta=min_strength,
        wait=3,
    )
    onsets = [float(times[p]) for p in peaks]
    if top_n and len(onsets) > top_n:
        strengths = [(onset_env[p], times[p]) for p in peaks]
        strengths.sort(reverse=True)
        entries = sorted(s for _, s in strengths[:top_n])
        onsets = [float(e) for e in entries]
    return onsets


def onsets_to_coords(onsets, bpm):
    from .timing import coord_from_seconds

    return [coord_from_seconds(t, bpm) for t in onsets]


def detect_leading_silence_frames(path, sr=44100):
    y, sr = load(path, sr=sr)
    if len(y) == 0:
        return 0
    abs_y = np.abs(y)
    frame_size = int(0.02 * sr)
    for i in range(0, len(abs_y) - frame_size, frame_size):
        if np.max(abs_y[i : i + frame_size]) > 1e-3:
            return int(i / sr * 60)
    return 0


def summary(path):
    _check()
    y, sr = load(path)
    duration = len(y) / sr
    bpm = detect_bpm(path)
    onsets = detect_onsets(path, top_n=200)
    return {
        "duration_sec": round(duration, 2),
        "bpm": round(bpm, 2),
        "num_onsets": len(onsets),
        "first_onset_sec": round(onsets[0], 3) if onsets else None,
        "leading_silence_frames": detect_leading_silence_frames(path, sr),
        "sample_rate": sr,
    }