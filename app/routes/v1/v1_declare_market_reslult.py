from app.auth import require_admin
from app.models import Bid, Market, Result
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
# from ..auth import require_admin
import datetime

router = APIRouter(prefix="/api/admin", tags=["Market Result Management"])


# -----------------------------
# GAME RATES
# -----------------------------
GAME_RATES = {
    "single": 9,
    "jodi": 95,
    "single_panna": 140,
    "double_panna": 300,
    "triple_panna": 600,
    "half_sangam": 1200,
    "full_sangam": 10000,
}


# -----------------------------
# INPUT MODEL
# -----------------------------
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
def settle_results(market_id: str, result_obj: Result):
    open_digit = result_obj.open_digit
    close_digit = result_obj.close_digit
    open_panna = result_obj.open_panna
    close_panna = result_obj.close_panna

    bids = Bid.objects(market_id=market_id)
    for bid in bids:
        win = False

        # Single digit
        if bid.game_type == "single" and bid.digit == open_digit:
            win = True

        # Jodi
        if bid.game_type == "jodi" and bid.digit == open_digit + close_digit:
            win = True

        # Open Panna
        if bid.game_type == "single_panna" and bid.digit == open_panna:
            win = True

        # Close Panna
        if bid.game_type == "double_panna" and bid.digit == close_panna:
            win = True

        # Triple panna open/close
        if bid.game_type == "triple_panna":
            if bid.session == "open" and bid.digit == open_panna:
                win = True
            if bid.session == "close" and bid.digit == close_panna:
                win = True

        # Half Sangam
        if bid.game_type == "half_sangam":
            panna, digit = bid.digit.split("-")
            if panna == open_panna and digit == close_digit:
                win = True

        # Full Sangam
        if bid.game_type == "full_sangam":
            op, cp = bid.digit.split("-")
            if op == open_panna and cp == close_panna:
                win = True

        # Credit winnings
        if win:
            rate = GAME_RATES.get(bid.game_type, 0)
            amount = bid.points * rate
            wallet = Wallet.objects(user_id=bid.user_id).first()
            if wallet:
                wallet.update(inc__balance=amount)


# -----------------------------
# DECLARE RESULT
# -----------------------------
@router.post("/result/declare")
def declare_result(payload: ResultDeclare, admin=Depends(require_admin)):
    session = payload.session.lower()

    market = Market.objects(id=payload.game_id).first()
    if not market:
        raise HTTPException(404, "Market not found")

    # Find or create
    result = Result.objects(market_id=payload.game_id, date=payload.date).first()
    if not result:
        result = Result(
            market_id=payload.game_id,
            date=payload.date,
            open_digit="-",
            close_digit="-",
            open_panna="-",
            close_panna="-",
        )

    now = datetime.datetime.now()

    # Apply session logic
    if session == "open":
        if not payload.open_digit and not payload.open_panna:
            raise HTTPException(400, "Open digit or panna required")
        result.open_digit = payload.open_digit or result.open_digit
        result.open_panna = payload.open_panna or result.open_panna
        result.open_declared_at = now

    elif session == "close":
        if not payload.close_digit and not payload.close_panna:
            raise HTTPException(400, "Close digit or panna required")
        result.close_digit = payload.close_digit or result.close_digit
        result.close_panna = payload.close_panna or result.close_panna
        result.close_declared_at = now

    else:
        raise HTTPException(400, "Session must be open or close")

    result.save()
    settle_results(payload.game_id, result)

    return {"message": "Result declared successfully"}


# -----------------------------
# GET RESULTS BY DATE
# -----------------------------
@router.get("/results")
def get_results(date: str, admin=Depends(require_admin)):
    results = Result.objects(date=date)
    output = []

    for r in results:
        # fetch market name using the existing market schema
        market = Market.objects(id=r.market_id).first()

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
        })

    return {"data": output}



# -----------------------------
# GET RESULT FOR GO BUTTON
# -----------------------------
@router.get("/result/find")
def find_result(date: str, game_id: str, session: str, admin=Depends(require_admin)):
    session = session.lower()
    r = Result.objects(market_id=game_id, date=date).first()

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
    r = Result.objects(id=result_id).first()
    if not r:
        raise HTTPException(404, "Result not found")

    r.delete()
    return {"message": "Result deleted"}
