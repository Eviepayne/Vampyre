import argparse

class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)

    def exit(self, status=0, message=None):
        if message:
            self._print_message(message, _sys.stderr)

    def _print_message(self, message, file=None):
        pass
