from fastapi import APIRouter, Depends
from ..auth import get_current_user
from ..models import Transaction, Withdrawal, Bid, DepositQR

router = APIRouter(prefix="/passbook", tags=["Passbook"])


@router.get("/history")
def passbook_history(user=Depends(get_current_user)):
    user_id = str(user.id)

    entries = []

    # -----------------------------
    # 1️⃣  DEPOSITS (from Transaction)
    # -----------------------------
    deposits = Transaction.objects(
        user_id=user_id,
        payment_method="DEPOSIT"
    )

    for d in deposits:
        entries.append({
            "type": "DEPOSIT",
            "amount": d.amount,
            "status": d.status,
            "tx_id": d.tx_id,
            "created_at": d.created_at
        })

    # -----------------------------
    # 2️⃣  WINS (Transaction WIN)
    # -----------------------------
    wins = Transaction.objects(
        user_id=user_id,
        payment_method="WIN"
    )

    for w in wins:
        entries.append({
            "type": "WIN",
            "amount": w.amount,
            "status": w.status,
            "tx_id": w.tx_id,
            "created_at": w.created_at
        })

    # -----------------------------
    # 3️⃣  WITHDRAWALS
    # -----------------------------
    withdrawals = Withdrawal.objects(user_id=user_id)

    for w in withdrawals:
        entries.append({
            "type": "WITHDRAWAL",
            "amount": w.amount,
            "method": w.method,
            "status": w.status,
            "created_at": w.created_at
        })

    # -----------------------------
    # 4️⃣  BIDS (wallet deduction)
    # -----------------------------
    bids = Bid.objects(user_id=user_id)

    for b in bids:
        entries.append({
            "type": "BID",
            "game_type": b.game_type,
            "market_id": b.market_id,
            "session": b.session,
            "digit": b.digit,
            "debit": b.points,
            "created_at": b.created_at
        })

    # -----------------------------
    # 5️⃣  DEPOSIT QR SCREENSHOTS
    # -----------------------------
    qr = DepositQR.objects(user_id=user_id)

    for q in qr:
        entries.append({
            "type": "QR_DEPOSIT",
            "image_url": q.image_url,
            "amount": q.amount,
            "status": q.status,
            "created_at": q.created_at
        })

    # -----------------------------
    # 🔥 SORT BY DATE (Latest first)
    # -----------------------------
    entries = sorted(entries, key=lambda x: x["created_at"], reverse=True)

    return {
        "success": True,
        "count": len(entries),
        "history": entries
    }
