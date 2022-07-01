import json


class StreamlinedSerializerMixin:
    @property
    def streamlined_serialize(self):
        output = {}
        for key, value in self.__dict__.items():
            if value is not None:
                output[key] = value

        return json.dumps(output)
