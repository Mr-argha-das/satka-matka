import json
from app.new_models import MarketGod, RateChartGod, BidGod, ResultGod

from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, time
import uuid
from mongoengine.errors import NotUniqueError
from ...auth import get_current_user, require_admin
from ...models import Transaction, Wallet
from pydantic import BaseModel
from typing import Optional


router = APIRouter(prefix="/api/admin/Golidesawar", tags=["Golidesawar Game Management"])


# -----------------------------
# INPUT MODELS
# -----------------------------

class ResultDeclare(BaseModel):
    game_id: str
    date: str
    session: str      # open / close
    digit: str = None # 1 digit (open/close) or 2 digit (jodi)


class MarketInput(BaseModel):
    name: str
    hindi: str
    open_time: str
    close_time: str
    is_active: bool = True
    status: bool = True
    marketType: str


class RateChartGodInput(BaseModel):
    single_digit_1: Optional[int] = None
    jodi_digit_1: Optional[int] = None

    single_digit_2: Optional[int] = None
    jodi_digit_2: Optional[int] = None


# -----------------------------
# RATE CHART ROUTES
# -----------------------------

@router.get("/rate/")
def get_rate_chart():
    chart = RateChartGod.objects().first()
    if not chart:
        return {"message": "No rate chart found"}
    return chart.to_mongo().to_dict()


@router.post("/rate/")
def create_or_update_rate_chart(data: RateChartGodInput, admin=Depends(require_admin)):
    chart = RateChartGod.objects().first()
    if not chart:
        chart = RateChartGod()

    data_dict = data.dict(exclude_unset=True)
    for key, value in data_dict.items():
        setattr(chart, key, value)

    chart.save()

    return {
        "message": "Rate chart updated successfully",
        "data": json.loads(chart.to_json())
    }


# -----------------------------
# MARKET CRUD
# -----------------------------

@router.post("/market/")
def create_market(data: MarketInput, admin=Depends(require_admin)):
    try:
        market = MarketGod(**data.dict())
        market.save()
        return {"message": "Market created successfully", "id": str(market.id)}
    except NotUniqueError:
        raise HTTPException(status_code=400, detail="Market already exists")
    
@router.get("/user/markets/")
def get_user_markets(user=Depends(get_current_user)):
    markets = MarketGod.objects(is_active=True, marketType="Market")
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
        todays_result = ResultGod.objects(
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
    markets = MarketGod.objects(is_active=True, marketType="Starline")
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
        todays_result = ResultGod.objects(
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
    try:
        now = datetime.now().strftime("%I:%M %p")
        fmt = "%I:%M %p"

        open_dt = datetime.strptime(open_time, fmt)
        close_dt = datetime.strptime(close_time, fmt)
        now_dt = datetime.strptime(now, fmt)

        if open_dt <= close_dt:
            return open_dt <= now_dt <= close_dt
        else:
            return now_dt >= open_dt or now_dt <= close_dt

    except:
        return False


@router.get("/market/")
def get_markets(admin=Depends(require_admin)):
    markets = MarketGod.objects()
    final_markets = []

    today = datetime.utcnow().date()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)

    for m in markets:
        data = json.loads(m.to_json())

        # AUTO CALCULATE STATUS
        auto_status = compute_status(m.open_time, m.close_time)
        data["status"] = auto_status

        # ---- GET TODAY'S RESULT FOR THIS MARKET ----
        todays_result = ResultGod.objects(
            market_id=str(m.id),
            date__gte=start,
            date__lte=end
        ).first()

        data["today_result"] = (
            json.loads(todays_result.to_json()) if todays_result else None
        )

        final_markets.append(data)

    return {"message": "Markets fetched successfully", "data": final_markets}


@router.get("/market/{market_id}")
def get_market(market_id: str, admin=Depends(require_admin)):
    market = MarketGod.objects(id=market_id).first()
    if not market:
        raise HTTPException(404, "Market not found")

    data = json.loads(market.to_json())
    data["status"] = compute_status(market.open_time, market.close_time)

    today = datetime.utcnow().date()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)

    todays_result = ResultGod.objects(
        market_id=str(market.id),
        date__gte=start,
        date__lte=end
    ).first()

    data["today_result"] = (
        json.loads(todays_result.to_json()) if todays_result else None
    )

    return {"message": "Market fetched successfully", "data": data}


@router.put("/market/{market_id}")
def update_market(market_id: str, data: MarketInput, admin=Depends(require_admin)):
    market = MarketGod.objects(id=market_id).first()
    if not market:
        raise HTTPException(404, "Market not found")

    for k, v in data.dict().items():
        setattr(market, k, v)

    try:
        market.save()
    except NotUniqueError:
        raise HTTPException(400, "Market name already exists")

    return {"message": "Market updated successfully"}


@router.patch("/market/{market_id}/status")
def update_market_status(market_id: str, status: bool, admin=Depends(require_admin)):
    market = MarketGod.objects(id=market_id).first()
    if not market:
        raise HTTPException(404, "Market not found")

    market.status = status
    market.save()

    return {"message": "Market status updated", "status": status}


@router.delete("/market/{market_id}")
def delete_market(market_id: str, admin=Depends(require_admin)):
    market = MarketGod.objects(id=market_id).first()
    if not market:
        raise HTTPException(404, "Market not found")

    market.delete()
    return {"message": "Market deleted successfully"}


