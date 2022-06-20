import logging

from actors.cloud_ear import CloudEar

logging.basicConfig(level="DEBUG")

ear = CloudEar(write_to_csv=True, logging_on=True)

ear.start()
