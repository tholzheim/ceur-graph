import logging
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordRequestForm

from ceur_graph.api import ceurws, wd_migrate
from ceur_graph.api.auth import login_user
from ceur_graph.codegen import get_routers

logging.basicConfig(level=logging.INFO)

app = FastAPI()

for router in get_routers():
    app.include_router(router)

app.include_router(wd_migrate.router)
app.include_router(ceurws.router)


@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    return await login_user(form_data.username, form_data.password)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
