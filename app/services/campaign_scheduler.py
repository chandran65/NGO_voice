import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import Campaign, CustomerProfile

logger = logging.getLogger(__name__)

class CampaignScheduler:
    @staticmethod
    def get_active_campaigns(db: Session) -> List[Campaign]:
        """Fetch list of campaigns from DB."""
        campaigns = db.query(Campaign).order_by(Campaign.created_at.desc()).all()
        if not campaigns:
            # Seed initial insurance outbound campaign
            c = Campaign(
                name="Q3 Renewal & Policy Assistance Campaign (Tamil)",
                description="Automated Tamil outbound calls for upcoming policy renewal dues, EMI assistance, and policy enquiries.",
                status="ACTIVE",
                total_customers=5,
                completed_calls=0,
                escalated_calls=0
            )
            db.add(c)
            db.commit()
            db.refresh(c)
            return [c]
        return campaigns

    @staticmethod
    def get_campaign_customers(db: Session, campaign_id: int) -> List[CustomerProfile]:
        """Fetch customer roster for an outbound campaign."""
        customers = db.query(CustomerProfile).limit(10).all()
        return customers
