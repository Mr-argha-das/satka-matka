


from random import random
import string
from ...models import Wallet, Transaction
from pydantic import BaseModel
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form

router = APIRouter(prefix="/user-deposit-deeplink", tags=["Auto Pay UPI"])

class CreatePaymentRequest(BaseModel):
    user_id: str
    amount: float


class SMSWebhookRequest(BaseModel):
    sms: str
    ref_no: str
    amount: float

def generate_txn_id():
    return "TXN" + ''.join(random.choices(string.digits, k=8))


def get_or_create_wallet(user_id):
    wallet = Wallet.objects(user_id=user_id).first()
    if wallet:
        return wallet
    return Wallet(user_id=user_id, balance=0).save()

@router.post("/payment/create")
def create_payment(req: CreatePaymentRequest):
    txn_id = generate_txn_id()

    # Save pending transaction
    Transaction(
        txn_id=txn_id,
        user_id=req.user_id,
        amount=req.amount,
        status="pending"
    ).save()

    upi_link = f"upi://pay?pa=hdml61i74205@hdfcbank&pn=Abhay Prakash Koli&am={req.amount}&cu=INR&tn=Paying to Kalyan Ratan 777&tr={txn_id}"
    

    return {
        "status": "pending",
        "txn_id": txn_id,
        "upi_link": upi_link
    }



@router.post("/payment/sms-webhook")
def sms_webhook(req: SMSWebhookRequest):
    print("Received SMS webhook:", req.to_dict())
    utr = req.ref_no

    # Find pending transaction with same amount (best guess match)
    txn = Transaction.objects(amount=req.amount, status="pending").first()

    if not txn:
        return {"error": "Transaction not found"}

    # Mark transaction success
    txn.status = "success"
    txn.utr = utr
    txn.save()

    # Add money to wallet
    wallet = get_or_create_wallet(txn.user_id)
    wallet.balance += txn.amount
    wallet.updated_at = datetime.utcnow()
    wallet.save()

    return {
        "status": "success",
        "message": "Wallet credited",
        "txn_id": txn.txn_id,
        "utr": utr,
        "new_balance": wallet.balance
    }

@router.get("/wallet/{user_id}")
def get_wallet(user_id: str):
    wallet = get_or_create_wallet(user_id)
    return {
        "user_id": wallet.user_id,
        "balance": wallet.balance
    }