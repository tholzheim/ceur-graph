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


## Frontend tooling

JavaScript files in `src/ceur_graph/static/js/` are checked with [Biome](https://biomejs.dev) (requires Node ≥ 18).

Install once:
```shell
npm install -g @biomejs/biome
```

Check formatting and linting:
```shell
biome check src/ceur_graph/static/js/
```

Auto-fix (format + safe lint fixes):
```shell
biome check --write src/ceur_graph/static/js/
```


## Configuration

The Wikibase URLs and OAuth client credentials are read from environment
variables (or a `.env` file) at startup. All variables are prefixed with
`CEUR_GRAPH_`. The Wikibase URLs default to the public CEUR-dev instance,
so you only need to override them when targeting a different Wikibase.

| Variable | Purpose | Default |
| --- | --- | --- |
| `CEUR_GRAPH_WIKIBASE_WEBSITE` | Wikibase root URL | `https://ceur-dev.wikibase.cloud/` |
| `CEUR_GRAPH_WIKIBASE_SPARQL_ENDPOINT` | SPARQL endpoint | `.../query/sparql` |
| `CEUR_GRAPH_WIKIBASE_ITEM_PREFIX` | Item IRI prefix | `.../entity/` |
| `CEUR_GRAPH_WIKIBASE_PROPERTY_PREFIX` | Property IRI prefix | `.../prop/direct/` |
| `CEUR_GRAPH_WIKIBASE_MEDIAWIKI_API_URL` | MediaWiki API (`/w/api.php`) | `.../w/api.php` |
| `CEUR_GRAPH_WIKIBASE_MEDIAWIKI_REST_URL` | MediaWiki REST API (`/w/rest.php`) | `.../w/rest.php` |
| `CEUR_GRAPH_OAUTH_CLIENT_ID` | OAuth 2.0 consumer ID | _required for login_ |
| `CEUR_GRAPH_OAUTH_CLIENT_SECRET` | OAuth 2.0 consumer secret | _required for login_ |
| `CEUR_GRAPH_OAUTH_REDIRECT_URI` | Callback URL registered with the OAuth consumer | _required for login_ |
| `CEUR_GRAPH_APP_BASE_URL` | Public base URL of the SPA | `http://localhost:8000/` |
| `CEUR_GRAPH_SESSION_TTL_MINUTES` | Session lifetime | `60` |

Register an OAuth 2.0 consumer (confidential client, authorization-code
grant) at `${WIKIBASE_WEBSITE}wiki/Special:OAuthConsumerRegistration/propose`
with the callback URL set to `${CEUR_GRAPH_OAUTH_REDIRECT_URI}` (e.g.
`http://localhost:8000/oauth/callback`). The login button in the UI
redirects to the Wikibase login, and after consent the user is sent back
to the SPA with a session token. The REST API additionally accepts bot
credentials via `POST /token`, so non-interactive clients keep working.

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
