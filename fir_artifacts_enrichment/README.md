## Install
Follow the generic plugin installation instructions in [the FIR wiki](https://github.com/certsocietegenerale/FIR/wiki/Plugins).

This plugin requires `fir_celery` to be installed and working first. ([[link]](https://github.com/certsocietegenerale/FIR/tree/master/fir_celery))


## Usage
The `fir_artifacts_enrichment` plugin defines a __celery__ task that can be performed by a worker in the background.

It relies on the `abuse_finder` package to perform an action depending on the `artifact.type`.
The result of this task is then kept into FIR database and can be used by other modules.

An API endpoint allows to check the status of a task.
