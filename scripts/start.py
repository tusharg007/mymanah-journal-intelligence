from __future__ import annotations

import logging

import uvicorn

from mymanah.api import create_app
from mymanah.config import Settings

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    settings = Settings.from_env()
    uvicorn.run(create_app(settings), host=settings.host, port=settings.port, workers=1, access_log=False)
