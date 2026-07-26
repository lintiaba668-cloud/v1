# -*- coding: utf-8 -*-
"""Batch OCR and rename processing."""

from concurrent.futures import as_completed, ThreadPoolExecutor
import os
import threading

from core.ocr_rename_service import OCRRenameService


class BatchProcessor:
    """Run independent image OCR jobs with a conservative worker limit."""

    MAX_WORKERS = 2

    def __init__(self, output_dir, worker_count=None):
        self.output_dir = output_dir
        self.output_lock = threading.Lock()
        self.worker_count = self._resolve_worker_count(worker_count)
        self._worker_state = threading.local()
        self.service = OCRRenameService(
            output_dir,
            output_lock=self.output_lock,
        )

    def run(
        self,
        files,
        progress_callback=None,
        stage_callback=None,
    ):
        items = list(files)
        total = len(items)
        results = [None] * total
        difficult = []
        completed = 0
        scanned = 0

        if stage_callback:
            stage_callback('fast', 0, total, 0)

        if len(items) <= 1 or self.worker_count <= 1:
            fast_items = (
                (
                    index,
                    item,
                    self.service.process(
                        item,
                        recognition_mode='fast',
                    ),
                )
                for index, item in enumerate(items)
            )
            for index, item, result in fast_items:
                scanned += 1
                result = self._tag_stage(result, 'fast')
                if result.get('status') == 'success':
                    results[index] = result
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total, str(item))
                else:
                    difficult.append((index, item, result))
                if stage_callback:
                    stage_callback(
                        'fast',
                        scanned,
                        total,
                        len(difficult),
                    )
        else:
            with ThreadPoolExecutor(
                max_workers=self.worker_count
            ) as executor:
                futures = {
                    executor.submit(
                        self._process_one,
                        item,
                        'fast',
                    ): (index, item)
                    for index, item in enumerate(items)
                }

                for future in as_completed(futures):
                    index, item = futures[future]
                    scanned += 1
                    result = self._tag_stage(
                        future.result(),
                        'fast',
                    )
                    if result.get('status') == 'success':
                        results[index] = result
                        completed += 1
                        if progress_callback:
                            progress_callback(
                                completed,
                                total,
                                str(item),
                            )
                    else:
                        difficult.append((index, item, result))
                    if stage_callback:
                        stage_callback(
                            'fast',
                            scanned,
                            total,
                            len(difficult),
                        )

        # The accuracy pass is deliberately serial. It uses larger OCR images
        # and more Tesseract variants, so parallel retries would be unsafe on
        # Win7 32-bit machines and can starve later work of memory.
        difficult.sort(key=lambda value: value[0])
        if difficult and stage_callback:
            stage_callback('deep', 0, len(difficult), len(difficult))

        for current, (index, item, fast_result) in enumerate(
            difficult,
            start=1,
        ):
            deep_result = self._tag_stage(
                self.service.process(
                    item,
                    recognition_mode='deep',
                ),
                'deep',
            )
            results[index] = self._prefer_retry_result(
                fast_result,
                deep_result,
            )
            completed += 1
            if progress_callback:
                progress_callback(completed, total, str(item))
            if stage_callback:
                stage_callback(
                    'deep',
                    current,
                    len(difficult),
                    len(difficult) - current,
                )

        if stage_callback:
            stage_callback('complete', total, total, 0)

        # Progress follows actual completion order, while returned results
        # preserve the user's imported file order.
        return results

    def _process_one(self, image, recognition_mode='deep'):
        service = getattr(self._worker_state, 'service', None)

        if service is None:
            # Each worker owns its OCR engine/executor. Sharing one executor
            # across simultaneous Tesseract subprocesses is not safe.
            service = OCRRenameService(
                self.output_dir,
                project_service=self.service.project_service,
                output_lock=self.output_lock,
            )
            self._worker_state.service = service

        return service.process(
            image,
            recognition_mode=recognition_mode,
        )

    @staticmethod
    def _tag_stage(result, stage):
        value = dict(result or {})
        value['recognition_stage'] = stage
        return value

    @staticmethod
    def _prefer_retry_result(fast_result, deep_result):
        status_rank = {
            'success': 4,
            'review_required': 3,
            'unmatched': 2,
            'failed': 1,
            'missing': 0,
        }

        def rank(value):
            return (
                status_rank.get(value.get('status', ''), 0),
                float(value.get('match_score', 0.0) or 0.0),
                float(value.get('match_margin', 0.0) or 0.0),
                len(value.get('candidates') or []),
                value.get('recognition_stage') == 'deep',
            )

        if rank(deep_result) >= rank(fast_result):
            return deep_result
        return fast_result

    @classmethod
    def _resolve_worker_count(cls, requested):
        if requested is None:
            requested = os.environ.get('POWER_RENAME_OCR_WORKERS')

        if requested is None:
            return cls._recommended_worker_count()

        try:
            workers = int(requested)
        except (TypeError, ValueError):
            return cls._recommended_worker_count()

        cpu_count = os.cpu_count() or 1
        return max(1, min(workers, cls.MAX_WORKERS, cpu_count))

    @classmethod
    def _recommended_worker_count(cls, cpu_count=None):
        """Choose a safe OCR process count for the current CPU."""
        if cpu_count is None:
            cpu_count = os.cpu_count() or 1

        cpu_count = max(1, int(cpu_count))

        # Tesseract is CPU and memory intensive. Real-image benchmarking on an
        # 8-thread/64-bit machine showed no gain from a third image worker, so
        # keep the quality-preserving ceiling at two. Low-core machines stay
        # serial to avoid CPU contention.
        if cpu_count >= 4:
            return 2
        return 1
