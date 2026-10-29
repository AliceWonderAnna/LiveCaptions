"""Offline speech-to-text for media files (mp4/mp3/m4a/wav/mkv)."""
from __future__ import annotations

import threading
from pathlib import Path

from audio_engine import cpu_thread_count
from paths import model_cache_dir
from transcript_export import is_supported_media, write_srt


class FileEngine:
    def __init__(self, settings, path, segment, status, error, done):
        self.settings = settings.copy()
        self.path = Path(path)
        self.segment = segment
        self.status = status
        self.error = error
        self.done = done
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.srt_path = None

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def run(self):
        try:
            if not is_supported_media(self.path):
                raise ValueError(f'Niet-ondersteund bestandstype: {self.path.suffix}')
            if not self.path.is_file():
                raise FileNotFoundError(f'Bestand niet gevonden: {self.path}')

            self.status('Bestand laden…')
            from faster_whisper.audio import decode_audio
            audio = decode_audio(str(self.path), sampling_rate=16000)
            if self.stop_event.is_set():
                return

            from faster_whisper import WhisperModel
            threads = cpu_thread_count()
            self.status('Model laden…')
            model = WhisperModel(
                self.settings['model'],
                device='cpu',
                compute_type='int8',
                cpu_threads=threads,
                download_root=str(model_cache_dir()),
            )
            if self.stop_event.is_set():
                return

            language = None if self.settings['language'] == 'auto' else self.settings['language']
            self.status(f'Transcriberen… {self.path.name}')
            segments_iter, _info = model.transcribe(
                audio,
                language=language,
                beam_size=1,
                vad_filter=True,
                condition_on_previous_text=True,
                without_timestamps=False,
            )

            collected = []
            iterator = iter(segments_iter)
            while not self.stop_event.is_set():
                try:
                    item = next(iterator)
                except StopIteration:
                    break
                text = (item.text or '').strip()
                if not text:
                    continue
                collected.append(item)
                self.segment(text, float(item.start or 0), float(item.end or 0))

            if self.stop_event.is_set():
                self.status('Bestand-STT gestopt.')
                return

            self.srt_path = write_srt(self.path, collected)
            self.status(f'Klaar · opgeslagen: {self.srt_path.name}')
        except Exception as exc:
            self.error(f'Bestand-STT: {type(exc).__name__}: {exc}')
        finally:
            self.stop_event.set()
            self.done()
