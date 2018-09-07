## Install
Follow the generic plugin installation instructions in [the FIR wiki](https://github.com/certsocietegenerale/FIR/wiki/Plugins).

__Python Package Index (PyPI) requirements__
* celery
* redis

__Database requirement__
* Redis

The `fir_celery` plugin uses __redis__ as a broker and result backend. As a consequence, you should make sure to provide your FIR instance with the following ( `REDIS_HOST`, `REDIS_PORT` and `REDIS_DB` in the configuration file).


## Usage
Start a worker instance by using the __celery__ program. This is enough for testing/dev purpose but in production you will want to run your worker as a [daemon](http://docs.celeryproject.org/en/latest/userguide/daemonizing.html#daemonizing)
```bash
$ celery -A fir_celery.celeryconf worker -l info
```

### TODO
Improve this integration of celery as we add more tasks
