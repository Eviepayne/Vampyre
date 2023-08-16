import argparse

class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)

# parser = ArgumentParser(description='My custom error handler')
# parser.add_argument('--foo', required=True)

# try:
#     args = parser.parse_args()
# except ValueError as e:
#     print(f"Caught an error: {e}")
#     # Handle the error as you wish here
