# -*- coding: utf-8 -*-

"""Concurrency guarantees for the production batch processor."""

import threading

from core import batch_process


def test_recommended_worker_count_follows_cpu_capacity():
    processor = batch_process.BatchProcessor

    assert processor._recommended_worker_count(1) == 1
    assert processor._recommended_worker_count(3) == 1
    assert processor._recommended_worker_count(4) == 2
    assert processor._recommended_worker_count(16) == 2


def test_batch_processor_runs_two_ocr_jobs_concurrently_and_keeps_order(
    monkeypatch,
    tmp_path,
):
    barrier = threading.Barrier(2)
    worker_threads = set()
    output_locks = []
    shared_project_service = object()

    class FakeOCRRenameService:

        def __init__(
            self,
            output_dir,
            project_service=None,
            output_lock=None,
        ):
            self.project_service = project_service or shared_project_service
            output_locks.append(output_lock)

        def process(self, image, recognition_mode='deep'):
            worker_threads.add(threading.current_thread().ident)
            barrier.wait(timeout=2.0)
            return {'status': 'success', 'source': str(image)}

    monkeypatch.setattr(
        batch_process,
        'OCRRenameService',
        FakeOCRRenameService,
    )

    processor = batch_process.BatchProcessor(
        tmp_path,
        worker_count=2,
    )
    results = processor.run(['first.jpg', 'second.jpg'])

    assert [item['source'] for item in results] == [
        'first.jpg',
        'second.jpg',
    ]
    assert len(worker_threads) == 2
    assert output_locks
    assert all(lock is output_locks[0] for lock in output_locks)


def test_batch_processor_single_file_uses_normal_service(
    monkeypatch,
    tmp_path,
):
    calls = []

    class FakeOCRRenameService:

        def __init__(
            self,
            output_dir,
            project_service=None,
            output_lock=None,
        ):
            self.project_service = project_service or object()

        def process(self, image, recognition_mode='deep'):
            calls.append(image)
            return {'status': 'success', 'source': str(image)}

    monkeypatch.setattr(
        batch_process,
        'OCRRenameService',
        FakeOCRRenameService,
    )

    processor = batch_process.BatchProcessor(
        tmp_path,
        worker_count=2,
    )
    results = processor.run(['only.jpg'])

    assert calls == ['only.jpg']
    assert results == [{
        'status': 'success',
        'source': 'only.jpg',
        'recognition_stage': 'fast',
    }]


def test_batch_progress_reports_each_actual_completion(
    monkeypatch,
    tmp_path,
):
    second_finished = threading.Event()
    first_can_finish = threading.Event()
    progress = []
    shared_project_service = object()

    class FakeOCRRenameService:

        def __init__(
            self,
            output_dir,
            project_service=None,
            output_lock=None,
        ):
            self.project_service = project_service or shared_project_service

        def process(self, image, recognition_mode='deep'):
            if image == 'first.jpg':
                assert second_finished.wait(timeout=2.0)
                assert first_can_finish.wait(timeout=2.0)
            else:
                second_finished.set()
                threading.Timer(
                    0.05,
                    first_can_finish.set,
                ).start()
            return {'status': 'success', 'source': str(image)}

    monkeypatch.setattr(
        batch_process,
        'OCRRenameService',
        FakeOCRRenameService,
    )

    processor = batch_process.BatchProcessor(
        tmp_path,
        worker_count=2,
    )
    results = processor.run(
        ['first.jpg', 'second.jpg'],
        progress_callback=lambda current, total, filename: progress.append(
            (current, total, filename)
        ),
    )

    assert [item['source'] for item in results] == [
        'first.jpg',
        'second.jpg',
    ]
    assert progress == [
        (1, 2, 'second.jpg'),
        (2, 2, 'first.jpg'),
    ]


def test_batch_runs_all_fast_jobs_before_deep_retry(
    monkeypatch,
    tmp_path,
):
    calls = []
    stages = []
    shared_project_service = object()

    class FakeOCRRenameService:

        def __init__(
            self,
            output_dir,
            project_service=None,
            output_lock=None,
        ):
            self.project_service = project_service or shared_project_service

        def process(self, image, recognition_mode='deep'):
            calls.append((str(image), recognition_mode))
            if recognition_mode == 'fast' and image == 'hard.jpg':
                return {
                    'status': 'unmatched',
                    'source': str(image),
                    'match_score': 45.0,
                }
            return {
                'status': 'success',
                'source': str(image),
            }

    monkeypatch.setattr(
        batch_process,
        'OCRRenameService',
        FakeOCRRenameService,
    )

    processor = batch_process.BatchProcessor(
        tmp_path,
        worker_count=1,
    )
    results = processor.run(
        ['hard.jpg', 'easy.jpg'],
        stage_callback=lambda *values: stages.append(values),
    )

    assert calls == [
        ('hard.jpg', 'fast'),
        ('easy.jpg', 'fast'),
        ('hard.jpg', 'deep'),
    ]
    assert [item['status'] for item in results] == [
        'success',
        'success',
    ]
    assert results[0]['recognition_stage'] == 'deep'
    assert results[1]['recognition_stage'] == 'fast'
    assert ('deep', 0, 1, 1) in stages


def test_deep_failure_keeps_better_fast_review_result(
    monkeypatch,
    tmp_path,
):
    class FakeOCRRenameService:

        def __init__(
            self,
            output_dir,
            project_service=None,
            output_lock=None,
        ):
            self.project_service = project_service or object()

        def process(self, image, recognition_mode='deep'):
            if recognition_mode == 'fast':
                return {
                    'status': 'review_required',
                    'source': str(image),
                    'match_score': 66.0,
                    'candidates': [{'project_code': 'P001'}],
                }
            return {
                'status': 'failed',
                'source': str(image),
                'error': 'deep OCR failed',
            }

    monkeypatch.setattr(
        batch_process,
        'OCRRenameService',
        FakeOCRRenameService,
    )

    result = batch_process.BatchProcessor(
        tmp_path,
        worker_count=1,
    ).run(['hard.jpg'])[0]

    assert result['status'] == 'review_required'
    assert result['recognition_stage'] == 'fast'
    assert result['candidates'] == [{'project_code': 'P001'}]
