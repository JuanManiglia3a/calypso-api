"""
scaffold/__init__.py

Public API – re-exports the generate() function so that:
    from apicalypso.scaffold import generate
continues to work without any changes to cli.py or external code.

To add a new resource type, create resources/<type>/ and expose its
generate_<type>() from here.
"""
from .resources.api._generator import generate  # noqa: F401
from .cicd._generator import generate_cicd      # noqa: F401
