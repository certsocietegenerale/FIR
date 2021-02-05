# Quick Start

```
docker-compose build
docker-compose up -d
```

Browse to http://localhost and log in with default credentials admin:admin or dev:dev

Enjoy!

# Customization. 

If you need to change settings related to mysql or redis, you can edit fir.env file and set accordingly. These environments variable are provided to the container and used in composeprod.py file which corresponds to the default settings for django