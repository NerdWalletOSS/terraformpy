|pypi| |versions| |format| |license| |coverage|

.. |pypi| image:: https://img.shields.io/pypi/v/terraformpy?color=blue
   :target: https://pypi.org/project/terraformpy

.. |versions| image:: https://img.shields.io/badge/python-2.7%20%7C%203.5%20%7C%203.6%20%7C%203.7%20%7C%203.8-blue
   :target: https://pypi.org/project/terraformpy

.. |format| image:: https://img.shields.io/pypi/format/terraformpy?color=blue
   :target: https://pypi.org/project/terraformpy

.. |license| image:: https://img.shields.io/pypi/l/terraformpy?color=blue
   :target: https://pypi.org/project/terraformpy

.. |coverage| image:: https://codecov.io/gh/NerdWalletOSS/terraformpy/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/NerdWalletOSS/terraformpy


Terrafompy
==========

Terraformpy is a library and command line tool to supercharge your Terraform configs using a full fledged Python environment!

`Terraform`_ is an amazing tool.  Like, really amazing.  When working with code that is managing third-party service definitions, and actually applying changes to those definitions by invoking APIs, a high-degree of confidence in the change process is a must-have, and that's where Terraform excels.  The work flow it empowers allow teams to quickly make changes across a large (and ever growing) footprint in multiple providers/regions/technologies/etc.

But as your definitions grow the `HCL`_ syntax very quickly leaves a lot to be desired, and is it ever verbose... So many definitions of variables and outputs need to be repeated, over and over, as you compose more modules that use each other.

Since `HCL`_ is "fully JSON compatible" and Python is great at generating JSON data, we built Terraformpy to provide a more productive environment to build and maintain complex Terraform configs.  It has been used daily in production at `NerdWallet`_ since 2016 and has proven very valuable in accelerating our adoption of Terraform across our engineering organization.

.. _Terraform: https://www.terraform.io
.. _HCL: https://github.com/hashicorp/hcl
.. _NerdWallet: https://www.nerdwallet.com


Installing Terraformpy
----------------------

The recommended way to install and use Terraformpy is via `Pipenv`_

An example would look like:

.. code-block:: bash

    $ mkdir my-terraform-project
    $ cd my-terraform-project
    $ pipenv install terraformpy

You can then run Terraformpy using ``pipenv run``:

.. code-block:: bash

    $ pipenv run terraformpy ...

Or you can use ``pipenv shell`` to activate the virtualenv so you don't need to use ``pipenv run``.  The rest of this document assumes that you've run ``pipenv shell`` and can just run ``terraformpy`` directly.

.. _Pipenv: https://docs.pipenv.org/en/latest/

Using the CLI tool
------------------

The ``terraformpy`` command line tool operates as a shim for the underlying ``terraform`` tool.  When invoked it will first find all ``*.tf.py`` files in the current directory, loading them using the `imp`_ module, generate a file named ``main.tf.json``, and then invoke underlying tool.

.. code-block:: bash

    # just replace terraform in your regular workflow
    terraformpy plan -out=tf.plan

    # review changes...

    # apply them!
    # since we're going to operate on the generated plan here, we don't event need to use terraformpy anymore
    terraform apply tf.plan


Each of the ``*.tf.py`` files uses a declarative syntax, using objects imported from this library.  You don't need to define a main function, you just create instances of classes (anonymous or otherwise) in the root of the module (you're building regular Python code here).  Since you're in a full blown Python environment there is no limit on what you can do -- import things, connect to databases, etc.

.. _imp: https://docs.python.org/3/library/imp.html


Writing ``.tf.py`` files
------------------------

The ``terraformpy`` name space provides a number of classes that map directly to things you declare in normal ``.tf.`` files.  To write your definitions simply import these classes and begin creating instances of them.  Below is the first example from the `Terraform getting start guide`_.

.. _Terraform getting start guide: https://learn.hashicorp.com/terraform/getting-started/build.html#configuration

.. code-block:: python

    from terraformpy import Provider, Resource

    Provider(
        'aws',
        profile='default',
        region='us-east-1'
    )

    Resource(
        'aws_instance', 'example',
        ami='ami-2757f631'
        instance_type='t2.micro'
    )


Things you can import from ``terraformpy``:

* ``Resource`` - https://www.terraform.io/docs/configuration/resources.html
* ``Provider`` - https://www.terraform.io/docs/configuration/providers.html
* ``Variable`` - https://www.terraform.io/docs/configuration/variables.html
* ``Output`` - https://www.terraform.io/docs/configuration/outputs.html
* ``Module`` - https://www.terraform.io/docs/configuration/modules.html
* ``Data`` - https://www.terraform.io/docs/configuration/data-sources.html
* ``Terraform`` - https://www.terraform.io/docs/configuration/terraform.html

