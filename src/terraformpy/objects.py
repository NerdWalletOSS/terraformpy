class TFObject(object):
    _instances = None

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
        compiled = {}
        for klass in cls.__subclasses__():
            compiled.update(klass.compile())
        return compiled

    @property
    def terraform_name(self):
        raise NotImplementedError

    def __getattr__(self, name):
        return '${{{0}.{1}}}'.format(self.terraform_name, name)


class NamedObject(TFObject):
    def __init__(self, _name, **kwargs):
        self._name = _name
        self._values = kwargs

    @property
    def terraform_name(self):
        return self.__class__.__name__.lower()

    @classmethod
    def compile(cls):
        return dict(
            (klass.__name__.lower(), dict(
                (instance._name, instance._values)
                for instance in klass._instances
            ))
            for klass in cls.__subclasses__()
            if klass._instances
        )


class TypedObject(TFObject):
    def __init__(self, _type, _name, **kwargs):
        self._type = _type
        self._name = _name
        self._values = kwargs

    @property
    def terraform_name(self):
        return '.'.join([self._type, self._name])

    @classmethod
    def compile(cls):
        compiled = {}
        for klass in cls.__subclasses__():
            if not klass._instances:
                continue

            klass_name = klass.__name__.lower()
            compiled[klass_name] = {}

            for instance in klass._instances:
                try:
                    compiled[klass_name][instance._type][instance._name] = instance._values
                except KeyError:
                    compiled[klass_name][instance._type] = {instance._name: instance._values}

        return compiled


class Provider(NamedObject):
    def __getattr__(self, name):
        raise RuntimeError("Providers do not provide any attribute outputs")


class Variable(NamedObject):
    def __repr__(self):
        return '${{var.{0}}}'.format(self._name)

    def __getattr__(self, name):
        raise RuntimeError("Variables do not provide any attribute outputs")


class Output(NamedObject):
    pass


class Data(TypedObject):
    pass


class Resource(TypedObject):
    pass