# -----------------------------
# RESULT DECLARE (FINAL FIXED)
# -----------------------------

@router.post("/result/declare")
def declare_result(payload: ResultDeclare, admin=Depends(require_admin)):

    session = payload.session.lower()

    if not payload.digit:
        raise HTTPException(400, "Digit is required")

    digit = payload.digit.strip()

    if len(digit) not in [1, 2]:
        raise HTTPException(400, "Digit must be 1 or 2 digits")

    result = ResultGod.objects(
        market_id=payload.game_id, date=payload.date
    ).first()

    if not result:
        result = ResultGod(
            market_id=payload.game_id,
            date=payload.date,
            open_digit="-",
            close_digit="-"
        )

    if session == "open":
        result.open_digit = digit[0]

    elif session == "close":
        result.close_digit = digit[-1]

        if result.open_digit == "-" and len(digit) == 2:
            result.open_digit = digit[0]

    else:
        raise HTTPException(400, "Invalid session")

    result.save()

    settle_results(payload.game_id, result)

    return {"message": "Result declared successfully"}


# -----------------------------
# SETTLEMENT LOGIC
# -----------------------------

def settle_results(market_id: str, result_obj: ResultGod):

    chart = RateChartGod.objects().first()
    if not chart:
        return

    open_digit = result_obj.open_digit
    close_digit = result_obj.close_digit

    bids = BidGod.objects(market_id=market_id)

    for bid in bids:
        win = False

        if bid.game_type == "single":
            if bid.session == "open" and bid.open_digit == open_digit:
                win = True
            if bid.session == "close" and bid.close_digit == close_digit:
                win = True

        if bid.game_type == "jodi":
            if bid.open_digit + bid.close_digit == open_digit + close_digit:
                win = True

        if win:
            rate = chart.jodi_digit_2 if bid.game_type == "jodi" else chart.single_digit_2
            amount = bid.points * rate

            wallet = Wallet.objects(user_id=bid.user_id).first()
            if wallet:
                wallet.update(inc__balance=amount)

                Transaction(
                    tx_id=str(uuid.uuid4()),
                    user_id=bid.user_id,
                    amount=amount,
                    payment_method="Win",
                    status="Approved"
                ).save()


# -----------------------------
# RESULT LIST
# -----------------------------

@router.get("/results")
def get_results(date: str, admin=Depends(require_admin)):
    results = ResultGod.objects(date=date)
    output = []

    for r in results:
        market = MarketGod.objects(id=r.market_id).first()

        output.append({
            "_id": str(r.id),
            "market_id": r.market_id,
            "game_name": market.name if market else "-",
            "date": r.date,
            "open_digit": r.open_digit,
            "close_digit": r.close_digit,
            "open_time": market.open_time if market else "-",
            "close_time": market.close_time if market else "-"
        })

    return {"data": output}


# -----------------------------
# FIND RESULT (FOR GO BUTTON)
# -----------------------------

@router.get("/result/find")
def find_result(date: str, game_id: str, session: str, admin=Depends(require_admin)):
    r = ResultGod.objects(market_id=game_id, date=date).first()

    if not r:
        return {"data": None}

    if session == "open":
        return {"data": {"open_digit": r.open_digit}}

    if session == "close":
        return {"data": {"close_digit": r.close_digit}}

    raise HTTPException(400, "Invalid session")


# -----------------------------
# DELETE RESULT
# -----------------------------

@router.delete("/result/{result_id}")
def delete_result(result_id: str, admin=Depends(require_admin)):
    r = ResultGod.objects(id=result_id).first()
    if not r:
        raise HTTPException(404, "Result not found")

    r.delete()
    return {"message": "Result deleted"}


# -----------------------------
# WINNING REPORT
# -----------------------------

@router.get("/winning-report", dependencies=[Depends(require_admin)])
def winning_report(
    date: str = Query(...),
    market_id: str = None
):
    target_date = datetime.strptime(date, "%Y-%m-%d")

    query = {"date__gte": target_date, "date__lte": target_date}
    if market_id:
        query["market_id"] = market_id

    results = ResultGod.objects(**query)

    if not results:
        return {"message": "No results found"}

    chart = RateChartGod.objects().first()
    if not chart:
        raise HTTPException(400, "Rate chart missing")

    reports = []

    for res in results:
        bids = BidGod.objects(market_id=res.market_id)

        for bid in bids:
            win = False

            if bid.game_type == "single":
                if bid.session == "open" and bid.open_digit == res.open_digit:
                    win = True
                if bid.session == "close" and bid.close_digit == res.close_digit:
                    win = True

            if bid.game_type == "jodi":
                if bid.open_digit + bid.close_digit == res.open_digit + res.close_digit:
                    win = True

            if win:
                amount = (chart.jodi_digit_2 if bid.game_type == "jodi" else chart.single_digit_2) * bid.points

                reports.append({
                    "user_id": bid.user_id,
                    "market_id": bid.market_id,
                    "game_type": bid.game_type,
                    "session": bid.session,
                    "open_digit": bid.open_digit,
                    "close_digit": bid.close_digit,
                    "points": bid.points,
                    "win_amount": amount
                })

    return {"count": len(reports), "data": reports}


