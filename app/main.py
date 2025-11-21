from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # <-- 1. Import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from mongoengine import connect
from app.config import settings
from app.routes import auth_routes, admin_routes, user_routes, withdrawal_routes, bids_routes, chart, admin_result, market, jackpot,passbook, images_routes, deposit_qr
import os

app = FastAPI(title="Matka Satka Backend")

origins = [
    "http://localhost:5173",  
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connect(host=settings.MONGO_URI)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(auth_routes.router)
app.include_router(admin_routes.router)
app.include_router(user_routes.router)
app.include_router(withdrawal_routes.router)
app.include_router(bids_routes.router)
app.include_router(chart.router)
app.include_router(admin_result.router)
app.include_router(market.router)
app.include_router(images_routes.router)
app.include_router(deposit_qr.router)
app.include_router(passbook.router)
app.include_router(jackpot.router)


@app.get("/")
def root():
    return {"status":"ok", "message":"Matka backend running"}

