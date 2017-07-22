import warnings

import schematics.types

from terraformpy.helpers import relative_file as _relative_file


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
            if not isinstance(attr, (Input, schematics.types.BaseType)):
                continue

            val = None
            default = attr.default

            # if we have a variant we want to check it first
            if Variant.CURRENT_VARIANT is not None:
                # if there is then try fetching the val from inside the special variant attr
                variant_name = '{0}_variant'.format(Variant.CURRENT_VARIANT.name)
                variant_args = kwargs.get(variant_name, None)
                if variant_args is not None:
                    val = variant_args.get(name, None)

                # capture the default value from the variant if it exists
                # the variant default always trumps the field default
                # if the variant doesn't have a default we fall back to the original default
                default = Variant.CURRENT_VARIANT.defaults.get(name, default)

            if val is not None and name in kwargs:
                warn_msg = "The input {name} is specified in the variant {variant} AND the base ResourceCollection for collection type {collection}.".format(
                    name=name, variant=Variant.CURRENT_VARIANT.name, collection=type(self))
                warnings.warn(warn_msg)

            if val is None:
                val = kwargs.get(name, default)

            if isinstance(attr, Input):
                if val == InputDefault:
                    raise MissingInput("{0} is a required input".format(name))

            elif isinstance(attr, schematics.types.BaseType):
                if val is None and attr.required:
                    raise schematics.exceptions.ValidationError("{0} is a required input".format(name))

                attr.validate(val)
                val = attr.to_native(val)

            setattr(self, name, val)

        self.create_resources()

    def relative_file(self, filename):
        return _relative_file(filename, _caller_depth=2)

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
    inputs are shared, with only a few differences.

    Any kwargs passed to the constructor become defaults for non-variant inputs.  This allows you to supply inputs that
    are shared between many different ResourceCollections at the variant level so you don't need to pass them over and
    over again.
    """
    CURRENT_VARIANT = None

    def __init__(self, name, **kwargs):
        self.name = name
        self.defaults = kwargs
        self.previous_variant = None

    def __enter__(self):
        self.previous_variant = Variant.CURRENT_VARIANT
        Variant.CURRENT_VARIANT = self

    def __exit__(self, exc_type, exc_value, traceback):
        Variant.CURRENT_VARIANT = self.previous_variant
