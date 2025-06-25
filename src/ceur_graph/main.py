import logging
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordRequestForm

from ceur_graph.api import (
    ceurws,
    paper_authors,
    paper_reference,
    paper_subject,
    papers,
    volume,
    volume_editors,
    volume_subject,
    wd_migrate,
)
from ceur_graph.api.auth import login_user

logging.basicConfig(level=logging.INFO)

app = FastAPI()
app.include_router(papers.router)
app.include_router(paper_authors.router)
app.include_router(paper_subject.router)
app.include_router(paper_reference.router)
app.include_router(volume.router)
app.include_router(volume_subject.router)
app.include_router(volume_editors.router)
app.include_router(wd_migrate.router)
app.include_router(ceurws.router)


@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    return await login_user(form_data.username, form_data.password)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
