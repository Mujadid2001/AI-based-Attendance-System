"""
Configuration package for the attendance system.

Importing this package wires up two things that must happen before Django
starts.

1. The Celery application, so that ``@shared_task`` in any app binds to it.
2. A pure-Python MySQL driver shim (see below).

MySQL driver
------------
Django's ``django.db.backends.mysql`` expects to import a module named
``MySQLdb``. The usual provider, ``mysqlclient``, is a C extension that needs
a compiler, pkg-config and the MySQL development headers - and a failed build
aborts the entire ``pip install``.

``PyMySQL`` speaks the same DB-API and needs none of that, so it is registered
under the name Django looks for. ``cryptography`` is required alongside it for
the caching_sha2_password auth plugin that MySQL 8 / MariaDB 10.4+ use by
default; without it, login fails with
"cryptography is required for sha256_password or caching_sha2_password".
"""

try:  # pragma: no cover - depends on the configured database backend
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:  # pragma: no cover
    # Not using MySQL (SQLite in development, or psycopg2 for PostgreSQL).
    # Nothing to register.
    pass

from .celery import app as celery_app

__all__ = ('celery_app',)