See the ``examples/`` dir for fully functional examples.


Interpolation
-------------

So far, we've only used terraformpy anonymously, but the returned instances of the ``Data`` and ``Resource`` classes offer handy interpolation attributes.  For example, a common task is using the ``Data`` class to fetch remote data:

.. code-block:: python

    ami = Data(
        'aws_ami', 'ecs_ami',
        most_recent=True,
        filter=[
            dict(name='name', values=['\*amazon-ecs-optimized']),
            dict(name='owner-alias', values=['amazon'])
        ]
    )

    Resource(
        'aws_instance', 'example',
        ami=ami.id,
        instance_type='m4.xlarge'
    )

Here we simply refer to the id attribute on the ami object when creating the ``aws_instance``.  During the compile phase it would be converted to the correct syntax: ``"${data.aws_ami.ecs_ami.id}"``.

This works by having a custom ``__getattr__`` function on our ``Data`` and ``Resource`` objects that will turn any attribute access for an attribute name that doesn't exist into the Terraform interpolation syntax.


Backend
-------

Configuring a backend happens in the `Terraform` object. See `Configuring a Terraform Backend`_ for more details.

Bellow we are using an S3 Backend:

.. code-block:: python

    Terraform(
        backend=dict(
            s3=dict(
                region="us-east-1",
                bucket="terraform-tfstate-bucket",
                key="terraform.tfstate",
                workspace_key_prefix="my_prefix",
                dynamodb_table="terraform_locks",
            )
        )
    )

Modules
-------

Since Terraformpy gives you the full power of Python we encourage you to use "Resource Collections" (see the next section) when you're building your own modular functionality and you don't plan on sharing these modules outside of your current organization.

You can however leverage existing HCL modules using the ``Module`` object if you want to use pre-built, existing modules:

.. code-block:: python

    Module(
        "consul",
        source="hashicorp/consul/aws",
        version="0.0.5",

        servers=3
    )


Resource Collections
--------------------

A common pattern when building configs using Python is to want to abstract a number of different resources under the guise of a single object -- which is the same pattern native Terraform modules aim to solve.  In terraformpy we provide a ``ResourceCollection`` base class for building objects that represent multiple resources.

You can use `Schematics`_ to define the fields and perform validation.

As an example, when provisioning an RDS cluster you may want to have a standard set of options that you ship with all your clusters.  You can express that with a resource collection:


.. _Schematics: https://schematics.readthedocs.io/en/latest/

.. code-block:: python

    from schematics import types
    from schematics.types import compound
    from terraformpy import Resource, ResourceCollection


    class RDSCluster(ResourceCollection):

        # Defining attributes of your resource collection is like defining a Schematics Model, in fact the
        # ResourceCollection class is just a specialized subclass of the Schematics Model class.
        #
        # Each attribute becomes a field on the collection, and can be provided as a keyword when constructing
        # an instance of your collection.
        #
        # Validation works the same as in Schematics.  You can attach validators to the fields themselves and
        # also define "validate_field" functions.

        name = types.StringType(required=True)
        azs = compound.ListType(types.StringType, required=True)
        instance_class = types.StringType(required=True, choices=('db.r3.large', ...))

        # The create_resources function is invoked once the instance has been created and the kwargs provided have been
        # processed against the inputs.  All of the instance attributes have been converted to the values provided, so
        # if you access self.name in create_resources you're accessing whatever value was provided to the instance

        def create_resources(self):
            self.param_group = Resource(
                'aws_rds_cluster_parameter_group', '{0}_pg'.format(self.name),
                family='aurora5.6',
                parameter=[
                    {'name': 'character_set_server', 'value': 'utf8'},
                    {'name': 'character_set_client', 'value': 'utf8'}
                ]
            )

            self.cluster = Resource(
                'aws_rds_cluster', self.name,
                cluster_identifier=self.name,
                availability_zones=self.azs,
                database_name=self.name,
                master_username='root',
                master_password='password',
                db_cluster_parameter_group_name=self.param_group.id
            )

            self.instances = Resource(
                'aws_rds_cluster_instance', '{0}_instances'.format(self.name),
                count=2,
                identifier='{0}-${{count.index}}'.format(self.name),
                cluster_identifier=self.cluster.id,
                instance_class=self.instance_class
            )


That definition can then be imported and used in your terraformpy configs.

.. code-block:: python

    from modules.rds import RDSCluster


    cluster1 = RDSCluster(
        name='cluster1',
        azs=['us-west-2a','us-west-2b','us-west-2c'],
        instance_class='db.r3.large'
    )

    # you can then refer to the resources themselves, for interpolation, through the attrs
    # i.e. cluster1.cluster.id


Variants
--------

