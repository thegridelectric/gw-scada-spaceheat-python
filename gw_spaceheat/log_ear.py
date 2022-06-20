import logging

from actors.cloud_ear import CloudEar

logging.basicConfig(level="DEBUG")

ear = CloudEar(logging_on=True)

ear.start()
