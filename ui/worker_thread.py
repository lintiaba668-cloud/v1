# -*- coding: utf-8 -*-

"""Background worker abstraction for UI integration.

Keeps batch processing away from the Qt main thread.
"""


class WorkerThread:

    def __init__(self, worker):
        self.worker = worker
        self.running = False
        self.result = None

    def run(self, *args, **kwargs):
        self.running = True

        try:
            self.result = self.worker.process_directory(
                *args,
                **kwargs
            )

        finally:
            self.running = False

        return self.result

    def stop(self):
        self.running = False
