from fastapi import APIRouter, Depends, HTTPException, Form
from datetime import datetime
import uuid

from ..models import Wallet, Transaction
from ..auth import get_current_user, require_admin

router = APIRouter(prefix="/user", tags=["Wallet"])


def get_or_create_wallet(user_id: str):
    wallet = Wallet.objects(user_id=user_id).first()
    if not wallet:
        wallet = Wallet(user_id=user_id, balance=0)
        wallet.save()
    return wallet


@router.post("/add-money", )
def create_payment_request(
    amount: float = Form(...),
    payment_method: str = Form(...),
    user=Depends(get_current_user)
):
    if amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    tx = Transaction(
        tx_id=str(uuid.uuid4()),
        user_id=str(user.id),
        amount=amount,
        payment_method=payment_method,
        status="PENDING"
    ).save()

    return {
        "message": "Payment request created. Wait for admin approval.",
        "transaction_id": tx.tx_id,
        "status": tx.status
    }


@router.get("/balance", )
def get_wallet_info(user=Depends(get_current_user)):
    wallet = get_or_create_wallet(str(user.id))
    return {
        "user_id": str(user.id),
        "balance": wallet.balance,
        "updated_at": wallet.updated_at
    }


@router.get("/transactions", )
def my_transactions(user=Depends(get_current_user)):
    tr = Transaction.objects(user_id=str(user.id)).order_by("-created_at")
    return [
        {
            "tx_id": t.tx_id,
            "amount": t.amount,
            "method": t.payment_method,
            "status": t.status,
            "created_at": t.created_at
        } for t in tr
    ]


@router.get("/admin/pending", dependencies=[Depends(require_admin)], )
def admin_pending_transactions():
    pending = Transaction.objects(status="PENDING").order_by("-created_at")
    return [
        {
            "tx_id": t.tx_id,
            "user_id": t.user_id,
            "amount": t.amount,
            "method": t.payment_method,
            "created_at": t.created_at
        } for t in pending
    ]



@router.post("/admin/approve", dependencies=[Depends(require_admin)], )
def approve_transaction(tx_id: str = Form(...)):
    tx = Transaction.objects(tx_id=tx_id).first()

    if not tx:
        raise HTTPException(404, "Transaction not found")

    if tx.status != "PENDING":
        return {"message": "Already processed"}

    wallet = get_or_create_wallet(tx.user_id)
    wallet.balance += tx.amount
    wallet.updated_at = datetime.utcnow()
    wallet.save()

    tx.status = "SUCCESS"
    tx.confirmed_at = datetime.utcnow()
    tx.save()

    return {"message": "Transaction Approved", "new_balance": wallet.balance}


@router.post("/admin/reject", dependencies=[Depends(require_admin)], )
def reject_transaction(tx_id: str = Form(...)):
    tx = Transaction.objects(tx_id=tx_id).first()

    if not tx:
        raise HTTPException(404, "Transaction not found")

    tx.status = "FAILED"
    tx.confirmed_at = datetime.utcnow()
    tx.save()

    return {"message": "Transaction Rejected"}
