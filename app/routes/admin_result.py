from fastapi import APIRouter,Depends
from ..models import Market
from ..models import Result
from ..auth import get_current_user, require_admin

from ..models import Bid
from ..models import Result
from ..models import Wallet
GAME_RATES = {
    "single": 9,
    "jodi": 95,
    "single_panna": 140,
    "double_panna": 300,
    "triple_panna": 600,
    "sp": 900,
    "dp": 2700,
    "tp": 9000,
    "half_sangam": 1200,
    "full_sangam": 10000,
}
def settle_results(market_id):
    market = Result.objects.filter(market_id=market_id).first()

    open_digit = market.open_digit
    close_digit = market.close_digit
    open_panna = market.open_panna
    close_panna = market.close_panna

    bids = Bid.objects(market_id=market_id)

    for bid in bids:
        win = False

        if bid.game_type == "single" and bid.digit == open_digit:
            win = True

        if bid.game_type == "jodi" and bid.digit == open_digit + close_digit:
            win = True

        if bid.game_type == "single_panna" and bid.digit == open_panna:
            win = True

        if bid.game_type == "double_panna" and bid.digit == close_panna:
            win = True

        if win:
            rate = GAME_RATES.get(bid.game_type)
            win_amount = bid.points * rate

            wallet = Wallet.objects(user_id=bid.user_id).first()
            wallet.update(inc__balance=win_amount)



router = APIRouter(prefix="/admin/result")

@router.post("/declare")
def declare(market_id: str, open_result: str = None, close_result: str = None, user=Depends(require_admin)):

    market = Market.objects.get(id=market_id)
    
    if open_result:
        market.update(open_result=open_result)

    if close_result:
        market.update(close_result=close_result)

    settle_results(market_id)   # AUTO SETTLEMENT

    return {"msg": "Result updated"}
