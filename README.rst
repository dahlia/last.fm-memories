Last.fm Memories
================

This small program lists music you had listened before from Last.fm (or Libre.fm).
Note that it requires Python 3.7 or later.  It can be installed using ``pip``:

.. code-block:: console

   pip install last.fm-memories

You need a Last.fm API key first, and can get one from here__.  The first time
you run this program, it will asks an API key pair (or you could configure it
through ``-k``/``--api-key`` and ``-s``/``--api-secret`` options).

The following command lists albums you had listened the year before last:

.. code-block:: console

   last.fm-memories $YOUR_LASTFM_NAME artists --back 24

For more usages:

.. code-block:: console

   last.fm-memories --help

__ https://www.last.fm/api/account/create
