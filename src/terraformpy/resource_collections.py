import inspect
import os


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

    def relative_file(self, filename):
        """Given a filename that is relative to the caller of this function this will return a string to be used in
        resource definitions where you need to load a file.

        Given that Terraform's path.module will always point to the main.tf.json path and we need to retrieve files from
        other directories (i.e. from modules) this provides a convenient way to write a file reference without needing
        to do all of the relative pathing and ../../../..

        .. code-block:: python

            class MyThing(ResourceCollection):
                def create_resources(self):
                    self.thing = Resource(
                        'some_resource', 'my_thing',
                        template=self.relative_file('files/foo.json')
                    )

        And the resulting JSON in main.tf.json will look like:

        .. code-block:: json

            "template": "${file(\"${path.module}/../../../modules/mything/files/foo.json\")}",

        """
        caller = inspect.stack()[1]
        return '${{file("${{path.module}}/{0}")}}'.format(
            os.path.relpath(os.path.join(os.path.dirname(caller[1]), filename))
        )

    def create_resources(self):
        raise NotImplementedError
