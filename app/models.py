from mongoengine import Document, StringField, EmailField, DateTimeField, FloatField, IntField, ReferenceField, BooleanField, ListField, EmbeddedDocumentField, EmbeddedDocument
import datetime

class User(Document):
    meta = {"collection": "users"}
    username = StringField(required=True)
    mobile = StringField(required=True, unique=True)
    email = EmailField()
    password_hash = StringField(required=True)
    role = StringField(choices=["player","admin"], default="player")
    balance = FloatField(default=0.0)
    created_at = DateTimeField(default=datetime.datetime.utcnow)

class Transaction(Document):
    meta = {"collection":"transactions"}
    user = ReferenceField(User, required=True)
    kind = StringField(choices=["deposit","withdraw","bet","win","refund"], required=True)
    amount = FloatField(required=True)
    balance_after = FloatField(required=True)
    meta_info = StringField()
    created_at = DateTimeField(default=datetime.datetime.utcnow)

class Bet(Document):
    meta = {"collection":"bets", "indexes": [{"fields":["-created_at"]}]}
    user = ReferenceField(User, required=True)
    market = StringField(required=True)  # e.g., 'open','close','single','jodi'
    number = StringField(required=True)  # the bet number (e.g., '123' or '7')
    stake = FloatField(required=True)
    odds = FloatField(default=1.0)  # multiplier for win
    status = StringField(choices=["open","settled","cancelled"], default="open")
    result = StringField(choices=["win","lose","pending"], default="pending")
    payout = FloatField(default=0.0)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    settled_at = DateTimeField()

class Draw(Document):
    meta = {"collection":"draws", "indexes":[{"fields":["-created_at"]}]}
    market = StringField(required=True)  # 'open' or 'close' or custom
    result_number = StringField(required=True)  # result of draw
    published_by = ReferenceField(User)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    settled = BooleanField(default=False)
