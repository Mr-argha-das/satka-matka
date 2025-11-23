import json
from app.models import Market, RateChart

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import FileResponse
from datetime import datetime, time
import os
import uuid
from mongoengine.errors import NotUniqueError
from ...auth import get_current_user, require_admin
from ...models import DepositQR, Result, Transaction, Wallet, User

from pydantic import BaseModel
from typing import Optional



class MarketInput(BaseModel):
    name: str
    hindi: str
    open_time: str
    close_time: str
    is_active : bool = True
    status : bool = True
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
            hindi=data.hindi,
            open_time=data.open_time,
            close_time=data.close_time,
            marketType=data.marketType,
            is_active=data.is_active,
            status=data.status
        )
        market.save()
        return {"message": "Market created successfully", "id": str(market.id)}
    
    except NotUniqueError:
        raise HTTPException(status_code=400, detail="Market already exists")
    
@router.get("/user/markets/")
def get_user_markets(user=Depends(get_current_user)):
    markets = Market.objects(is_active=True, marketType="Market")
    final_markets = []
    
    # TODAY DATE RANGE (12:00 AM – 11:59 PM)
    today = datetime.utcnow().date()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)

    for m in markets:
        data = json.loads(m.to_json())

        # AUTO CALCULATE STATUS
        auto_status = compute_status(m.open_time, m.close_time)
        data["status"] = auto_status

        # ---- GET TODAY'S RESULT FOR THIS MARKET ----
        todays_result = Result.objects(
            market_id=str(m.id),
            date__gte=start,
            date__lte=end
        ).first()

        data["today_result"] = (
            json.loads(todays_result.to_json()) if todays_result else None
        )

        final_markets.append(data)

    return {
        "message": "Markets fetched successfully",
        "data": final_markets
    }

@router.get("/user/starline/")
def get_user_markets(user=Depends(get_current_user)):
    markets = Market.objects(is_active=True, marketType="Starline")
    final_markets = []
    
    # TODAY DATE RANGE (12:00 AM – 11:59 PM)
    today = datetime.utcnow().date()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)

    for m in markets:
        data = json.loads(m.to_json())

        # AUTO CALCULATE STATUS
        auto_status = compute_status(m.open_time, m.close_time)
        data["status"] = auto_status

        # ---- GET TODAY'S RESULT FOR THIS MARKET ----
        todays_result = Result.objects(
            market_id=str(m.id),
            date__gte=start,
            date__lte=end
        ).first()

        data["today_result"] = (
            json.loads(todays_result.to_json()) if todays_result else None
        )

        final_markets.append(data)

    return {
        "message": "Markets fetched successfully",
        "data": final_markets
    }



def compute_status(open_time: str, close_time: str):
    """Return True if current time is between open_time and close_time."""
    try:
        # Normalize to 24hr format
        now = datetime.now().strftime("%I:%M %p")

        fmt = "%I:%M %p"
        open_dt = datetime.strptime(open_time, fmt)
        close_dt = datetime.strptime(close_time, fmt)
        now_dt = datetime.strptime(now, fmt)

        # Handle cross-midnight cases
        if open_dt <= close_dt:
            return open_dt <= now_dt <= close_dt
        else:
            return now_dt >= open_dt or now_dt <= close_dt

    except Exception:
        # if time invalid → fallback to DB saved value
        return False    
    
@router.get("/market/")
def get_markets(admin=Depends(require_admin)):
    markets = Market.objects()
    final_markets = []
    
    # TODAY DATE RANGE (12:00 AM – 11:59 PM)
    today = datetime.utcnow().date()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)

    for m in markets:
        data = json.loads(m.to_json())

        # AUTO CALCULATE STATUS
        auto_status = compute_status(m.open_time, m.close_time)
        data["status"] = auto_status

        # ---- GET TODAY'S RESULT FOR THIS MARKET ----
        todays_result = Result.objects(
            market_id=str(m.id),
            date__gte=start,
            date__lte=end
        ).first()

        data["today_result"] = (
            json.loads(todays_result.to_json()) if todays_result else None
        )

        final_markets.append(data)

    return {
        "message": "Markets fetched successfully",
        "data": final_markets
    }

@router.get("/market/{market_id}")
def get_market(market_id: str, admin=Depends(require_admin)):
    market = Market.objects(id=market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    data = json.loads(market.to_json())

    # AUTO CALCULATE STATUS
    data["status"] = compute_status(market.open_time, market.close_time)

    # TODAY DATE RANGE
    today = datetime.utcnow().date()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)

    todays_result = Result.objects(
        market_id=str(market.id),
        date__gte=start,
        date__lte=end
    ).first()

    if todays_result:
        data["today_result"] = json.loads(todays_result.to_json())
    else:
        data["today_result"] = None

    return {
        "message": "Market fetched successfully",
        "data": data
    }


@router.put("/market/{market_id}")
def update_market(market_id: str, data: MarketInput,admin = Depends(require_admin)):
    market = Market.objects(id=market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    market.name = data.name
    market.hindi = data.hindi
    market.open_time = data.open_time
    market.close_time = data.close_time
    market.marketType = data.marketType
    market.is_active = data.is_active
    market.status = data.status

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



