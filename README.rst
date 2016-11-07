Terraform - Python Abstraction
==============================

This is a library and command line tool for building Terraform configs using Python.

How it works
------------

.. code-block:: bash

    terraformpy > main.tf.json

It works by looking for ``*.tf.py`` files in the current directory and loading them using the `imp`_ module.  Each of
these ``.tf.py`` files should import the objects from this library and then use them to build the Terraform config (see
the examples).  As each object is declared it is registered and the command line tool then invokes a "compile" step that
turns the definitions into `Terraform's JSON syntax`_.

From here you can operate on the ``.tf.json`` files using the standard Terraform workflow.


.. _imp: https://docs.python.org/3/library/imp.html
.. _Terraform's JSON syntax: https://www.terraform.io/docs/configuration/syntax.html#json-syntax


Goals
-----

* Maintain as much of the declarative nature of Terraform configs as possible, given that we are explicitly adding
  functional programming to the mix.
* 


Usage
-----

Below is the first example from the `Terraform getting start guide`_.

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


See the ``examples/`` dir for fully functional examples.


Modules
^^^^^^^

Modules have been explicitly excluded from this implementation because they aim to solve the same problem -- building
reusable blocks in your Terraform configs.

With all the features of Python at your disposal building reusable units is straightforward without using the native
modules from Terraform.
