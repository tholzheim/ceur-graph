import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from wikibasemigrator.migrator import WikibaseMigrator
from wikibasemigrator.model.profile import UserToken, WikibaseMigrationProfile, load_profile

from ceur_graph.api.auth import get_current_user
from ceur_graph.ceur_dev import CeurDev
from ceur_graph.datamodel.auth import WikibaseAuthorizationConfig, WikibaseLoginTypes

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/wd",
    tags=["Wikidata"],
    # dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


@router.post("/import/{entity_id}")
def wikidata_import(
    entity_id: str,
    ceur_dev: Annotated[CeurDev, Depends(get_current_user)],
    summary: str | None = None,
):
    """
    Import the given Wikidata entity corresponding to the provided entity_id.
    """
    # todo fix for proper resource loading
    path = Path(__file__).parent.parent.joinpath("./resources/migration_profiles/wd_to_ceur-dev.yaml")
    migration_profile = load_profile(path)
    if ceur_dev.auth_config is None:
        return {
            "error": True,
            "message": "Authentication configuration not provided. Please ensure that you are logged in",
        }
    update_migration_profile(ceur_dev.auth_config, migration_profile)
    try:
        migrator = WikibaseMigrator(migration_profile)
        translations = migrator.translate_entities_by_id([entity_id])
        migrated_entities = migrator.migrate_entities_to_target(translations, summary=summary)
        qid = migrated_entities[0].created_entity.id
        return {"error": False, "wikidata_id": entity_id, "ceurdev_id": qid}
    except Exception as e:
        logger.error(f"Failed to migrate {entity_id}: {e}")
        return {"error": True, "message": str(e)}


def update_migration_profile(auth_config: WikibaseAuthorizationConfig, profile: WikibaseMigrationProfile):
    """
    Update the authentication information of the migration profile
    :param auth_config: wikibase auth config to use for updating the migration profile target
    :param profile: migration profile to update
    :return:
    """
    match auth_config.auth_type:
        case WikibaseLoginTypes.NONE:
            pass
        case WikibaseLoginTypes.USER:
            profile.target.user = auth_config.user
            profile.target.password = auth_config.password
        case WikibaseLoginTypes.BOT:
            profile.target.user = auth_config.user
            profile.target.bot_password = auth_config.password
        case WikibaseLoginTypes.OAUTH1:
            profile.target.consumer_key = auth_config.consumer_token
            profile.target.consumer_secret = auth_config.consumer_secret
            profile.target.user_token = UserToken(
                oauth_token=auth_config.access_token, oauth_token_secret=auth_config.access_secret
            )
        case WikibaseLoginTypes.OAUTH2:
            logger.info("OAuth2 is currently not supported by wikibase migrator")
        case _:
            raise Exception(f"Unknown auth_type {auth_config.auth_type}")
