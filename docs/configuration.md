# Configuration reference

wbforms is configured entirely through environment variables (or a `.env` file). The
settings model lives in `src/wbforms/settings.py` (`Settings`, based on
pydantic-settings):

- all variables use the prefix `WBFORMS_`,
- a `.env` file in the **project root** or the current working directory is loaded
  automatically (UTF-8); set the real environment variable `WBFORMS_ENV_FILE` to load a
  different file instead (e.g. `WBFORMS_ENV_FILE=.env.factgrid`),
- unknown variables in the environment/`.env` are ignored,
- settings are read **once** per process (`get_settings()` is cached) — configuration
  changes require a restart (editing `.env` does not trigger the `fastapi dev` reloader),
- the startup log reports which env file(s) were loaded and which Wikibase instance is
  targeted; if none is found the service falls back to the built-in ceur-dev defaults.

A ready-to-edit template is tracked at `.env.example`; copy it to `.env` and fill in the
values. Keep one preset file per deployment target (e.g. a CEUR-dev and a FactGrid
variant) and either copy the one you need over `.env` or select it via
`WBFORMS_ENV_FILE`. **Never commit `.env` files containing real OAuth secrets.**

## Settings

### Wikibase target

All URLs default to the public CEUR-dev instance, so the service runs read-only against
CEUR-dev with zero configuration. Override all six when targeting another Wikibase:

| Variable | Purpose | Default |
|---|---|---|
| `WBFORMS_WIKIBASE_WEBSITE` | Wikibase root URL | `https://ceur-dev.wikibase.cloud/` |
| `WBFORMS_WIKIBASE_SPARQL_ENDPOINT` | SPARQL query endpoint | `.../query/sparql` |
| `WBFORMS_WIKIBASE_ITEM_PREFIX` | Item IRI prefix (`.../entity/`) | `.../entity/` |
| `WBFORMS_WIKIBASE_PROPERTY_PREFIX` | Direct-property IRI prefix | `.../prop/direct/` |
| `WBFORMS_WIKIBASE_MEDIAWIKI_API_URL` | MediaWiki action API; used for login and the entity-search/label proxies | `.../w/api.php` |
| `WBFORMS_WIKIBASE_MEDIAWIKI_REST_URL` | MediaWiki REST API; used for OAuth 2.0 writes | `.../w/rest.php` |

### Schema selection

| Variable | Purpose | Default |
|---|---|---|
| `WBFORMS_SCHEMA_PATH` | Path to the LinkML schema that drives model, endpoint, and form generation (see [schema-authoring.md](schema-authoring.md)) | bundled `src/wbforms/schema/ceur_graph.yaml` |

The schema is read at import time; **switching schemas requires a process restart**.
Bundled alternatives: `ceur_graph.yaml` (CEUR-dev) and `factgrid_besucherbuch.yaml`
(FactGrid). With Docker, mount your schema file into the container (uncomment the
`volumes:` block in `docker-compose.yml`) and point `WBFORMS_SCHEMA_PATH` at the
in-container path.

### OAuth / sessions

| Variable | Purpose | Default |
|---|---|---|
| `WBFORMS_OAUTH_VERSION` | `"2.0"` (wikibase.cloud / MediaWiki REST) or `"1.0a"` (classic MediaWiki, e.g. FactGrid) | `2.0` |
| `WBFORMS_OAUTH_CLIENT_ID` | OAuth consumer ID (2.0: `client_id`; 1.0a: consumer token) | unset — required for OAuth login |
| `WBFORMS_OAUTH_CLIENT_SECRET` | OAuth consumer secret (both versions) | unset — required for OAuth login |
| `WBFORMS_OAUTH_REDIRECT_URI` | Callback URL registered with the consumer, e.g. `http://localhost:8000/oauth/callback` | unset — required for OAuth login |
| `WBFORMS_APP_BASE_URL` | Public base URL of the SPA (used for the post-login redirect) | `http://localhost:8000/` |
| `WBFORMS_SESSION_TTL_MINUTES` | Lifetime of issued session tokens (JWT) | `60` |

### Other environment variables (not `WBFORMS_`-prefixed)

| Variable | Purpose | Default |
|---|---|---|
| `LOG_LEVEL` | Python logging level of the app logger | `DEBUG` |
| `PYTHONUTF8` | Set to `1` on Windows — avoids a cp1252 encoding error in the FastAPI CLI startup banner | unset |

## Authentication setup

wbforms supports three login mechanisms; all of them end in a JWT bearer token that the
generated CRUD endpoints require.

### OAuth 2.0 (default — wikibase.cloud instances)

Register an OAuth 2.0 consumer (confidential client, authorization-code grant) at
`${WBFORMS_WIKIBASE_WEBSITE}wiki/Special:OAuthConsumerRegistration/propose`, with the
callback URL set to your `WBFORMS_OAUTH_REDIRECT_URI`. Put the resulting client id and
secret into `WBFORMS_OAUTH_CLIENT_ID` / `WBFORMS_OAUTH_CLIENT_SECRET`.

### OAuth 1.0a (classic MediaWiki, e.g. FactGrid)

Set `WBFORMS_OAUTH_VERSION=1.0a` and register a 1.0a consumer at
`${WBFORMS_WIKIBASE_WEBSITE}wiki/Special:OAuthConsumerRegistration/propose/oauth1a` with
the same callback URL. Use the consumer token/secret as
`WBFORMS_OAUTH_CLIENT_ID` / `WBFORMS_OAUTH_CLIENT_SECRET`.

In both cases the SPA's login button redirects to the wiki, and after consent the user
returns to the SPA with a session token in the URL fragment.

### Bot password (non-interactive clients)

`POST /token` with username/password form fields (a MediaWiki bot password works)
returns a bearer token directly — useful for scripts and API clients that cannot do the
OAuth dance.

### Operational caveats

- The JWT signing key is generated randomly **per process** (`api/auth.py`): all issued
  tokens become invalid on restart, and tokens are not portable across multiple worker
  processes.
- Sessions live in an in-process dict — run a single worker, or put sticky sessions in
  front if you scale out.

## Deployment

```shell
docker compose up      # serves on port 9005
```

Copy `.env.example` to `.env` first and fill in the OAuth credentials plus any Wikibase
URL overrides; `docker-compose.yml` passes the `.env` file to the container. For local
development instead:

```shell
PYTHONUTF8=1 uv run fastapi dev src/wbforms/main.py    # serves on port 8000
```
