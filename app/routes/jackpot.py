# ================================
#     STARLINE + JACKPOT APIs
# ================================
import json
from pydantic import BaseModel # You need this import
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from ..models import (
    StarlineSlot, JackpotSlot,
    Bid, Result, Wallet
)
from bson import ObjectId

from ..auth import get_current_user, require_admin

router = APIRouter(prefix="/starline_jackpot", tags=["Starline & Jackpot"])

ALLOWED_GAMES = ["single_digit", "single_panna", "double_panna", "triple_panna"]

GAME_RATES = {
    "single_digit": 9,
    "single_panna": 140,
    "double_panna": 300,
    "triple_panna": 600,
}


# ======================================================
#              HELPER FUNCTIONS
# ======================================================

def validate_digit(game, digit):
    if game == "single_digit":
        if not digit.isdigit() or len(digit) != 1:
            raise HTTPException(400, "Digit must be 1 number")

    if game in ["single_panna", "double_panna", "triple_panna"]:
        if not digit.isdigit() or len(digit) != 3:
            raise HTTPException(400, "Panna must be 3 digits")


def settle(slot_id, panna):
    digit = panna[-1]  # last digit

    bids = Bid.objects(market_id=slot_id)

    for b in bids:
        win = False

        if b.game_type == "single_digit" and b.digit == digit:
            win = True

        if b.game_type in ["single_panna", "double_panna", "triple_panna"]:
            if b.digit == panna:
                win = True

        if win:
            amount = b.points * GAME_RATES[b.game_type]
            Wallet.objects(user_id=b.user_id).update(inc__balance=amount)


# ======================================================
#            🟣 STARLINE APIs
# ======================================================

# 1. Define the Pydantic model for the request body (JSON)
class StarlineSlotRequest(BaseModel):
    name: str
    start_time: str
    end_time: str


# ⭐ Add Slot
@router.post("/starline/add")
# 💡 FIX: Accept the request data as a single Pydantic model (which reads the JSON body)
def starline_add(slot_data: StarlineSlotRequest):

    # Access data using dot notation (slot_data.name)
    slot = StarlineSlot(
        name=slot_data.name,
        start_time=slot_data.start_time,
        end_time=slot_data.end_time,
        games=ALLOWED_GAMES
    ).save()

    return {"msg": "Starline Slot Added", "slot_id": str(slot.id)}



# ⭐ Get Slot List
@router.get("/starline/list")
def starline_list():
    return [{
        "id": str(s.id),
        "name": s.name,
        "start_time": s.start_time,
        "end_time": s.end_time,
        "games": s.games
    } for s in StarlineSlot.objects]


# ⭐ Get Slot By ID
@router.get("/starline/{slot_id}")
def get_starline_by_id(slot_id: str):
    slot = StarlineSlot.objects(id=slot_id).first()

    if not slot:
        raise HTTPException(404, "Slot not found")

    return {
        "id": str(slot.id),
        "name": slot.name,
        "start_time": slot.start_time,
        "end_time": slot.end_time,
        "games": slot.games
    }


# ⭐ Place Bid
@router.post("/starline/bid")
def starline_bid(slot_id: str, game_type: str, digit: str, points: int, user=Depends(get_current_user)):

    if game_type not in ALLOWED_GAMES:
        raise HTTPException(400, "Invalid Game Type")

    validate_digit(game_type, digit)

    slot = StarlineSlot.objects(id=slot_id).first()
    if not slot:
        raise HTTPException(404, "Slot Not Found")

    wallet = Wallet.objects(user_id=str(user.id)).first()
    if wallet.balance < points:
        raise HTTPException(400, "Insufficient Balance")

    wallet.update(dec__balance=points)

    bid = Bid(
        user_id=str(user.id),
        market_id=slot_id,
        game_type=game_type,
        session="starline",
        digit=digit,
        points=points
    ).save()

    return {"msg": "Bid Placed", "bid_id": str(bid.id)}


