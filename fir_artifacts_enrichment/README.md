## Install
Follow the generic plugin installation instructions in [the FIR wiki](https://github.com/certsocietegenerale/FIR/wiki/Plugins).

| FIR plugin requirements   |                                                                               |
| ------------------------- | ----------------------------------------------------------------------------- |
| fir_abuse                 | [[link]](https://github.com/y9mo/FIR/tree/master/fir_abuse)                   |
| fir_celery                | [[link]](https://github.com/certsocietegenerale/FIR/tree/master/fir_celery)   |


__Python Package Index (PyPI) requirements __
* abuse_finder [[link]](https://pypi.python.org/pypi/abuse-finder)

## Usage

You have nothing to do, that's the whole point. Just sit back and enjoy the ride ;)

The `fir_artifacts_enrichment` plugin defines a __celery__ task that can be performed by a worker in the background.

It relies on the `abuse_finder` package to perform an action depending on the `artifact.type`

```python
ENRICHMENT_FUNCTIONS = {
    'hostname': domain_abuse,
    'ip': ip_abuse,
    'email': email_abuse,
    'url': url_abuse
}
```

The result of this task is then kept into FIR database and can be used by `fir_abuse` plugin
