## Install

First, follow the generic plugin installation instructions in [the FIR wiki](https://github.com/certsocietegenerale/FIR/wiki/Plugins).

Then, create the `fir_threatintel/static/fir_threatintel/yeti_endpoints.js`:

    $ cp fir_threatintel/static/fir_threatintel/yeti_endpoints.js.sample fir_threatintel/static/fir_threatintel/yeti_endpoints.js

Edit this file if your Yeti instance is behind basic authentication.

## Usage

This plugin leverages the [YETI](https://yeti-platform.github.io/) Threat Intelligence platform in order to enrich incidents. When opening an incident, a "Threat Intel" tab will display all known observables and indicators matching your incident's artifacts, as well as related entities.

You can also send your artifacts to Yeti directly from FIR.

In order for this integration to work, each FIR user should set his Yeti API key in his profile page (by clicking on his username).
