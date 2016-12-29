Terrafompy
==========

Terraform is an amazing tool.  Like, really amazing.  When working with code that is managing third-party service
definitions, and actually applying changes to those definitions by invoking APIs, a high-degree of confidence in the
change process is a must-have, and that's where Terraform excels.  The work flow it empowers allow teams to quickly make
changes across a large (and ever growing) footprint in multiple providers/regions/technologies/etc.

But as your definitions grow the HCL syntax very quickly leaves a lot to be desired, and oh-my-gosh is it verbose... So
many definitions of variables and outputs need to be repeated, over and over, as you compose more modules that use each
other.  Also, since HCL is a language built at Hashicorp specifically for Terraform it has an immaturity about it that
is just the fact of the matter about a young language.

Nestled in the Terraform docs there is a `section on a JSON syntax`_.  Well... building JSON from code is something
we're pretty good at in Python!

.. _section on a JSON syntax: https://www.terraform.io/docs/configuration/syntax.html#json-syntax


Terraformpy is a library and command line tool for building Terraform configs using Python.


Using the CLI tool
------------------

The ``terraformpy`` command line tool operates as a shim for the underlying ``terraform`` tool.  When invoked it will
first find all ``*.tf.py`` files in the current directory, loading them using the `imp`_ module, generate a file named
``main.tf.json``, and then invoke underlying tool.

.. code-block:: bash

    # just replace terraform in your regular workflow
    terraformpy plan -out=tf.plan

    # review changes...

    # apply them!
    # since we're going to operate on the generated plan here, we don't event need to use terraformpy anymore
    terraform apply tf.plan

    # unless you're a cowboy, then you could do
    terraformpy apply


Each of the ``*.tf.py`` files uses a declarative syntax, using objects imported from this library.  You don't need to
define a main function, you just create instances of classes (anonymous or otherwise) in the root of the module (you're
building regular Python code here).  Since you're in a full blown Python environment there is no limit on what you can
do -- import things, connect to databases, etc.

.. _imp: https://docs.python.org/3/library/imp.html


Writing ``.tf.py`` files
------------------------

The ``terraformpy`` name space provides a number of classes that map directly to things you declare in normal ``.tf.``
files.  To write your definitions simply import these classes and begin creating instances of them.  Below is the first
example from the `Terraform getting start guide`_.

.. _Terraform getting start guide: https://www.terraform.io/intro/getting-started/build.html#configuration

.. code-block:: python

    from terraformpy import Provider, Resource

    Provider(
        'aws',
        access_key='ACCESS_KEY_HERE',
        secret_key='SECRET_KEY_HERE',
        region='us-east-1'
    )

    Resource(
        'aws_instance', 'example',
        ami='ami-0d729a60'
        instance_type='t2.micro'
    )


Things you can import from ``terraformpy``:

* ``Provider``
* ``Variable``
* ``Data``
* ``Resource``
* ``Output``

See the ``examples/`` dir for fully functional examples.


Interpolation
-------------

So far, we've only used terraformpy anonymously, but the returned instances of the ``Data`` and ``Resource`` classes
offer handy interpolation shortcuts.  For example, a common task is using the ``Data`` class to fetch remote data:

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

Here we simply refer to the id attribute on the ami object when creating the ``aws_instance``.  During the compile phase
it would be converted to the correct syntax: ``"${data.aws_ami.ecs_ami.id}"``.


Modules
-------

Modules have been explicitly excluded from this implementation because they aim to solve the same problem -- building
reusable blocks in your Terraform configs.

With all the features of Python at your disposal building reusable units is straightforward without using the native
modules from Terraform.


Real-world use
==============

Create a new python project specifically to house your definitions and give you namespace you can use to define and
import your reusable pieces.  Depend on terraformpy from your project.

When proposing a change to the project use ``terraformpy plan -out=tf.plan`` (or similar) to generate a plan.  Apply the
change in the generated plan and then commit the resulting state back to your project.
