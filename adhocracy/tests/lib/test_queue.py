from unittest import TestCase

from mock import MagicMock, patch


@patch('adhocracy.lib.cli.AdhocracyTimer.setup_timer', return_value=None)
@patch('adhocracy.lib.cli.AdhocracyTimer.get_lock', return_value=True)
class TimerTestCase(TestCase):

    def _make_timer(self):
        from adhocracy.lib.cli import AdhocracyTimer
        timer = AdhocracyTimer(None, 'dummy')
        task_mock = MagicMock()
        periodicals = {'testperiodical': {'delay': 1.0,
                                          'task': task_mock}}
        timer.periodicals = periodicals
        return task_mock, timer

    def test_runs_initial_periodicals_if_get_lock(self, get_lock, setup_timer):
        task_mock, timer = self._make_timer()
        run_periodicals_mock = MagicMock()
        timer.run_periodicals = run_periodicals_mock

        get_lock.return_value = True
        timer.guard()

        self.assertTrue(get_lock.called)
        self.assertTrue(run_periodicals_mock.called)
        self.assertTrue(setup_timer.called)

    def test_not_runs_periodicals_without_lock(self, get_lock, setup_timer):
        task_mock, timer = self._make_timer()
        run_periodicals_mock = MagicMock()
        timer.run_periodicals = run_periodicals_mock

        get_lock.return_value = False
        timer.guard()

        self.assertTrue(get_lock.called)
        self.assertFalse(run_periodicals_mock.called)
        # but it setups up the timer anyway
        self.assertTrue(setup_timer.called)
        