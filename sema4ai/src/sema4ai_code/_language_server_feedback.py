from functools import partial

from sema4ai_code.protocols import IRcc


class _Feedback(object):
    def __init__(self, rcc: IRcc):
        self.track = True
        self._rcc = rcc

    def metric(self, name, value="+1"):
        if not self.track:
            return

        from sema4ai_ls_core.timeouts import TimeoutTracker

        timeout_tracker = TimeoutTracker.get_singleton()
        timeout_tracker.call_on_timeout(
            0.1, partial(self._rcc.feedack_metric, name, value)
        )
