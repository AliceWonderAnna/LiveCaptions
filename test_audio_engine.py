"""Tests for CPU thread capping and latest-only job queue."""
import queue

from audio_engine import cpu_thread_count, offer_job


def test_cpu_thread_count_caps_at_eight():
    assert cpu_thread_count(requested=8, available=16) == 8
    assert cpu_thread_count(requested=8, available=4) == 4
    assert cpu_thread_count(requested=8, available=1) == 1
    assert cpu_thread_count(requested=8, available=0) == 8


def test_cpu_thread_count_never_zero():
    assert cpu_thread_count(requested=8, available=None) >= 1


def test_offer_job_keeps_newest():
    jobs = queue.Queue(maxsize=1)
    assert offer_job(jobs, 1.0, 'old', False) is False
    assert offer_job(jobs, 2.0, 'new', True) is True
    stamp, samples, final = jobs.get_nowait()
    assert stamp == 2.0
    assert samples == 'new'
    assert final is True
    assert jobs.empty()
