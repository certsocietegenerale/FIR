This plugin leverages the [MISP ](https://www.misp-project.org/) Threat Intelligence platform in order to enrich incidents. When opening an incident, a "MISP" tab will display all known observables and indicators matching your incident's artifacts, as well as related events.

You can also send your artifacts to MISP directly from FIR.


## Install

First, follow the generic plugin installation instructions in [the FIR wiki](https://github.com/certsocietegenerale/FIR/wiki/Plugins).

Then, each user needs to set his MISP API key and the location of the MISP instance in his profile page (by clicking on his username).
Alternatively, an administrator you can also set up the API key and location globally, by defining the settings `MISP_URL` and `MISP_APIKEY` in FIR config.