Resource definitions that exist across many different environments often only vary slightly between each environment. To facilitate the ease of definition for these differences you can use variant grouping.

First create the folders: ``configs/stage/``, ``configs/prod/``, ``configs/shared/``.  Inside each of them place a ``__init__.py`` to make them packages.

Next create the file ``configs/shared/instances.py``:

.. code-block:: python

    from terraformpy import Resource

    Resource(
        'aws_instance', 'example',
        ami=ami.id,
        prod_variant=dict(
            instance_type='m4.xlarge'
        ),
        stage_variant=dict(
            instance_type='t2.medium'
        )
    )

Then create ``configs/stage/main.tf.py``:

.. code-block:: python

    from terraformpy import Variant

    with Variant('stage'):
        import configs.shared.instances

Since the import of the instances file happens inside of the Variant context then the Resource will be created as if it had been defined like:

.. code-block:: python

    from terraformpy import Resource

    Resource(
        'aws_instance', 'example',
        ami=ami.id,
        instance_type='t2.medium'
    )


Multiple providers
------------------

Depending on your usage of Terraform you will likely end up needing to use multiple providers at some point in time. To use `multiple providers in Terraform`_ you define them using aliases and then reference those aliases in your resource definitions.

To make this pattern easier you can use the Terraformpy ``Provider`` object as a context manager, and then any resources created within the context will automatically have that provider aliases referenced:

.. code-block:: python

    from terraformpy import Resource, Provider

    with Provider("aws", region="us-west-2", alias="west2"):
        sg = Resource('aws_security_group', 'sg', ingress=['foo'])

    assert sg.provider == 'aws.west2'

.. _multiple providers in Terraform: https://www.terraform.io/docs/configuration/providers.html#alias-multiple-provider-instances


Using file contents
-------------------

Often times you will want to include the contents of a file that is located alongside your Python code, but when running ``terraform`` along with the ``${file('myfile.json')}`` interpolation function pathing will be relative to where the compiled ``main.tf.json`` file is and not where the Python code lives.

To help with this situation a function named ``relative_file`` inside of the ``terraformpy.helpers`` namespace is provided.

.. code-block:: python

    from terraformpy import Resource
    from terraformpy.helpers import relative_file

    Resource(
        'aws_iam_role', 'role_name',
        name='role-name',
        assume_role_policy=relative_file('role_policy.json')
    )

This would produce a definition that leverages the ``${file(...)}`` interpolation function with a path that reads the ``role_policy.json`` file from the same directory as the Python code that defined the role.


Hooks
=====

Terraformy offers a "hooks" system that allows you to modify objects on the fly at compile
time.  This can be useful to apply transformations so that users of objects do not need
to worry about some of the idiosyncratic schema details of Terraform's JSON syntax,
most notably `"Attributes as Blocks"`_.

The best example of this is the ``aws_security_group`` object type, which requires that its
``ingress`` and ``egress`` blocks have all of their attributes present, even if they are
``null``.  To have users have to type out all of the different attributes and set them to
``None`` is cumbersome, so instead you can use the hook that we ship with this distribution:

.. code-block:: python

    from terraformpy.hooks.aws import install_aws_security_group_attributes_as_blocks_hook

    install_aws_security_group_attributes_as_blocks_hook()


Now, users only need to specify the attributes they care about in rules and the hook will
take care of filling in all of the optional attributes that are mandatory to appear in the
final compiled JSON.

For more information on how the hooks work see the ``test_hooks_aws.py`` file and the
inline comments for the ``add_hook`` function on the different object types.


.. _"Attributes as Blocks": https://www.terraform.io/docs/configuration/attr-as-blocks.html


Notes and Gotchas
=================

Security Group Rules and ``self``
----------------------------------

When creating ``aws_security_group_rule`` ``Resource`` objects you cannot pass ``self=True`` to the object since Python already passes a ``self`` argument into the constructor.  In this case you'll need to specify it directly in the ``_values``:

.. code-block:: python

    sg = Resource(
        'aws_security_group_rule', 'my_rule',
        _values=dict(self=True),
        vpc_id=vpc.id,
        ...
    )

Developer notes
===============

Running tests
-------------

We use tox to run tests.  While developing locally you can run:

.. code-block::

    tox


Formatting with black
---------------------

We use black to format code.  To apply formatting run:

.. code-block::

    tox -e black -- .


Release Steps
-------------

1. Make a branch
2. Make your changes
3. Bump the version in the VERSION file and add an entry to the CHANGELOG.md file
4. Open a PR, tag @NerdWalletOSS/dynamorm in your PR description
5. Once approved and merged to master the new version will be pushed to pypi

.. _`Configuring a Terraform Backend`: https://www.terraform.io/docs/configuration/terraform.html#configuring-a-terraform-backend
