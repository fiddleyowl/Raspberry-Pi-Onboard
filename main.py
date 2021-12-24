from http_server import *
import sys

if __name__ == "__main__":
    setup_GPIO_pins()
    if len(sys.argv) > 0:
        start_server_ssl()
    start_server()
