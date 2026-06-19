"""Stub progressbar — the original used a Tkinter-based progress widget.
In the new Qt app progress is shown via ProgressDialog or status bar."""


class progressBar:
    def __init__(self, *args, **kwargs):
        pass

    def print_progress_bar(self, *args, **kwargs):
        pass

    def update(self, *args, **kwargs):
        pass

    def finish(self, *args, **kwargs):
        pass


# Alias so both capitalisation styles work
ProgressBar = progressBar
