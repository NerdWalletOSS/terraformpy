from .resource_collections import ResourceCollection, Variant  # noqa
from .objects import TFObject, Provider, Variable, Data, Resource, Output, DuplicateKey, Terraform  # noqa

# add a couple shortcuts
compile = TFObject.compile
reset = TFObject.reset
