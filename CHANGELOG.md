# 1.0.8

Update TypedObjecAttr to build dot-separated strings for ${resource-type.resource.attribute.key-name} value access.

# 1.0.7

Update TypedObjecAttr to build itself recursively.

# 1.0.6

Update TypedObjecAttr to format for integer-based arrays.

# 1.0.5

Added OrderedDictionary schema type

# 1.0.4

Ensure DuplicateKey hash is monotonically increasing for stablesorting purposes

# 1.0.3

Allow ResourceCollection to be used in ModelType fields

# 1.0.2

Ensure the TypedObjecAttr class, added in 1.0.1, works as StringType inputs in ResourceCollection

# 1.0.1

* Add support for map indices access: https://www.terraform.io/docs/configuration/expressions.html#indices-and-attributes

# 1.0.0

* **BREAKING** - The `Input()` primitive originally shipped with terraformpy is now fully deprecated.
  All inputs must be defined as schematics types.

* `ResourceCollection` is now a specialized subclass of a schematics `Model`

# 0.0.37

* Support Schematics style field level validation (#33)

* Add a changelog
