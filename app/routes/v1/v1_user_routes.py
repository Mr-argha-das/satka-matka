import json
from app.utils import hash_password, verify_password
from ...models import User, Transaction,Withdrawal,Bid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends,Form
from pydantic import BaseModel
from ...auth import require_admin
router = APIRouter(prefix="/api/v1/admin", tags=["Admin user management"])

@router.get("/users")
def all_users(user=Depends(require_admin)):
    users = User.objects().order_by("-created_at")
    return {
        "message": "Users fetched successfully",
        "count": len(users),
        "users": json.loads(users.to_json())
    }

class StatusUpdate(BaseModel):
    status: bool

@router.put("/users/{user_id}/status")
def update_status(user_id: str, payload: StatusUpdate, user=Depends(require_admin)):
    user = User.objects(id=user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    user.update(status=payload.status)
    return {"message": "Status updated successfully"}

class BetUpdate(BaseModel):
    is_bet: bool

@router.put("/users/{user_id}/is-bet")
def update_is_bet(user_id: str, payload: BetUpdate,user=Depends(require_admin)):
    user = User.objects(id=user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    user.update(is_bet=payload.is_bet)
    return {"message": "Bet Permission updated successfully"}


# Unapproved Users
@router.get("/users/status/disapprove")
def inactive_users(user=Depends(require_admin)):
    users = User.objects(status=False)
    return {
        "message": "Inactive users fetched successfully",
        "count": len(users),
        "users": json.loads(users.to_json())    
    }

# Approved Users
@router.get("/users/status/approve")
def active_users(user=Depends(require_admin)):
    users = User.objects(status=True)
    return {
        "message": "Active users fetched successfully",
        "count": len(users),
        "users": json.loads(users.to_json())
    }
from datetime import datetime


# Login Today Users
@router.get("/users/today-logins")
def todays_logins(user=Depends(require_admin)):
    today = datetime.utcnow().date()

    users = User.objects(last_login__gte=datetime.combine(today, datetime.min.time()),
                         last_login__lte=datetime.combine(today, datetime.max.time()))

    return {
        "message": "Today's logins fetched successfully",
        "count": len(users),
        "users": json.loads(users.to_json())
    }

@router.get("/user/add-money")
def add_money(amount: float, user_id: str, user=Depends(require_admin)):
    user = User.objects(id=user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    if amount <= 0:
        raise HTTPException(400, "Invalid amount")

    user.update(inc__balance=amount)
    return {"message": f"Added {amount} to user {user.username} successfully"}

@router.get("/user/witdrawal-money")
def deduct_money(amount: float, user_id: str, user=Depends(require_admin)):
    user = User.objects(id=user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    if amount <= 0:
        raise HTTPException(400, "Invalid amount")

    if user.balance < amount:
        raise HTTPException(400, "Insufficient balance")

    user.update(inc__balance=-amount)

    return {"message": f"Deducted {amount} from user {user.username} successfully"}



@router.post("/user/update-password")
def update_password(
    user_id: str = Form(...),
    user=Depends(require_admin),
    new_password: str = Form(...),
    
):
    user = User.objects(id=user_id).first()
    new_hash = hash_password(new_password)
    user.update(password_hash=new_hash)

    return {"message": "Password updated successfully"}



@router.get("/user/user-details/{user_id}")
def user_details(user_id: str, use2r=Depends(require_admin)):
    user = User.objects(id=user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    total = Transaction.objects(user_id=str(user_id), status="Approved",payment_method="Deposit").sum("amount") or 0.0
    total2 = Withdrawal.objects(user_id=str(user_id), status="SUCCESS").sum("amount") or 0.0
    bids = Bid.objects(user_id=str(user.id)).order_by("-created_at").limit(100)
    query = {
        "user_id": str(user.id),
        "payment_method": "WIN",
        "status": "SUCCESS"
    }
    wins = Transaction.objects(**query).order_by("-created_at")
    return {
        "data": {
            "@user":json.loads(user.to_json()),
            "@total_deposit": total,
            "@total_withdrawal": total2,
            "@user_bids": json.loads(bids.to_json()),
            "@wins": json.loads(wins.to_json())
        }
    }


# Today Registered Users
@router.get("/users/today-created")
def today_created_users(admin_user = Depends(require_admin)):
    today = datetime.utcnow().date()

    users = User.objects(
        created_at__gte=datetime.combine(today, datetime.min.time()),
        created_at__lte=datetime.combine(today, datetime.max.time())
    )

    return {
        "message": "Today's created users fetched successfully",
        "count": len(users),
        "users": json.loads(users.to_json())
    }