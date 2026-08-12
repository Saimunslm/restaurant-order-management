from datetime import datetime
from app.extensions import db
from app.models.special_offer import SpecialOffer


def create_offer(product_id, offer_price, start_date, end_date):
    existing = SpecialOffer.query.filter_by(product_id=product_id).first()
    if existing:
        existing.offer_price = offer_price
        existing.start_date = start_date
        existing.end_date = end_date
        existing.is_active = True
        db.session.commit()
        return existing

    offer = SpecialOffer(
        product_id=product_id,
        offer_price=offer_price,
        start_date=start_date,
        end_date=end_date,
    )
    db.session.add(offer)
    db.session.commit()
    return offer


def deactivate_offer(offer_id):
    offer = SpecialOffer.query.get_or_404(offer_id)
    offer.is_active = False
    db.session.commit()
    return offer


def get_active_offers():
    now = datetime.utcnow()
    return SpecialOffer.query.filter(
        SpecialOffer.is_active == True,
        SpecialOffer.start_date <= now,
        SpecialOffer.end_date >= now,
    ).all()


def check_and_expire_offers():
    now = datetime.utcnow()
    expired = SpecialOffer.query.filter(
        SpecialOffer.is_active == True,
        SpecialOffer.end_date < now,
    ).all()
    for offer in expired:
        offer.is_active = False
    db.session.commit()
    return len(expired)
