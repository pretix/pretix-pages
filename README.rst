pretix pages
============

This is a plugin for `pretix`_ that allows you to add static pages to your event site, for example for a FAQ, terms of
service, etc.

Contributing
------------

If you like to contribute to this project, you are very welcome to do so. If you have any
questions in the process, please do not hesitate to ask us.

Please note that we have a `Code of Conduct`_ in place that applies to all project contributions, including issues,
pull requests, etc.

Development setup
^^^^^^^^^^^^^^^^^

1. Make sure that you have a working `pretix development setup`_.

2. Clone this repository, eg to ``local/pretix-pages``.

3. Activate the virtual environment you use for pretix development.

4. Execute ``python setup.py develop`` within this directory to register this application with pretix's plugin registry.

5. Execute ``make`` within this directory to compile translations.

6. Restart your local pretix server. You can now use the plugin from this repository for your events by enabling it in
   the 'plugins' tab in the settings.


License
-------

Copyright 2017 Raphael Michel

Released under the terms of the Apache License 2.0


.. _pretix: https://github.com/pretix/pretix
.. _pretix development setup: https://docs.pretix.eu/en/latest/development/setup.html
.. _Code of Conduct: https://docs.pretix.eu/en/latest/development/contribution/codeofconduct.html
