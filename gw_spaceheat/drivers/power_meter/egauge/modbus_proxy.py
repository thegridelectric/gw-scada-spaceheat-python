import argparse
import logging
import socket

import dotenv
from pydantic import BaseSettings
from pyModbusTCP.client import ModbusClient
from pyModbusTCP.server import DataBank
from pyModbusTCP.server import ModbusServer
from rich import print
from rich.console import Console
import rich.traceback
console = Console()
rich.traceback.install(console=console)

class ProxyDataBank(DataBank):
    real_client: ModbusClient

    def __init__(self, real_client: ModbusClient, **kwargs):
        super().__init__(**kwargs)
        self.real_client = real_client
        self.real_client.open()
        if not self.real_client.is_open:
            raise ValueError(f"ERROR. Could not connect to Modubs server at {self.real_client.host}")


    def get_input_registers(self, address, number=1, srv_info=None):
        """Read data on server input registers space

        :param address: start address
        :type address: int
        :param number: number of words (optional)
        :type number: int
        :param srv_info: some server info (must be set by server only)
        :type srv_info: ModbusServerInfo
        :returns: list of int or None if error
        :rtype: list or None
        """
        # secure extract of data from list used by server thread
        print(f"get_input_registers: address:{address}  registers:{number}  from server: {srv_info is not None}")
        if srv_info is not None:
            if not self.real_client.is_open:
                self.real_client.open()
                if not self.real_client.is_open:
                    raise ValueError(f"ERROR. Could not connect to Modubs server at {self.real_client.host}")
            word_list = self.real_client.read_input_registers(address, number)
            if word_list is None:
                return None
            self.set_input_registers(address, word_list=word_list)
        return super().get_input_registers(address, number)

class ModbusClientSettings(BaseSettings):
    host: str = ""
    port: int = 502
    unit_id: int = 1
    timeout: float = 30.0
    debug: bool = False
    auto_open: bool = True
    auto_close: bool = False

def be_the_proxy():
    logging.basicConfig()
    parser = argparse.ArgumentParser()
    parser.add_argument("-H", "--host", type=str, default="localhost", help="Host (default: localhost)")
    parser.add_argument("-p", "--port", type=int, default=502, help="TCP port (default: 502)")
    parser.add_argument("-d", "--debug", action="store_true", help="set debug mode")
    parser.add_argument("--real-host", type=str, help="The host for whom we are proxying")
    parser.add_argument("--real-port", type=int, default=502, help="The port on the real host")
    parser.add_argument("-e", "--env-file", type=str, default=".env", help=".env file to load.")
    args = parser.parse_args()
    cmd_line_args = dict()
    if hasattr(args, "real_host"):
        cmd_line_args["host"] = args.real_host
    if hasattr(args, "real_port"):
        cmd_line_args["port"] = args.real_port
    if args.debug:
        logging.getLogger("pyModbusTCP.server").setLevel(logging.DEBUG)
    settings = ModbusClientSettings(
        _env_file=dotenv.find_dotenv(args.env_file),
        **cmd_line_args
    )
    un_resolved_real_host = settings.host
    settings.host = socket.gethostbyname(settings.host)
    print(f"Serving on host {args.host}")
    print(f"Real modbus host, for which we proxy: {un_resolved_real_host} -> {settings.host}")
    server = ModbusServer(
        host=args.host,
        port=args.port,
        data_bank=ProxyDataBank(ModbusClient(**settings.dict()))
    )
    server.start()

if __name__ == "__main__":
    be_the_proxy()