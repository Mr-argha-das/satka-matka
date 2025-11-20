from fastapi import APIRouter, HTTPException, Depends
import datetime
from ..models import Bid, Wallet, Market
from ..auth import get_current_user, require_admin

router = APIRouter(prefix="/bid")

VALID_GAMES = [
    "single","jodi","single_panna","double_panna","triple_panna",
    "sp","dp","tp","half_sangam","full_sangam"
]


@router.post("/place")
def place_bid(market_id: str, game_type: str,
              session: str, digit: str, points: int,
              user=Depends(get_current_user)):

    # Wallet Check
    wallet = Wallet.objects(user_id=str(user.id)).first()
    if not wallet:
        raise HTTPException(400, "Wallet not found")

    if wallet.balance < points:
        raise HTTPException(400, "Insufficient Balance")

    # Market Check
    market = Market.objects(id=market_id).first()
    if not market:
        raise HTTPException(404, "Invalid Market ID")

    # Validate Game Type
    if game_type not in VALID_GAMES:
        raise HTTPException(400, "Invalid Game Type")

    # Validate Session
    if session not in ["open", "close"]:
        raise HTTPException(400, "Invalid Session")

    # Deduct points
    wallet.update(
        dec__balance=points,
        set__updated_at=datetime.datetime.utcnow()
    )

    # Save Bid
    bid = Bid(
        user_id=str(user.id),
        market_id=market_id,
        game_type=game_type,
        session=session,
        digit=digit,
        points=points
    ).save()

    return {
        "msg": "Bid Successfully Placed",
        "bid": {
            "id": str(bid.id),
            "market_id": bid.market_id,
            "game_type": bid.game_type,
            "session": bid.session,
            "digit": bid.digit,
            "points": bid.points,
            "created_at": bid.created_at
        }
    }


@router.get("/my-bids")
def my_bids(user=Depends(get_current_user)):
    bids = Bid.objects(user_id=str(user.id)).order_by("-created_at").limit(100)
    return [{
        "id": str(b.id),
        "market_id": b.market_id,
        "game_type": b.game_type,
        "session": b.session,
        "digit": b.digit,
        "points": b.points,
        "created_at": b.created_at
    } for b in bids]


@router.get("/market-bids")
def market_bids(market_id: str, admin=Depends(require_admin)):
    bids = Bid.objects(market_id=market_id).order_by("-created_at")
    return [{
        "id": str(b.id),
        "user_id": b.user_id,
        "game_type": b.game_type,
        "digit": b.digit,
        "points": b.points,
        "session": b.session,
        "created_at": b.created_at
    } for b in bids]
