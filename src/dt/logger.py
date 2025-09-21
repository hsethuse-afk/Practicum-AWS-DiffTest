from .contracts import LoggerMode

_current = None


def set_logger(logger):
    global _current
    _current = logger


def get_logger():
    return _current or Logger(LoggerMode.Normal)


class Logger:
    def __init__(
        self, mode=LoggerMode.Normal, record=False, file_path=None
    ):
        self.mode = mode
        self.record = record
        self.file_path = file_path
        self._file = (
            open(file_path, "a") if record and file_path else None
        )

    def log(self, level: LoggerMode, msg: str):
        if self.mode >= level:
            print(msg)
            if self._file:
                self._file.write(f"[{level.name}] {msg}\n")
                self._file.flush()

    def normal(self, msg):
        self.log(LoggerMode.Normal, msg)

    def verbose(self, msg):
        self.log(LoggerMode.Verbose, msg)

    def debug(self, msg):
        self.log(LoggerMode.Debug, msg)

    def get_mode(self):
        return self.mode

    def close(self):
        if self._file:
            self._file.close()
