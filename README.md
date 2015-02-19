api.palaverapp.com
==================

[![Build Status](https://travis-ci.org/cocodelabs/api.palaverapp.com.png?branch=master)](https://travis-ci.org/cocodelabs/api.palaverapp.com)
[![Apiary Documentation](https://img.shields.io/badge/Apiary-Documented-blue.svg)](http://docs.palaver.apiary.io/)

Available under the [BSD license](LICENSE).

## Setup

1. Create a virtual environment:

        $ virtualenv venv

2. Activate the virtual environment:

        $ source venv/bin/activate

3. Install the dependencies:

        $ pip install -r requirements.txt


### Running tests

```shell
$ invoke tests
```

### Running the server

For development:

```shell
$ python -m palaverapi
```

In production:

```shell
$ gunicorn palaverapi:wsgi
```

Via foreman:

```shell
$ foreman start
```

