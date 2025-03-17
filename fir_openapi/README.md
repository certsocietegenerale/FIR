# OpenAPI Scheme for FIR

## Features

This plugins allows you to make FIR's API compatible with OpenAPI Schemes and to enable Swagger or Redoc.

## Installation


In your FIR virtualenv, launch:

```bash
(env-FIR)$ pip install -r fir_notifications/requirements.txt

```
In *$FIR_HOME/fir/config/production.py*, add:

```
SPECTACULAR_SETTINGS = {
    "TITLE": "FIR API",
    "DESCRIPTION": "Fast Incident Response OpenAPI specification",
    "VERSION": "0.0.1",
    "SERVE_INCLUDE_SCHEMA": True,
    # OTHER SETTINGS
    "SWAGGER_UI_DIST": "SIDECAR",  # shorthand to use the sidecar instead
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
}
```
and in **$FIR_HOME/fir/config/production.py** look for the `INSTALLED_APPS` variable and add this into it
```
    "drf_spectacular",
    "drf_spectacular_sidecar",
```

In *$FIR_HOME/fir/config/installed_app.txt*, add:

```
fir_openapi
```

In your *$FIR_HOME*, launch:

```bash
(env-FIR)$ ./manage.py migrate fir_openapi
```



## Usage

You can access it through one of the following: 
* https://<FIR_Instance_FQDN>/api/schema
* https://<FIR_Instance_FQDN>/api/swagger (if configured)
* https://<FIR_Instance_FQDN>/api/redoc (if configured)

## Configuration

WARNING : If you remove the following line in `urls.py`, it will automatically make swagger and redoc unusable. Don't comment or delete it unless you know what you're doing.     

`re_path(r"^schema/$", SpectacularAPIView.as_view(), name="schema")` 

### Disable Swagger

Comment or remove the following lines in `fir_openapi/urls.py` : 
```python
re_path(
        r"^schema/swagger-ui/$",
        SpectacularSwaggerView.as_view(url_name="fir_api:schema"),
        name="swagger-ui",
    ),
```

### Disable Redoc

Comment or remove the following lines in `fir_openapi/urls.py` : 
```python
    re_path(
        r"^schema/redoc/$",
        SpectacularRedocView.as_view(url_name="fir_api:schema"),
        name="redoc",
    ),
```