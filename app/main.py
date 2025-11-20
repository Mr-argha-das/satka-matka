from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # <-- 1. Import CORSMiddleware

from mongoengine import connect
from app.config import settings
from app.routes import auth_routes, admin_routes, user_routes, withdrawal_routes, bids_routes, chart, admin_result, market
import os

app = FastAPI(title="Matka Satka Backend")

origins = [
    "http://localhost:5173",  # Default React development port
    "*"
]

# 3. Add CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers, including Authorization
)

# connect mongo
connect(host=settings.MONGO_URI)

app.include_router(auth_routes.router)
# app.include_router(bet_routes.router)
app.include_router(admin_routes.router)
app.include_router(user_routes.router,)
app.include_router(withdrawal_routes.router)

app.include_router(bids_routes.router)
app.include_router(chart.router)
app.include_router(admin_result.router)
app.include_router(market.router)


@app.get("/")
def root():
    return {"status":"ok", "message":"Matka backend running"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)