"""Terraform "objects"

This module provides a set of classes that can be used to build Terraform configurations in a (mostly) declarative way,
while also leveraging Python to add some functional aspects to automate some of the more repetitive aspects of HCL.
"""
import collections
import six


def recursive_update(dest, source):
    for key, val in six.iteritems(source):
        if isinstance(val, collections.Mapping):
            recurse = recursive_update(dest.get(key, {}), val)
            dest[key] = recurse
        else:
            dest[key] = val
    return dest


class TFObject(object):
    _instances = None
    tf_object_name = "TFObject"

    def __new__(cls, *args, **kwargs):
        # create the instance
        inst = super(TFObject, cls).__new__(cls, *args, **kwargs)

        # register it on the class
        try:
            cls._instances.append(inst)
        except AttributeError:
            cls._instances = [inst]

        # return it
        return inst

    @classmethod
    def reset(cls):
        def recursive_reset(cls):
            cls._instances = []
            for klass in cls.__subclasses__():
                recursive_reset(klass)
        recursive_reset(cls)

    @classmethod
    def compile(cls):
        def recursive_compile(cls):
            results = []
            try:
                for instance in cls._instances:
                    output = instance.build()
                    results.append(output)
            except TypeError:
                pass

            for klass in cls.__subclasses__():
                results += recursive_compile(klass)
            return results
        configs = recursive_compile(cls)

        result = {}
        for config in configs:
            result = recursive_update(result, config)
        return result


class NamedObject(TFObject):
    """Named objects are the Terraform definitions that only have a single name component (i.e. variable or output)"""
    def __init__(self, _name, **kwargs):
        self._name = _name
        self._values = kwargs

    def __getattr__(self, name):
        """This is here as a safety so that you cannot generate hard to debug .tf.json files"""
        raise RuntimeError("%ss does not provide attribute interpolation through attribute access!" %
                           self.__class__.__name__)

    def build(self):
        result = {
            self.tf_object_name: {
                self._name: self._values
            }
        }
        return result


class TypedObject(TFObject):
    """Represents a Terraform object that has both a type and name (i.e. resource or data).

    When you access an attribute of an instance of this class it will return the correct interpolation syntax for that
    object.

    .. code-block:: python

        instance = Resource('aws_instance', 'my_instance', ...)
        assert instance.id == '${aws_instance.my_instance.id}'

    This allows you to build up configurations using the instances of the objects as a shortcut to writing out all of
    the interpolation syntax.
    """
    def __init__(self, _type, _name, **kwargs):
        self._type = _type
        self._name = _name
        self._values = kwargs

    @property
    def terraform_name(self):
        return '.'.join([self._type, self._name])

    def __getattr__(self, name):
        return '${{{0}.{1}}}'.format(self.terraform_name, name)

    def build(self):
        result = {
            self.tf_object_name: {
                self._type: {
                    self._name: self._values
                }
            }
        }
        return result


class Provider(NamedObject):
    """Represents a Terraform provider configuration"""
    tf_object_name = "provider"


class Variable(NamedObject):
    """Represents a Terraform variable

    You can reference the interpolation syntax for a Variable instance by simply using it as a string.

    .. code-block:: python

        var = Variable('my_var', default='foo')
        assert var == '${var.my_var}'
    """
    tf_object_name = "variable"

    def __repr__(self):
        return '${{var.{0}}}'.format(self._name)


class Output(NamedObject):
    """Represents a Terraform output"""
    tf_object_name = "output"


class Data(TypedObject):
    """Represents a Terraform data source"""
    tf_object_name = "data"

    @property
    def terraform_name(self):
        return '.'.join(['data', super(Data, self).terraform_name])


class Resource(TypedObject):
    """Represents a Terraform resource"""
    tf_object_name = "resource"
