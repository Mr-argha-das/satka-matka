from mongoengine import Document, StringField, EmailField, DateTimeField, FloatField, IntField, ReferenceField, BooleanField, ListField, EmbeddedDocumentField, EmbeddedDocument
import datetime
import uuid
class User(Document):
    meta = {"collection": "users"}

    username = StringField(required=True)
    mobile = StringField(required=True, unique=True)
   
    password_hash = StringField(required=True)
    role = StringField(choices=["player","admin"], default="player")
    balance = FloatField(default=0.0)
    created_at = DateTimeField(default=datetime.datetime.utcnow)




class Draw(Document):
    meta = {"collection":"draws", "indexes":[{"fields":["-created_at"]}]}
    market = StringField(required=True)  # 'open' or 'close' or custom
    result_number = StringField(required=True)  # result of draw
    published_by = ReferenceField(User)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    settled = BooleanField(default=False)

class Transaction(Document):
    tx_id = StringField(required=True, unique=True)
    user_id = StringField(required=True)
    amount = FloatField(required=True)
    payment_method = StringField(required=True)
    status = StringField(default="PENDING")  # PENDING, SUCCESS, FAILED
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    confirmed_at = DateTimeField()
    screenshot = StringField()


class Wallet(Document):
    user_id = StringField(required=True, unique=True)
    balance = FloatField(default=0)
    updated_at =DateTimeField(default=datetime.datetime.utcnow)


class Withdrawal(Document):
    wd_id = StringField(default=lambda: str(uuid.uuid4()))
    user_id = StringField(required=True)
    amount = FloatField(required=True)
    method = StringField(required=True)  # Paytm / PhonePe / GooglePay
    number = StringField(required=True)

    status = StringField(default="PENDING")  # PENDING / SUCCESS / FAILED
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    confirmed_at = DateTimeField()

class Market(Document):
    name = StringField(required=True, unique=True)
    open_time = StringField(required=True)
    close_time = StringField(required=True)
    
    open_result = StringField(default="-")
    close_result = StringField(default="-")
    
    is_active = BooleanField(default=True)

class Bid(Document):
    user_id = StringField(required=True)
    market_id = StringField(required=True)

    game_type = StringField(required=True)  # single, jodi, sp, dp, tp, panna, sangam
    session = StringField(required=True)    # open / close

    digit = StringField(required=True)
    points = IntField(required=True)

    created_at = DateTimeField(default=datetime.datetime.utcnow)


class Result(Document):
    market_id = StringField(required=True)
    date = StringField(required=True)

    open_panna = StringField(default="-")
    close_panna = StringField(default="-")
    open_digit = StringField(default="-")
    close_digit = StringField(default="-")

class DepositQR(Document):
    user_id = StringField(required=True)
    image_url = StringField(required=True)
    status = StringField(default="PENDING")  # PENDING, SUCCESS, FAILED
    amount = FloatField(default=0)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)


class StarlineSlot(Document):
    meta = {"collection": "starline_slots"}

    name = StringField(required=True)                # e.g., "Slot 1"
    start_time = StringField(required=True)          # "10:00"
    end_time = StringField(required=True)            # "10:15" (admin decides)
    games = ListField(StringField())                 # Allowed games
    is_active = BooleanField(default=True)


class JackpotSlot(Document):
    meta = {"collection": "jackpot_slots"}

    name = StringField(required=True)
    start_time = StringField(required=True)
    end_time = StringField(required=True)
    games = ListField(StringField())
    is_active = BooleanField(default=True)
