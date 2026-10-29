"""Capture and inference on separate daemon threads; RAM queues only."""
import os
import queue
import threading
import time
from core import Segmenter, mono_16k
from paths import model_cache_dir

STALE_SECONDS = 1.0


def cpu_thread_count(requested=8, available=None):
    """Cap Whisper intra-threads at 8, or fewer if the machine has fewer cores."""
    cores = available if available is not None else os.cpu_count()
    return max(1, min(requested, cores or requested))


def offer_job(jobs, stamp, samples, final):
    """Keep only the newest audio so captions stay live. Returns True if an older job was dropped."""
    dropped = False
    if jobs.full():
        try:
            jobs.get_nowait()
            dropped = True
        except queue.Empty:
            pass
    jobs.put_nowait((stamp, samples, final))
    return dropped


class Engine:
    def __init__(self, settings, caption, status, error, done):
        self.settings = settings.copy()
        self.caption, self.status, self.error, self.done = caption, status, error, done
        self.stop_event = threading.Event()
        self.jobs = queue.Queue(maxsize=1)
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def run(self):
        capture = None
        try:
            from faster_whisper import WhisperModel
            threads = cpu_thread_count()
            self.status('Model laden… Eerste keer: download; dit kan enkele minuten duren.')
            model = WhisperModel(
                self.settings['model'],
                device='cpu',
                compute_type='int8',
                cpu_threads=threads,
                download_root=str(model_cache_dir()),
            )
            if self.stop_event.is_set():
                return
            capture = threading.Thread(target=self.capture, daemon=True)
            capture.start()
            language = None if self.settings['language'] == 'auto' else self.settings['language']
            while not self.stop_event.is_set():
                try:
                    stamp, samples, final = self.jobs.get(timeout=.2)
                except queue.Empty:
                    continue
                if time.monotonic() - stamp > STALE_SECONDS:
                    continue
                segments, _ = model.transcribe(
                    samples, language=language, beam_size=1,
                    vad_filter=False, condition_on_previous_text=False,
                    without_timestamps=True,
                )
                text = ' '.join(s.text.strip() for s in segments if s.no_speech_prob < .65).strip()
                if text and not self.stop_event.is_set():
                    self.caption(text, final)
        except Exception as exc:
            self.error(f'Herkenning: {type(exc).__name__}: {exc}')
        finally:
            self.stop_event.set()
            if capture:
                capture.join(timeout=3)
            self.done()

    def capture(self):
        pa = stream = None
        try:
            import pyaudiowpatch as audio
            from audio_devices import resolve_device
            pa = audio.PyAudio()
            device = resolve_device(pa, self.settings)
            rate = int(device['defaultSampleRate'])
            channels = int(device['maxInputChannels'])
            if channels < 1:
                raise RuntimeError('Geen audiokanalen op dit apparaat')
            block = int(rate * .1)
            segmenter = Segmenter(
                self.settings['threshold'],
                self.settings['max_seconds'],
                self.settings['silence_seconds'],
                self.settings['partial_seconds'],
            )
            def callback(raw, count, timing, flags):
                try:
                    if self.stop_event.is_set():
                        return None, audio.paComplete
                    if flags:
                        self.status('Audio-overloop: een kort stukje geluid kan ontbreken.')
                    chunk = segmenter.push(mono_16k(raw, channels, rate))
                    if chunk is not None:
                        if offer_job(self.jobs, time.monotonic(), chunk.samples, chunk.final):
                            self.status('CPU loopt achter; nieuwste audio wordt gebruikt. Probeer model tiny.')
                    return None, audio.paContinue
                except Exception as exc:
                    self.error(f'Audioverwerking: {exc}')
                    self.stop_event.set()
                    return None, audio.paAbort
            stream = pa.open(format=audio.paFloat32, channels=channels, rate=rate, input=True,
                             input_device_index=device['index'], frames_per_buffer=block,
                             stream_callback=callback)
            self.status(f'Luistert naar: {device["name"]} · {cpu_thread_count()} CPU-threads')
            while not self.stop_event.wait(.15):
                if not stream.is_active():
                    raise RuntimeError('Audioapparaat gestopt. Controleer de aansluiting en start opnieuw.')
        except Exception as exc:
            self.error(f'Audio: {type(exc).__name__}: {exc}')
            self.stop_event.set()
        finally:
            if stream:
                stream.close()
            if pa:
                pa.terminate()
