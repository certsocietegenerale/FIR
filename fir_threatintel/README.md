This plugin leverages the [YETI](https://yeti-platform.github.io/) Threat Intelligence platform in order to enrich incidents. When opening an incident, a "Threat Intel" tab will display all known observables and indicators matching your incident's artifacts, as well as related entities.

You can also send your artifacts to Yeti directly from FIR.


## Install

First, follow the generic plugin installation instructions in [the FIR wiki](https://github.com/certsocietegenerale/FIR/wiki/Plugins).

Then, each user need to set his Yeti API key and the location of the Yeti instance in his profile page (by clicking on his username).
Alternatively, an administrator you can also set up the API key and location globally, by defining the settings `YETI_URL` and `YETI_APIKEY` in FIR config.
