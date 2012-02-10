Mustache to javascript compiler
===============================

Mustache to javascript compiler written in python. It is based on
twitter hogan.js compiler http://twitter.github.com/hogan.js/

`Hogan.Template` is still required for rendering.


Installation
------------

1. Install virtualenv::

    $ wget https://raw.github.com/pypa/virtualenv/master/virtualenv.py
    $ python2.7 ./virtualenv.py --no-site-packages venv

2. Clone pyhogan from github and then install::

    $ git clone git://github.com/fafhrd91/pyhogan.git
    $ cd pyhogan
    $ ../venv/bin/python setup.py develop

3. Compile your mustache templates::

    $ ../venv/bin/pyhogan template.mustache

    new Hogan.Template(function(c,p,i){...}


Testing
-------

Node.js is required for tests::

    $ cd pyhogen/spec/
    $ ../../venv/python ./mustache_spec.py


Requirements
------------

- Python 2.6 and up

- Hogan.js 1.0.5
