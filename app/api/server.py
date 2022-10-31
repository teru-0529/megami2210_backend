#!/usr/bin/python3
# server.py

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def hello():
    return {"message": "Hello World!"}
