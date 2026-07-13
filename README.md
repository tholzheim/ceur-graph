![GitHub](https://img.shields.io/github/license/tholzheim/ceur-graph)
![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)
![Development Status](https://img.shields.io/badge/status-beta-yellowgreen.svg)
# wbforms
wbforms (Wikibase forms) is a schema-driven web application for editing entities in a Wikibase instance. A [LinkML](https://linkml.io) schema describes the entity types, their statements, qualifiers, and references; at startup wbforms generates the Pydantic models, REST CRUD endpoints, and edit forms from that schema. Point it at a different schema and Wikibase instance to serve a different use case — no code changes required.

Bundled use cases:
* **CEUR-WS** (`src/wbforms/schema/ceur_graph.yaml`, default): proceedings/paper metadata in the [CEUR-dev Wikibase](https://ceur-dev.wikibase.cloud), synchronized with Wikidata.
* **FactGrid Besucherbuch** (`src/wbforms/schema/factgrid_besucherbuch.yaml`): visitor-book records in [FactGrid](https://database.factgrid.de).

## Features
* Schema-driven: entity types, forms, and REST endpoints are generated from a LinkML schema at startup.
* RESTful API: CRUD endpoints for items and (qualified) statements, with OpenAPI docs at `/docs`.
* Wikibase integration: reads and writes via WikibaseIntegrator and SPARQL; works with wikibase.cloud and classic MediaWiki deployments.
* OAuth 2.0 / 1.0a and bot-password login.

## Usage
To run the FastAPI application, execute the following command:
```shell
uv run fastapi dev src/wbforms/main.py
```

To format the code using Ruff, run:
```shell
uv run ruff format
```


## Frontend tooling

JavaScript files in `src/wbforms/static/js/` are checked with [Biome](https://biomejs.dev) (requires Node ≥ 18).

Install once:
```shell
npm install -g @biomejs/biome
```

Check formatting and linting:
```shell
biome check src/wbforms/static/js/
```

Auto-fix (format + safe lint fixes):
```shell
biome check --write src/wbforms/static/js/
```


## Configuration

The Wikibase URLs, schema path, and OAuth client credentials are read from
environment variables (or a `.env` file) at startup. All variables are
prefixed with `WBFORMS_`. The Wikibase URLs default to the public CEUR-dev
instance, so you only need to override them when targeting a different
Wikibase.

| Variable | Purpose | Default |
| --- | --- | --- |
| `WBFORMS_WIKIBASE_WEBSITE` | Wikibase root URL | `https://ceur-dev.wikibase.cloud/` |
| `WBFORMS_WIKIBASE_SPARQL_ENDPOINT` | SPARQL endpoint | `.../query/sparql` |
| `WBFORMS_WIKIBASE_ITEM_PREFIX` | Item IRI prefix | `.../entity/` |
| `WBFORMS_WIKIBASE_PROPERTY_PREFIX` | Property IRI prefix | `.../prop/direct/` |
| `WBFORMS_WIKIBASE_MEDIAWIKI_API_URL` | MediaWiki API (`/w/api.php`) | `.../w/api.php` |
| `WBFORMS_WIKIBASE_MEDIAWIKI_REST_URL` | MediaWiki REST API (`/w/rest.php`) | `.../w/rest.php` |
| `WBFORMS_OAUTH_VERSION` | `"2.0"` (Wikibase REST) or `"1.0a"` (classic MediaWiki, e.g. FactGrid) | `2.0` |
| `WBFORMS_OAUTH_CLIENT_ID` | OAuth consumer ID/token (2.0: `client_id`; 1.0a: consumer token) | _required for login_ |
| `WBFORMS_OAUTH_CLIENT_SECRET` | OAuth consumer secret (same field, both versions) | _required for login_ |
| `WBFORMS_OAUTH_REDIRECT_URI` | Callback URL registered with the OAuth consumer | _required for login_ |
| `WBFORMS_APP_BASE_URL` | Public base URL of the SPA | `http://localhost:8000/` |
| `WBFORMS_SESSION_TTL_MINUTES` | Session lifetime | `60` |
| `WBFORMS_SCHEMA_PATH` | LinkML schema file driving model + router codegen | bundled `ceur_graph.yaml` |

A ready-to-edit template is provided at `.env.example` — copy it to `.env`
and adjust the values for your deployment.

For `OAUTH_VERSION=2.0` (default — wikibase.cloud-hosted instances such as
ceur-dev), register an OAuth 2.0 consumer (confidential client,
authorization-code grant) at
`${WIKIBASE_WEBSITE}wiki/Special:OAuthConsumerRegistration/propose` with the
callback URL set to `${WBFORMS_OAUTH_REDIRECT_URI}`
(e.g. `http://localhost:8000/oauth/callback`).

For `OAUTH_VERSION=1.0a` (classic MediaWiki deployments such as FactGrid),
register an OAuth 1.0a consumer at
`${WIKIBASE_WEBSITE}wiki/Special:OAuthConsumerRegistration/propose/oauth1a`
with the same callback URL. Use the resulting consumer token/secret as
`WBFORMS_OAUTH_CLIENT_ID` / `WBFORMS_OAUTH_CLIENT_SECRET`.

The login button in the UI redirects to the Wikibase login, and after
consent the user is sent back to the SPA with a session token. The REST
API additionally accepts bot credentials via `POST /token`, so
non-interactive clients keep working.

## Docker Support

wbforms can be easily deployed using Docker.

Copy `.env.example` to `.env`, fill in the OAuth credentials (and any
Wikibase URLs you want to override), then:

```shell
docker compose up
```

To stop:

```shell
docker compose down
```

To deploy against a different LinkML schema, place your schema YAML next
to `docker-compose.yml`, uncomment the `volumes:` block in
`docker-compose.yml`, and point `WBFORMS_SCHEMA_PATH` in `.env` at
the in-container mount path.


## License

This project is licensed under the [Apache License, Version 2.0](./LICENSE).


## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
