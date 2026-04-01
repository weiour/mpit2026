from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.wishlist import Wishlist
from app.schemas.wishlist import WishlistCreate, WishlistOut, WishlistUpdate

router = APIRouter()


@router.post("/events/{event_id}/wishlist", response_model=WishlistOut)
def create_wishlist_item(
    event_id: int,
    item: WishlistCreate,
    db: Session = Depends(get_db)
):
    db_item = Wishlist(**item.model_dump(), event_id=event_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.get("/events/{event_id}/wishlist", response_model=list[WishlistOut])
def get_wishlist_items(event_id: int, db: Session = Depends(get_db)):
    items = db.query(Wishlist).filter(Wishlist.event_id == event_id).all()
    return items


@router.put("/wishlist/{item_id}", response_model=WishlistOut)
def update_wishlist_item(
    item_id: int,
    item_update: WishlistUpdate,
    db: Session = Depends(get_db)
):
    db_item = db.query(Wishlist).filter(Wishlist.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    
    update_data = item_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/wishlist/{item_id}")
def delete_wishlist_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Wishlist).filter(Wishlist.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    
    db.delete(db_item)
    db.commit()
    return {"message": "Wishlist item deleted successfully"}
