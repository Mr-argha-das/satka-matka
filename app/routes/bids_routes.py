from fastapi import APIRouter, HTTPException,Depends
from ..models import Bid
from ..models import Wallet
from ..models import Market
from ..auth import get_current_user

router = APIRouter(prefix="/bid")

@router.post("/place")
def place_bid(market_id: str, game_type: str,
              session: str, digit: str, points: int, user=Depends(get_current_user)):

    wallet = Wallet.objects(user_id=user.id).first()
    if wallet.balance < points:
        raise HTTPException(400, "Insufficient Balance")

    wallet.update(dec__balance=points)

    bid = Bid(
        user_id=user.id,
        market_id=market_id,
        game_type=game_type,
        session=session,
        digit=digit,
        points=points
    )
    bid.save()

    return {"msg": "Bid Successfully Placed", "bid": bid}
@router.get("/my-bids")
def my_bids(user=Depends(get_current_user)):
    bids = Bid.objects(user_id=user.id).order_by("-created_at").limit(100)
    return bids
@router.get("/market-bids")
def market_bids(market_id: str, user=Depends(get_current_user)):
    bids = Bid.objects(market_id=market_id).order_by("-created_at")
    return bids
