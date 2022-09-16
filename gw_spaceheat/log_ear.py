import logging

import dotenv

import load_house
from actors.cloud_ear import CloudEar
from config import ScadaSettings

logging.basicConfig(level="DEBUG")

settings = ScadaSettings(_env_file=dotenv.find_dotenv())
ear = CloudEar(settings=settings, hardware_layout=load_house.load_all(settings))

ear.start()
