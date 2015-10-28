import unittest

from freezer.scheduler import scheduler_job

class TestSchedulerJob(unittest.TestCase):
    def setUp(self):
        self.job = scheduler_job.Job(None, None, {"job_schedule": {}})

    def test(self):
        scheduler_job.RunningState.stop(self.job, {})
