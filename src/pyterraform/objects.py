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


class NamedObject(TFObject):
    def __init__(self, name, **kwargs):
        self.name = name
        self.values = kwargs

    @classmethod
    def compile(cls):
        return dict(
            (klass.__name__.lower(), dict(
                (instance.name, instance.values)
                for instance in klass._instances
            ))
            for klass in cls.__subclasses__()
            if klass._instances
        )


class TypedObject(TFObject):
    def __init__(self, type, name, **kwargs):
        self.type = type
        self.name = name
        self.values = kwargs

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
                    compiled[klass_name][instance.type][instance.name] = instance.values
                except KeyError:
                    compiled[klass_name][instance.type] = {instance.name: instance.values}

        return compiled


class Provider(NamedObject):
    pass


class Variable(NamedObject):
    pass


class Output(NamedObject):
    pass


class Data(TypedObject):
    pass


class Resource(TypedObject):
    pass
