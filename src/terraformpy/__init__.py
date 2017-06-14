from .resource_collections import ResourceCollection, Input, Variant  # noqa
from .objects import TFObject, Provider, Variable, Data, Resource, Output, DuplicateKey  # noqa 

# add a couple shortcuts
compile = TFObject.compile
reset = TFObject.reset
