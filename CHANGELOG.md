# 1.0.1

* Add support for map indices access: https://www.terraform.io/docs/configuration/expressions.html#indices-and-attributes

# 1.0.0

* **BREAKING** - The `Input()` primitive originally shipped with terraformpy is now fully deprecated.
  All inputs must be defined as schematics types.

* `ResourceCollection` is now a specialized subclass of a schematics `Model`

# 0.0.37

* Support Schematics style field level validation (#33)

* Add a changelog
