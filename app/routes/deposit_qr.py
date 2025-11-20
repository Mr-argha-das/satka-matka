from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import FileResponse
from datetime import datetime
import os
import uuid

from ..auth import get_current_user, require_admin
from ..models import DepositQR, Wallet, User

router = APIRouter(prefix="/deposit-qr", tags=["Deposit With QR"])

UPLOAD_DIR = "uploads/deposit_qr"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# -------------------------------------------------------
# 1️⃣ USER: Upload or Replace QR Image
# -------------------------------------------------------
@router.post("/upload")
async def upload_qr(image: UploadFile = File(...), user=Depends(get_current_user)):

    # only img allowed
    if not image.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        raise HTTPException(400, "Only PNG/JPG images allowed")

    # Create new filename
    filename = f"{uuid.uuid4()}.jpg"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # Save file
    with open(file_path, "wb") as f:
        f.write(await image.read())

    old = DepositQR.objects(user_id=str(user.id)).first()

    # If exists → delete old image file
    if old:
        try:
            os.remove(old.image_url)
        except:
            pass

        old.image_url = file_path
        old.status = "PENDING"
        old.updated_at = datetime.utcnow()
        old.save()

        return {"message": "QR updated successfully", "image_url": file_path}

    # First time upload
    qr = DepositQR(
        user_id=str(user.id),
        image_url=file_path,
        status="PENDING"
    ).save()

    return {"message": "QR uploaded successfully", "image_url": file_path}


# -------------------------------------------------------
# 2️⃣ PUBLIC: Get QR image by user ID
# -------------------------------------------------------
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

    pending = DepositQR.objects(status="PENDING").order_by("-created_at")
    data = []

    for p in pending:
        user = User.objects(id=p.user_id).first()
        data.append({
            "id": str(p.id),
            "user_id": p.user_id,
            "username": user.full_name if user else "Unknown",
            "image_url": p.image_url,
            "uploaded_at": p.created_at
        })

    return {"count": len(data), "pending": data}


# -------------------------------------------------------
# 4️⃣ ADMIN: Approve Deposit (adds money to wallet)
# -------------------------------------------------------
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

    return {"message": "Deposit request rejected"}
