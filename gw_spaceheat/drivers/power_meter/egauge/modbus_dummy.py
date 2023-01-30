import argparse
import logging
import random
import socket

from pyModbusTCP.server import DataBank
from pyModbusTCP.server import ModbusServer
from rich import print
from rich.console import Console
import rich.traceback

console = Console()
rich.traceback.install(console=console, width=console.width)

class DummyDataBank(DataBank):

    def get_input_registers(self, address, number=1, srv_info=None):
        """Read random data
        """
        if srv_info is not None:
            if number <= 4:
                word_list = [
                    random.randint(0, 2**16)
                    for _ in range(number)
                ]
            else:
                word_list = [
                    ((0x00FF & random.randint(33, 126)) | (0x00F0 & random.randint(33, 126) >> 8))
                    for _ in range(number)
                ]
                word_list[-1] = 0
            self.set_input_registers(address, word_list=word_list)
        return super().get_input_registers(address, number)

def serve_dummy():
    logging.basicConfig()
    parser = argparse.ArgumentParser()
    parser.add_argument("-H", "--host", type=str, default="localhost", help="Host (default: localhost)")
    parser.add_argument("-p", "--port", type=int, default=502, help="TCP port (default: 502)")
    parser.add_argument("-d", "--debug", action="store_true", help="set debug mode")
    parser.add_argument("-e", "--env-file", type=str, default=".env", help=".env file to load.")
    args = parser.parse_args()
    if args.debug:
        logging.getLogger("pyModbusTCP.server").setLevel(logging.DEBUG)
    args.host = socket.gethostbyname(args.host)
    print(f"Serving on host {args.host}")
    server = ModbusServer(
        host=args.host,
        port=args.port,
        data_bank=DummyDataBank()
    )
    server.start()

if __name__ == "__main__":
    serve_dummy()