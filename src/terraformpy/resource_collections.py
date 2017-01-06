
class MissingInput(Exception):
    """An input without a default was not supplied"""


class InputDefault(object):
    """This is used so that you can pass None as a default"""


class Input(object):
    def __init__(self, default=InputDefault):
        self.default = default


class ResourceCollection(object):
    def __init__(self, **kwargs):
        for name in dir(self):
            attr = getattr(self, name)
            if not isinstance(attr, Input):
                continue

            val = kwargs.get(name, attr.default)
            if val == InputDefault:
                raise MissingInput("You must supply '%s'" % name)

            setattr(self, name, val)

        self.create_resources()

    def create_resources(self):
        raise NotImplementedError
