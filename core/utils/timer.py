import time


class Timer:
    """Simple timer for measuring execution time."""

    def __init__(self, name: str):
        self.name = name
        self.start_time = None

    def start(self):
        self.start_time = time.perf_counter()

    def stop(self) -> float:
        if self.start_time is None:
            raise RuntimeError("Timer was not started.")

        elapsed = time.perf_counter() - self.start_time

        print(
            f"⏱️ {self.name}: {elapsed:.2f} seconds"
        )

        return elapsed