# ⭐ Bid History
@router.get("/starline/bid/history")
def starline_bid_history(user=Depends(get_current_user)):
    bids = Bid.objects(user_id=str(user.id), session="starline").order_by("-created_at")

    return [{
        "bid_id": str(b.id),
        "slot_id": b.market_id,
        "game": b.game_type,
        "digit": b.digit,
        "points": b.points,
        "time": b.created_at
    } for b in bids]


# ⭐ Declare Result
@router.post("/starline/result/declare")
def starline_result(slot_id: str, panna: str, ):

    now = datetime.utcnow().strftime("%Y-%m-%d")

    Result(
        market_id=slot_id,
        date=now,
        open_digit=panna[-1],
        close_digit=panna[-1],
        open_panna=panna,
        close_panna=panna,
    ).save()

    settle(slot_id, panna)

    return {"msg": "Starline Result Declared"}


# ⭐ Get Result
@router.get("/starline/result/get")
def starline_result_get(slot_id: str):

    result = Result.objects(market_id=slot_id).order_by("-date").first()

    if not result:
        return {"msg": "No Result"}

    return {
        "date": result.date,
        "panna": result.open_panna,
        "digit": result.open_digit
    }


# ======================================================
#            🟣 JACKPOT APIs
# ======================================================

# ⭐ Add Slot
@router.post("/jackpot/add")
def jackpot_add(name: str, start_time: str, end_time: str,
                ):

    slot = JackpotSlot(
        name=name,
        start_time=start_time,
        end_time=end_time,
        games=ALLOWED_GAMES
    ).save()

    return {"msg": "Jackpot Slot Added", "slot_id": str(slot.id)}


# ⭐ Get Slot List
@router.get("/jackpot/list")
def jackpot_list():
    return [{
        "id": str(s.id),
        "name": s.name,
        "start_time": s.start_time,
        "end_time": s.end_time,
        "games": s.games
    } for s in JackpotSlot.objects]


# ⭐ Place Bid
@router.post("/jackpot/bid")
def jackpot_bid(slot_id: str, game_type: str, digit: str, points: int,
                user=Depends(get_current_user)):

    if game_type not in ALLOWED_GAMES:
        raise HTTPException(400, "Invalid Game Type")

    validate_digit(game_type, digit)

    slot = JackpotSlot.objects(id=slot_id).first()
    if not slot:
        raise HTTPException(404, "Slot Not Found")

    wallet = Wallet.objects(user_id=str(user.id)).first()
    if wallet.balance < points:
        raise HTTPException(400, "Insufficient Balance")

    wallet.update(dec__balance=points)

    bid = Bid(
        user_id=str(user.id),
        market_id=slot_id,
        game_type=game_type,
        session="jackpot",
        digit=digit,
        points=points
    ).save()

    return {"msg": "Bid Placed", "bid_id": str(bid.id)}


# ⭐ Bid History
@router.get("/jackpot/bid/history")
def jackpot_bid_history(user=Depends(get_current_user)):

    bids = Bid.objects(user_id=str(user.id), session="jackpot").order_by("-created_at")

    return [{
        "bid_id": str(b.id),
        "slot_id": b.market_id,
        "game": b.game_type,
        "digit": b.digit,
        "points": b.points,
        "time": b.created_at
    } for b in bids]


# ⭐ Declare Result
@router.post("/jackpot/result/declare")
def jackpot_result(slot_id: str, panna: str, ):

    now = datetime.utcnow().strftime("%Y-%m-%d")

    Result(
        market_id=slot_id,
        date=now,
        open_digit=panna[-1],
        close_digit=panna[-1],
        open_panna=panna,
        close_panna=panna,
    ).save()

    settle(slot_id, panna)

    return {"msg": "Jackpot Result Declared"}


# ⭐ Get Result
@router.get("/jackpot/result/get")
def jackpot_result_get(slot_id: str):

    result = Result.objects(market_id=slot_id).order_by("-date").first()

    if not result:
        return {"msg": "No Result"}

    return {
        "date": result.date,
        "panna": result.open_panna,
        "digit": result.open_digit
    }
