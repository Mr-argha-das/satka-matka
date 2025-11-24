from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import FileResponse
from datetime import datetime
import os
import uuid

from ...auth import get_current_user, require_admin
from ...models import DepositQR, Transaction, Wallet, User, Withdrawal

router = APIRouter(prefix="/user-deposit-withdrawal", tags=["Deposit Withdrawal"])

UPLOAD_DIR = "uploads/deposit_qr"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_qr(trnx: str = None , image: UploadFile = File(...), user=Depends(get_current_user)):

    # only img allowed
    if not image.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        raise HTTPException(400, "Only PNG/JPG images allowed")

    # Create new filename
    filename = f"{uuid.uuid4()}.jpg"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # Save file
    with open(file_path, "wb") as f:
        f.write(await image.read())

    # 🔥 Always create a NEW QR request entry
    qr = DepositQR(
        trnx_id= trnx,
        user_id=str(user.id),
        image_url=file_path,
        status="PENDING",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    ).save()

    return {
        "message": "QR uploaded successfully",
        "image_url": file_path,
        "id": str(qr.id)
    }


@router.get("/image/{user_id}")
def get_qr_image(user_id: str):

    qr = DepositQR.objects(user_id=user_id).first()
    if not qr:
        raise HTTPException(404, "Image not found")

    return FileResponse(qr.image_url)


# -------------------------------------------------------
# 3️⃣ ADMIN: Get ALL Pending Requests (with username)
# -------------------------------------------------------
@router.get("/pending", dependencies=[Depends(require_admin)])
def get_pending_list():

    pending = DepositQR.objects().order_by("-created_at")
    data = []

    for p in pending:
        user = User.objects(id=p.user_id).first()
        data.append({
            "id": str(p.id),
            "user_id": p.user_id,
            "username": user.username if user else "Unknown",
            "image_url": p.image_url,
            "uploaded_at": p.created_at,
            "trxn_id": p.trnx_id
        })

    return {"count": len(data), "pending": data}


@router.post("/approve", dependencies=[Depends(require_admin)])
def approve_deposit(
    request_id: str = Form(...),
    amount: float = Form(...)
):

    qr = DepositQR.objects(id=request_id).first()
    if not qr:
        raise HTTPException(404, "Request not found")

    if qr.status != "PENDING":
        raise HTTPException(400, "Already processed")

    # Update wallet
    wallet = Wallet.objects(user_id=qr.user_id).first()
    wallet.update(inc__balance=amount)

    qr.status = "SUCCESS"
    qr.amount = amount
    qr.updated_at = datetime.utcnow()
    qr.save()
    tx = Transaction(
        tx_id=str(uuid.uuid4()),
        user_id=str(qr.user_id),
        amount=amount,
        payment_method="Deposit",
        status="Approved"
    ).save()

    return {"message": "Deposit Approved", "amount_added": amount}

# -------------------------------------------------------
# 5️⃣ ADMIN: Reject Deposit
# -------------------------------------------------------
@router.post("/reject", dependencies=[Depends(require_admin)])
def reject_deposit(request_id: str = Form(...)):

    qr = DepositQR.objects(id=request_id).first()
    if not qr:
        raise HTTPException(404, "Request not found")

    qr.status = "FAILED"
    qr.updated_at = datetime.utcnow()
    qr.save()
    tx = Transaction(
        tx_id=str(uuid.uuid4()),
        user_id=str(qr.user_id),
        amount=0,
        payment_method="Deposit",
        status="Rejected"
    ).save()

    return {"message": "Deposit request rejected"}


@router.get("/history")
def get_deposit_history(
    status: str | None = None,
    user=Depends(get_current_user)
):

    query = {"user_id": str(user.id)}
    if status:
        query["status"] = status.upper()

    history = DepositQR.objects(**query).order_by("-created_at")

    data = []
    for h in history:
        data.append({
            "id": str(h.id),
            "image_url": h.image_url,
            "status": h.status,
            "amount": getattr(h, "amount", None),
            "uploaded_at": h.created_at,
            "updated_at": h.updated_at
        })

    return {
        "count": len(data),
        "history": data
    }

def get_or_create_wallet(user_id: str):
    wallet = Wallet.objects(user_id=user_id).first()
    if not wallet:
        wallet = Wallet(user_id=user_id, balance=0)
        wallet.save()
    return wallet



@router.post("/request")
def request_withdraw(
    amount: float = Form(...),
    method: str = Form(...),
    number: str = Form(...),
    
):
    wallet = get_or_create_wallet(str(user.id))

    if amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    if wallet.balance < amount:
        raise HTTPException(400, "Insufficient balance")

    wd = Withdrawal(
        user_id=str(user.id),
        amount=amount,
        method=method,
        number=number
    ).save()

    return {
        "message": "Withdrawal request submitted",
        "withdrawal_id": wd.wd_id,
        "status": wd.status
    }




@router.get("/my")
def my_withdrawals(user=Depends(get_current_user)):
    data = Withdrawal.objects(user_id=str(user.id)).order_by("-created_at")
    return [
        {
            "wd_id": w.wd_id,
            "amount": w.amount,
            "method": w.method,
            "number": w.number,
            "status": w.status,
            "created_at": w.created_at
        }
        for w in data
    ]




@router.get("/admin/pending", )
def admin_pending():
    pending = Withdrawal.objects().order_by("-created_at")
    return [
        {
            "wd_id": w.wd_id,
            "user_id": w.user_id,
            "amount": w.amount,
            "method": w.method,
            "number": w.number,
            "created_at": w.created_at
        }
        for w in pending
    ]




@router.post("/admin/approve", )
def approve_withdraw(wd_id: str = Form(...)):
    wd = Withdrawal.objects(wd_id=wd_id).first()

    if not wd:
        raise HTTPException(404, "Withdrawal request not found")

    if wd.status != "PENDING":
        return {"message": "Already processed"}

    wallet = get_or_create_wallet(wd.user_id)

    if wallet.balance < wd.amount:
        raise HTTPException(400, "User wallet balance insufficient")

    # Deduct Money
    wallet.balance -= wd.amount
    wallet.updated_at = datetime.utcnow()
    wallet.save()

    wd.status = "SUCCESS"
    wd.confirmed_at = datetime.utcnow()
    wd.save()
    tx = Transaction(
        tx_id=str(uuid.uuid4()),
        user_id=str(wd.user_id),
        amount=-wd.amount,
        payment_method="Withdrawal",
        status="Approved"
    ).save()

    return {"message": "Withdrawal Approved", "new_balance": wallet.balance}




@router.post("/admin/reject", )
def reject_withdraw(wd_id: str = Form(...)):
    wd = Withdrawal.objects(wd_id=wd_id).first()

    if not wd:
        raise HTTPException(404, "Withdrawal not found")

    wd.status = "FAILED"
    wd.confirmed_at = datetime.utcnow()
    wd.save()
    tx = Transaction(
        tx_id=str(uuid.uuid4()),
        user_id=str(wd.user_id),
        amount=-wd.amount,
        payment_method="Withdrawal",
        status="Rejected"
    ).save()

    return {"message": "Withdrawal Rejected"}
