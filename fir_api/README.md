## Install

Follow the generic plugin installation instructions in [the FIR wiki](https://github.com/certsocietegenerale/FIR/wiki/Plugins).

## Usage

The `fir_api` plugin allows you to interact with FIR programmatically.
The API is pretty much self documented in the dedicated web interface available at `http(s)://YOURFIRINSTALL/api/`.

### Authentication

You need to be authenticated in order to use the API.
It will accept session or token based authentication.
Tokens can be retrieved from your user profile (`http(s)://YOURFIRINSTALL/user/profile`) and should be specified as a request header.
Example:

```
X-Api: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

### Querying the API

The APIs endpoints are all documented at `http(s)://YOURFIRINSTALL/api/`. 

As example, here is how to add a comment to an incident via API, using different languages/tools:

Python:
```
import requests
requests.post("http(s)://YOURFIRINSTALL/api/comments", headers={"X-API": "Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"}, json={"comment": "This is a comment made via API", "incident": 1, "action": "Info"}).json()

```

curl:
```
curl http(s)://YOURFIRINSTALL/api/comments -H "X-API: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b" -H "Content-Type: application/json" -X POST -d '{"comment": "This is a comment made via API", "incident": 1, "action": "Info"}'
```

powershell:
```
Invoke-RestMethod http(s)://YOURFIRINSTALL/api/comments  -Method 'Post' -Headers @{"X-API"="Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"} -Body @{"comment"="This is a comment made via API"; "incident"="1"; "action"="Info"}
```
