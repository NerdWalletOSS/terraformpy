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
    _instances = None

    def __new__(cls, *args, **kwargs):
        # create the instance
        inst = super(ResourceCollection, cls).__new__(cls, *args, **kwargs)

        # register it on the class
        try:
            ResourceCollection._instances.append(inst)
        except AttributeError:
            ResourceCollection._instances = [inst]

        # return it
        return inst

    def __init__(self, **kwargs):
        for name in dir(self):
            attr = getattr(self, name)
            if not isinstance(attr, Input):
                continue

            val = None

            # if we have a variant we want to check it first
            if Variant.CURRENT_VARIANT is not None:
                # if there is then try fetching the val from inside the special variant attr
                variant_name = '{0}_variant'.format(Variant.CURRENT_VARIANT.name)
                variant_args = kwargs.get(variant_name, None)
                if variant_args is not None:
                    val = variant_args.get(name, None)

            if val is None:
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

    def finalize_resources(self):
        """This is called right before we compile everything.  It gives the collection a chance to generate any final
        resources prior to the compilation occuring.
        """
        pass


class Variant(object):
    """When used as a context manager it provides the ability for ResourceCollection's to vary their inputs based on a
    symbolc string name that allows you to define a resource collection for multiple environments where most of the
    inputs are shared, with only a few differences
    """
    CURRENT_VARIANT = None

    def __init__(self, name):
        self.name = name

    def __enter__(self):
        assert Variant.CURRENT_VARIANT is None, "Only one variant may be active at a time"
        Variant.CURRENT_VARIANT = self

    def __exit__(self, exc_type, exc_value, traceback):
        Variant.CURRENT_VARIANT = None
