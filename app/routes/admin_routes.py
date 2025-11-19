from fastapi import APIRouter, Depends, HTTPException
from ..schemas import DrawCreate
from ..auth import require_admin
from ..models import Draw, Bet, User, Transaction
import datetime

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/publish_draw")
def publish_draw(payload: DrawCreate, admin = Depends(require_admin)):
    d = Draw(market=payload.market, result_number=payload.result_number, published_by=admin).save()
    return {"id": str(d.id)}

@router.post("/settle_draw/{draw_id}")
def settle_draw(draw_id: str, admin = Depends(require_admin)):
    draw = Draw.objects(id=draw_id).first()
    if not draw:
        raise HTTPException(404, "Draw not found")
    if draw.settled:
        raise HTTPException(400, "Already settled")
    # fetch matching bets for market & number
    matching = Bet.objects(market=draw.market, status="open")
    wins = []
    loses = []
    for b in matching:
        # example rule: exact match -> win with payout = stake * 9 (example)
        if b.number == draw.result_number:
            b.update(set__status="settled", set__result="win", set__payout=b.stake * 9, set__settled_at=datetime.datetime.utcnow())
            # credit user
            user = b.user
            payout = b.stake * 9
            new_balance = user.balance + payout
            user.update(balance=new_balance)
            Transaction(user=user, kind="win", amount=payout, balance_after=new_balance, meta_info=f"Win for bet {b.id}").save()
            wins.append(str(b.id))
        else:
            b.update(set__status="settled", set__result="lose", set__payout=0.0, set__settled_at=datetime.datetime.utcnow())
            loses.append(str(b.id))

    draw.update(set__settled=True)
    return {"settled": True, "wins": wins, "loses_count": len(loses)}
