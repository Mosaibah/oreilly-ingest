from abc import ABC


class Plugin(ABC):
    kernel = None

    @property
    def http(self):
        return self.kernel.http
