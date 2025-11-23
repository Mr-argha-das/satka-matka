import json
from app.models import Market, RateChart
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import FileResponse
from datetime import datetime
import os
import uuid
from mongoengine.errors import NotUniqueError
from ...auth import get_current_user, require_admin
from ...models import DepositQR, Transaction, Wallet, User

from pydantic import BaseModel
from typing import Optional


class MarketInput(BaseModel):
    name: str
    open_time: str
    close_time: str
    marketType: str 
class RateChartInput(BaseModel):
    single_digit_1: Optional[int] = None
    jodi_digit_1: Optional[int] = None
    single_pana_1: Optional[int] = None
    double_pana_1: Optional[int] = None
    tripple_pana_1: Optional[int] = None
    half_sangam_1: Optional[int] = None
    full_sangam_1: Optional[int] = None
    left_digit_1: Optional[int] = None
    right_digit_1: Optional[int] = None
    starline_single_digit_1: Optional[int] = None
    starline_single_pana_1: Optional[int] = None
    starline_double_pana_1: Optional[int] = None
    starline_tripple_pana_1: Optional[int] = None

    single_digit_2: Optional[int] = None
    jodi_digit_2: Optional[int] = None
    single_pana_2: Optional[int] = None
    double_pana_2: Optional[int] = None
    tripple_pana_2: Optional[int] = None
    half_sangam_2: Optional[int] = None
    full_sangam_2: Optional[int] = None
    left_digit_2: Optional[int] = None
    right_digit_2: Optional[int] = None
    starline_single_digit_2: Optional[int] = None
    starline_single_pana_2: Optional[int] = None
    starline_double_pana_2: Optional[int] = None
    starline_tripple_pana_2: Optional[int] = None


router = APIRouter(prefix="/api/admin", tags=["Game Management"])

@router.get("/rate/")
def get_rate_chart():
    chart = RateChart.objects().first()
    if not chart:
        return {"message": "No rate chart found"}
    return chart.to_mongo().to_dict()

@router.post("/rate/")
def create_or_update_rate_chart(data: RateChartInput,admin = Depends(require_admin)):
    chart = RateChart.objects().first()
    if not chart:
        chart = RateChart()
    data_dict = data.dict(exclude_unset=True)
    for key, value in data_dict.items():
        setattr(chart, key, value)
    chart.save()
    return {
        "message": "Rate chart updated successfully",
        "data": json.loads(chart.to_json())
    }
@router.post("/market/")
def create_market(data: MarketInput,admin = Depends(require_admin)):
    try:
        market = Market(
            name=data.name,
            open_time=data.open_time,
            close_time=data.close_time,
            marketType=data.marketType
        )
        market.save()
        return {"message": "Market created successfully", "id": str(market.id)}
    
    except NotUniqueError:
        raise HTTPException(status_code=400, detail="Market already exists")
@router.get("/market/")
def get_markets(admin = Depends(require_admin)):
    markets = Market.objects()
    return {
        "message": "Markets fetched successfully",
        "data" : json.loads(markets.to_json())
    }
@router.get("/market/{market_id}")
def get_market(market_id: str,admin = Depends(require_admin)):
    market = Market.objects(id=market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")
    return {
        "message": "Market fetched successfully",
        "data": json.loads(market.to_json())
    }
@router.put("/market/{market_id}")
def update_market(market_id: str, data: MarketInput,admin = Depends(require_admin)):
    market = Market.objects(id=market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    market.name = data.name
    market.open_time = data.open_time
    market.close_time = data.close_time
    market.marketType = data.marketType

    try:
        market.save()
    except NotUniqueError:
        raise HTTPException(status_code=400, detail="Market name already exists")

    return {"message": "Market updated successfully"}
@router.patch("/market/{market_id}/status")
def update_market_status(market_id: str, status: bool,admin = Depends(require_admin)):
    market = Market.objects(id=market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    market.status = status
    market.save()

    return {"message": "Market status updated", "status": status}
@router.delete("/market/{market_id}")
def delete_market(market_id: str,admin = Depends(require_admin)):
    market = Market.objects(id=market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    market.delete()
    return {"message": "Market deleted successfully"}
