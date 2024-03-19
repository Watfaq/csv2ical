from typing import Annotated
from fastapi import FastAPI, Form, Request

from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import csv
from ics import Calendar, Event

from datetime import datetime
from zoneinfo import ZoneInfo

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/")
async def main(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/")
async def download(
    content: Annotated[str, Form()],
    datetime_format: Annotated[str, Form(alias="datetime-format")],
):
    c = Calendar()
    for row in csv.DictReader(content.splitlines()):
        subject = row.get("Subject", None)
        start_date = row.get("Start Date", None)
        start_time = row.get("Start Time", "00:00")
        end_date = row.get("End Date", None)
        end_time = row.get("End Time", "00:00")
        description = row.get("Description", "")
        location = row.get("Location", "")

        if subject is None or start_date is None:
            continue

        e = Event()
        e.name = subject
        
        d = datetime.strptime(start_date + " " + start_time, datetime_format).replace(tzinfo=
                                                                                      ZoneInfo("Australia/Sydney"))
        e.begin = d.isoformat()

        if not end_date:
            end_date = start_date
        
        d = datetime.strptime(end_date + " " + end_time, datetime_format).replace(tzinfo=ZoneInfo("Australia/Sydney"))
        e.end = d.isoformat() 

        e.description = description
        e.location = location
        c.events.add(e)

    return StreamingResponse(
        c.serialize_iter(),
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=calendar.ics"},
    )


@app.exception_handler(Exception)
async def validation_exception_handler(request: Request, exc: Exception):
    # Change here to Logger
    return JSONResponse(
        status_code=500,
        content={
            "message": (
                f"Failed method {request.method} at URL {request.url}."
                f" Exception message is {exc!r}."
            )
        },
    )
