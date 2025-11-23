import json
from app.new_models import MarketGod, RateChartGod, BidGod, ResultGod

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form, Query
from fastapi.responses import FileResponse
from datetime import datetime, time
import os
import uuid
from mongoengine.errors import NotUniqueError
from ...auth import get_current_user, require_admin
from ...models import DepositQR, Transaction, Wallet, User

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

class RateChartGodInput(BaseModel):
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


router = APIRouter(prefix="/api/admin/Golidesawar", tags=["Golidesawar Game Management "])

@router.get("/rate/")
def get_rate_chart():
    chart = RateChartGod.objects().first()
    if not chart:
        return {"message": "No rate chart found"}
    return chart.to_mongo().to_dict()

@router.post("/rate/")
def create_or_update_rate_chart(data: RateChartGodInput,admin = Depends(require_admin)):
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


@router.post("/market/")
def create_market(data: MarketInput,admin = Depends(require_admin)):
    try:
        market = MarketGod(
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
    markets = MarketGod.objects()
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

@router.get("/market/{market_id}")
def get_market(market_id: str, admin=Depends(require_admin)):
    market = MarketGod.objects(id=market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    data = json.loads(market.to_json())

    # AUTO CALCULATE STATUS
    data["status"] = compute_status(market.open_time, market.close_time)

    # TODAY DATE RANGE
    today = datetime.utcnow().date()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)

    todays_result = ResultGod.objects(
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
    market = MarketGod.objects(id=market_id).first()
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
    market = MarketGod.objects(id=market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    market.status = status
    market.save()

    return {"message": "Market status updated", "status": status}



@router.delete("/market/{market_id}")
def delete_market(market_id: str,admin = Depends(require_admin)):
    market = MarketGod.objects(id=market_id).first()
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    market.delete()
    return {"message": "Market deleted successfully"}




class ResultDeclare(BaseModel):
    game_id: str
    date: str
    session: str  # open / close
    open_digit: str = None
    open_panna: str = None
    close_digit: str = None
    close_panna: str = None


# -----------------------------
# SETTLEMENT LOGIC
# -----------------------------
def settle_results(market_id: str, result_obj: ResultGod):

    # Load rate chart
    chart = RateChartGod.objects().first()
    if not chart:
        print("Rate chart not found!")
        return

    open_digit = result_obj.open_digit
    close_digit = result_obj.close_digit
    open_panna = result_obj.open_panna
    close_panna = result_obj.close_panna

    bids = BidGod.objects(market_id=market_id)

    # Rate chart mapping
    RATE_MAP = {
        "single": chart.single_digit_2,
        "jodi": chart.jodi_digit_2,
        "single_panna": chart.single_pana_2,
        "double_panna": chart.double_pana_2,
        "triple_panna": chart.tripple_pana_2,
        "half_sangam": chart.half_sangam_2,
        "full_sangam": chart.full_sangam_2,
    }

    for bid in bids:
        win = False

        # --------------------- WIN LOGIC ---------------------

        # SINGLE
        if bid.game_type == "single" and bid.digit == open_digit:
            win = True

        # JODI
        if bid.game_type == "jodi" and bid.digit == open_digit + close_digit:
            win = True

        # SINGLE PANNA
        if bid.game_type == "single_panna" and bid.digit == open_panna:
            win = True

        # DOUBLE PANNA
        if bid.game_type == "double_panna" and bid.digit == close_panna:
            win = True

        # TRIPLE PANNA
        if bid.game_type == "triple_panna":
            if bid.session == "open" and bid.digit == open_panna:
                win = True
            if bid.session == "close" and bid.digit == close_panna:
                win = True

        # HALF SANGAM – BOTH CASES SUPPORTED
        if bid.game_type == "half_sangam":
            panna, digitx = bid.digit.split("-")

            # Case 1 → open_panna + close_digit
            if panna == open_panna and digitx == close_digit:
                win = True

            # Case 2 → close_panna + open_digit
            if panna == close_panna and digitx == open_digit:
                win = True

        # FULL SANGAM
        if bid.game_type == "full_sangam":
            op, cp = bid.digit.split("-")
            if op == open_panna and cp == close_panna:
                win = True

        # --------------------- PAYOUT -------------------------
        if win:
            rate = RATE_MAP.get(bid.game_type, 0)
            amount = bid.points * rate

            wallet = Wallet.objects(user_id=bid.user_id).first()
            if wallet:
                wallet.update(inc__balance=amount)

                # Transaction log
                Transaction(
                    tx_id=str(uuid.uuid4()),
                    user_id=str(bid.user_id),
                    amount=amount,
                    payment_method="Win",
                    status="Approved"
                ).save()
@router.post("/result/declare")
def declare_result(payload: ResultDeclare, admin=Depends(require_admin)):
    session = payload.session.lower()

    market = MarketGod.objects(id=payload.game_id).first()
    if not market:
        raise HTTPException(404, "Market not found")

    # Find or create today's result entry
    result = ResultGod.objects(
        market_id=payload.game_id,
        date=payload.date
    ).first()

    if not result:
        result = ResultGod(
            market_id=payload.game_id,
            date=payload.date,
            open_digit="-",
            close_digit="-",
            open_panna="-",
            close_panna="-",
        )

    now = datetime.datetime.now()

    # OPEN SESSION
    if session == "open":
        if not payload.open_digit and not payload.open_panna:
            raise HTTPException(400, "Open digit or panna required")

        result.open_digit = payload.open_digit or result.open_digit
        result.open_panna = payload.open_panna or result.open_panna
        result.open_declared_at = now

    # CLOSE SESSION
    elif session == "close":
        if not payload.close_digit and not payload.close_panna:
            raise HTTPException(400, "Close digit or panna required")

        result.close_digit = payload.close_digit or result.close_digit
        result.close_panna = payload.close_panna or result.close_panna
        result.close_declared_at = now

    else:
        raise HTTPException(400, "Session must be open or close")

    result.save()

    # SETTLE WINNERS
    settle_results(payload.game_id, result)

    return {"message": "Result declared successfully"}




# -----------------------------
# GET RESULTS BY DATE
# -----------------------------
@router.get("/results")
def get_results(date: str, admin=Depends(require_admin)):
    results = ResultGod.objects(date=date)
    output = []

    for r in results:
        # fetch market name using the existing market schema
        market = MarketGod.objects(id=r.market_id).first()

        output.append({
            "_id": str(r.id),
            "market_id": r.market_id,
            "game_name": market.name if market else "-",
            "date": r.date,
            "open_panna": r.open_panna,
            "open_digit": r.open_digit,
            "close_panna": r.close_panna,
            "close_digit": r.close_digit,
            "open_declared_at": getattr(r, "open_declared_at", None),
            "close_declared_at": getattr(r, "close_declared_at", None),
            "close_timne": market.close_time if market else "-",
            "open_time": market.open_time if market else "-",
        })

    return {"data": output}



# -----------------------------
# GET RESULT FOR GO BUTTON
# -----------------------------
@router.get("/result/find")
def find_result(date: str, game_id: str, session: str, admin=Depends(require_admin)):
    session = session.lower()
    r = ResultGod.objects(market_id=game_id, date=date).first()

    if not r:
        return {"data": None}

    if session == "open":
        return {
            "data": {
                "open_panna": r.open_panna,
                "open_digit": r.open_digit
            }
        }

    elif session == "close":
        return {
            "data": {
                "close_panna": r.close_panna,
                "close_digit": r.close_digit
            }
        }

    else:
        raise HTTPException(400, "Invalid session")


@router.delete("/result/{result_id}")
def delete_result(result_id: str, admin=Depends(require_admin)):
    r = ResultGod.objects(id=result_id).first()
    if not r:
        raise HTTPException(404, "Result not found")

    r.delete()
    return {"message": "Result deleted"}



@router.get("/history", dependencies=[Depends(require_admin)])
def bid_history(
    user_id: str = None,
    market_id: str = None,
    session: str = None,
    game_type: str = None,
    date_from: str = None,
    date_to: str = None
):

    query = {}

    if user_id:
        query["user_id"] = user_id

    if market_id:
        query["market_id"] = market_id

    if session:
        query["session"] = session

    if game_type:
        query["game_type"] = game_type

    if date_from:
        query["created_at__gte"] = datetime.strptime(date_from, "%Y-%m-%d")

    if date_to:
        query["created_at__lte"] = datetime.strptime(date_to, "%Y-%m-%d")

    bids = BidGod.objects(**query).order_by("-created_at")

    result = []
    for b in bids:
        result.append({
            "id": str(b.id),
            "user_id": b.user_id,
            "market_id": b.market_id,
            "game_type": b.game_type,
            "session": b.session,
            "digit": b.digit,
            "points": b.points,
            "created_at": b.created_at
        })

    return {"count": len(result), "data": result}


@router.post("/edit", dependencies=[Depends(require_admin)])
def edit_bid(
    bid_id: str,
    digit: str = None,
    points: int = None,
    session: str = None,
    game_type: str = None
):
    bid = BidGod.objects(id=bid_id).first()

    if not bid:
        raise HTTPException(404, "Bid not found")

    if digit:
        bid.digit = digit

    if points:
        bid.points = points

    if session:
        bid.session = session

    if game_type:
        bid.game_type = game_type

    bid.save()

    return {"message": "Bid updated successfully"}
@router.delete("/delete/{bid_id}", dependencies=[Depends(require_admin)])
def delete_bid(bid_id: str):
    bid = BidGod.objects(id=bid_id).first()

    if not bid:
        raise HTTPException(404, "Bid not found")

    bid.delete()

    return {"message": "Bid deleted successfully"}
@router.get("/winning-report", dependencies=[Depends(require_admin)])
def winning_report(
    date: str = Query(..., description="Format: YYYY-MM-DD"),
    market_id: str = None
):
    day = datetime.strptime(date, "%Y-%m-%d")

    # Load Results
    query = {"date__gte": day, "date__lte": day}
    if market_id:
        query["market_id"] = market_id

    results = ResultGod.objects(**query)

    if not results:
        return {"message": "No results found"}

    chart = RateChartGod.objects().first()
    if not chart:
        raise HTTPException(400, "Rate chart not found")

    RATE = {
        "single": chart.single_digit_2,
        "jodi": chart.jodi_digit_2,
        "single_panna": chart.single_pana_2,
        "double_panna": chart.double_pana_2,
        "triple_panna": chart.tripple_pana_2,
        "half_sangam": chart.half_sangam_2,
        "full_sangam": chart.full_sangam_2,
    }

    report = []

    for res in results:
        bids = BidGod.objects(market_id=res.market_id)

        for bid in bids:
            win = False

            # --- APPLY WIN LOGIC ---
            if bid.game_type == "single" and bid.digit == res.open_digit:
                win = True

            if bid.game_type == "jodi" and bid.digit == res.open_digit + res.close_digit:
                win = True

            if bid.game_type == "single_panna" and bid.digit == res.open_panna:
                win = True

            if bid.game_type == "double_panna" and bid.digit == res.close_panna:
                win = True

            if bid.game_type == "triple_panna":
                if bid.session == "open" and bid.digit == res.open_panna:
                    win = True
                if bid.session == "close" and bid.digit == res.close_panna:
                    win = True

            if bid.game_type == "half_sangam":
                panna, dg = bid.digit.split("-")
                if panna == res.open_panna and dg == res.close_digit:
                    win = True

            if bid.game_type == "full_sangam":
                op, cp = bid.digit.split("-")
                if op == res.open_panna and cp == res.close_panna:
                    win = True

            # ----- WIN CALC -----
            if win:
                amount = bid.points * RATE[bid.game_type]

                report.append({
                    "user_id": bid.user_id,
                    "market_id": bid.market_id,
                    "game_type": bid.game_type,
                    "session": bid.session,
                    "digit": bid.digit,
                    "points": bid.points,
                    "win_amount": amount,
                })

    return {"count": len(report), "data": report}
