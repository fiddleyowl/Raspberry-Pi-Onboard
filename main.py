from http_server import *
import sys

if __name__ == "__main__":
    setup_GPIO_pins()
    if len(sys.argv) > 1:
        start_server_ssl()
    else:
        start_server()
