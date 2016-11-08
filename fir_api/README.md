## Install

Follow the generic plugin installation instructions in [the FIR wiki](https://github.com/certsocietegenerale/FIR/wiki/Plugins).

## Usage

The `fir_api` plugin allows you to interact with FIR programmatically. The API is pretty much self documented in the dedicated web interface available at `http(s)://YOURFIRINSTALL/api/`.

### Authentication

You need to be authenticated in order to use the API. It will accept session or token based authentication. Tokens can be managed in the administration interface and should be specified as a request header. Example:

```
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```
