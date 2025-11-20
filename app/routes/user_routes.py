from fastapi import APIRouter, Depends, HTTPException, Form
from datetime import datetime
import uuid
from ..models import Wallet, Transaction
from ..auth import get_current_user

router = APIRouter(prefix="/user")


def get_or_create_wallet(uid):
    w = Wallet.objects(user_id=uid).first()
    if not w:
        w = Wallet(user_id=uid, balance=0).save()
    return w


@router.post("/add-money")
def add_money(amount: float = Form(...), payment_method: str = Form(...), user=Depends(get_current_user)):
    if amount <= 0:
        raise HTTPException(400, "Invalid amount")

    tx = Transaction(
        tx_id=str(uuid.uuid4()),
        user_id=str(user.id),
        amount=amount,
        payment_method=payment_method,
        status="PENDING"
    ).save()

    return {"message": "Payment request created", "transaction_id": tx.tx_id}


@router.get("/balance")
def balance(user=Depends(get_current_user)):
    w = get_or_create_wallet(str(user.id))
    return {"balance": w.balance}


@router.get("/transactions")
def transactions(user=Depends(get_current_user)):
    tr = Transaction.objects(user_id=str(user.id)).order_by("-created_at")
    return [{
        "tx_id": t.tx_id,
        "amount": t.amount,
        "method": t.payment_method,
        "status": t.status,
        "created_at": t.created_at
    } for t in tr]


@router.get("/winning_history")
def winning_history(user=Depends(get_current_user)):
    wins = Transaction.objects(
        user_id=str(user.id),
        payment_method="WIN",
        status="SUCCESS"
    ).order_by("-created_at")

    return {
        "success": True,
        "winning_count": wins.count(),
        "wins": [{
            "tx_id": w.tx_id,
            "amount": w.amount,
            "date": w.created_at
        } for w in wins]
    }
