#!/usr/bin/python3
# -*- coding:utf-8 -*-
# Project: http://cloudedbats.org, https://github.com/cloudedbats
# Copyright (c) 2023-present Arnold Andreasson
# License: MIT License (see LICENSE or http://opensource.org/licenses/mit).

import time
import datetime
import asyncio
import logging
import fastapi
import fastapi.staticfiles
import fastapi.templating
from pydantic import BaseModel
from typing import Optional
import websockets.exceptions

# CloudedBats WURB.
import wurb_core
import wurb_app

logger = logging.getLogger(wurb_core.used_logger)

app = fastapi.FastAPI(
    title="CloudedBats WURB-2023",
    description="CloudedBats WURB-2023, the DIY bat detector.",
    version=wurb_core.__version__,
)

app.mount(
    "/static",
    fastapi.staticfiles.StaticFiles(directory="wurb_app/static"),
    name="static",
)
templates = fastapi.templating.Jinja2Templates(directory="wurb_app/templates")


@app.on_event("startup")
async def startup_event():
    """ """
    logger.debug("API called: startup.")


@app.on_event("shutdown")
async def shutdown_event():
    """ """
    logger.debug("API called: shutdown.")


# Include modules.
app.include_router(wurb_app.record_router)
app.include_router(wurb_app.live_router)
app.include_router(wurb_app.annotations_router)
app.include_router(wurb_app.admin_router)
app.include_router(wurb_app.about_router)


@app.get("/")
async def webpage(request: fastapi.Request):
    """ """
    try:
        logger.debug("API called: webpage.")
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "wurb_version": wurb_core.__version__,
            },
        )
    except Exception as e:
        logger.debug("Exception: webpage: " + str(e))
