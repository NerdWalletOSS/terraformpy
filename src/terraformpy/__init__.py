from .objects import Data, DuplicateKey, Output, Provider, Resource, Terraform, TFObject, Variable  # noqa
from .resource_collections import ResourceCollection, Variant  # noqa

# add a couple shortcuts
compile = TFObject.compile
reset = TFObject.reset
