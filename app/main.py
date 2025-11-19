from fastapi import FastAPI
from mongoengine import connect
from app.config import settings
from app.routes import auth_routes, bet_routes, admin_routes
import os

app = FastAPI(title="Matka Satka Backend")

# connect mongo
connect(host=settings.MONGO_URI)

app.include_router(auth_routes.router)
app.include_router(bet_routes.router)
app.include_router(admin_routes.router)

@app.get("/")
def root():
    return {"status":"ok", "message":"Matka backend running"}
