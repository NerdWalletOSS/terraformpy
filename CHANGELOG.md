# 1.3.3

* Add new line to the EOF for `main.tf.json`

# 1.3.2

* Fix build

# 1.3.1

* When dumping JSON we no longer pass `sort_keys=True`, but rather rely on the stable insertion order of Python 3+ dictionaries

# 1.3.0

* Add Hooks to the different object types.  See the README and inline code for docs.

# 1.2.4

* No functional changes
  * Adopt black formatting
  * Move to tox & travis for CI

# 1.2.3

* Fix bug: Multiple providers of different types were colliding with each other
  https://github.com/NerdWalletOSS/terraformpy/pull/62

# 1.2.2

* Fix bug: An explicit `provider` kwarg should take precedence over the `CURRENT_PROVIDER`
  from a `Provider` being used as a context manager.

# 1.2.1

* Add support for HCL modules via the new `Module` object

# 1.2.0

* Support Python 3.5+

# 1.1.3

* Fix distribution, we need to include the `VERSION` file

# 1.1.2

Fix `get_mock_object()` for `ResourceCollection`

# 1.1.1

Publish via CircleCI

# 1.1.0

First open source release, no changes from 1.0.8

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
