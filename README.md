![GitHub](https://img.shields.io/github/license/tholzheim/ceur-graph)
![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)
![Development Status](https://img.shields.io/badge/status-beta-yellowgreen.svg)
# CEUR-Graph
CEUR-Graph is a Python library that provides a RESTful API for adding CEUR-WS data into the CEUR-dev Wikibase instance. This instance functions as a semantification target for CEUR-WS and is synchronized with Wikidata.
## Features
* RESTful API: Easily add and manage CEUR-WS data. 
* Wikibase Integration: Seamlessly integrates with the CEUR-dev Wikibase instance. 
* Synchronization with Wikidata: Keeps your data in sync with Wikidata.


## Usage
To run the FastAPI application, execute the following command:
```shell
uv run fastapi dev src/ceur_graph/main.py
```

To format the code using Ruff, run:
```shell
uv run ruff format
```


## Docker Support

CEUR-Graph can be easily deployed using Docker.

To Start the Docker Container:
```shell
docker compose up
```

To Stop the Docker Container:

```shell
docker compose down
```


## License

This project is licensed under the [Apache License, Version 2.0](./LICENSE).


## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
