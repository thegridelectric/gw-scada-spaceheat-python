import re

snake_add_underscore_to_camel_pattern = re.compile(r'(?<!^)(?=[A-Z])')

def camel_to_snake(name):
    return snake_add_underscore_to_camel_pattern.sub('_', name).lower()