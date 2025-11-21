import json
from fastapi import APIRouter, HTTPException
from ..models import Market

router = APIRouter(prefix="/market")


@router.post("/create")
def create_market(name: str, open_time: str, close_time: str):

    if Market.objects(name=name).first():
        raise HTTPException(400, "Market already exists")

    m = Market(
        name=name,
        open_time=open_time,
        close_time=close_time
    )
    m.save()

    return {"msg": "Market created successfully", "market": m}

@router.put("/update/{market_id}")
def update_market(market_id: str, name: str = None, open_time: str = None, close_time: str = None):

    market = Market.objects(id=market_id).first()
    if not market:
        raise HTTPException(404, "Market not found")

    if name:
        market.name = name
    if open_time:
        market.open_time = open_time
    if close_time:
        market.close_time = close_time
    market.save()


    return {"msg": "Market updated", "market": market}
@router.delete("/delete/{market_id}")
def delete_market(market_id: str):
    market = Market.objects(id=market_id).first()
    if not market:
        raise HTTPException(404, "Market not found")

    market.delete()
    return {"msg": "Market deleted successfully"}

@router.get("/{market_id}")
def get_market(market_id: str):
    market = Market.objects(id=market_id).first()
    if not market:
        raise HTTPException(404, "Market not found")
    return json.loads(market.to_json())


@router.get("/")
def get_all_markets():
    return {
        "markets": json.loads(Market.objects.all().to_json()),
        "status": "success"
    }