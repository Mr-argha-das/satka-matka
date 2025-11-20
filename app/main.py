from fastapi import FastAPI
from mongoengine import connect
from app.config import settings
from app.routes import auth_routes, bet_routes, admin_routes, user_routes, withdrawal_routes, bids_routes, chart, admin_result, market
import os

app = FastAPI(title="Matka Satka Backend")

# connect mongo
connect(host=settings.MONGO_URI)

app.include_router(auth_routes.router)
app.include_router(bet_routes.router)
app.include_router(admin_routes.router)
app.include_router(user_routes.router,)
app.include_router(withdrawal_routes.router)
app.include_router(bids_routes.router, tags=["Bids"])
app.include_router(chart.router, tags=["Charts"])
app.include_router(admin_result.router, tags=["Admin Results"])
app.include_router(market.router, tags=["Market"])


@app.get("/")
def root():
    return {"status":"ok", "message":"Matka backend running"}
