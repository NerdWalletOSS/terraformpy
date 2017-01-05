from .resource_collections import ResourceCollection, Input  # noqa
from .objects import TFObject, Provider, Variable, Data, Resource, Output  # noqa 

# add a couple shortcuts
compile = TFObject.compile
reset = TFObject.reset
