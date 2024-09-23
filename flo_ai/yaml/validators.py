import re

name_regex = r'^[a-zA-Z0-9-]+$'

class DuplicateStringError(Exception):
    pass

class InvalidStringError(Exception):
    pass

def validate_name(string):
    if not re.match(name_regex, string):
        raise InvalidStringError("Name must contain only alphanumeric characters and hyphens.")