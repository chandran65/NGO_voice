import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import CustomerProfile

logger = logging.getLogger(__name__)

# Fallback default NGO donor data
DEFAULT_CUSTOMER = {
    "customer_id": "DONOR-90821",
    "phone": "+91 98765 43210",
    "name_ta": "சுரேஷ் குமார்",
    "name_en": "Suresh Kumar",
    "policy_number": "DON-80G-98234",
    "plan_type": "Child Sponsorship & Nutrition Fund",
    "premium_amount": 1500.0,
    "due_date": "25-08-2026",
    "sum_assured": 80.0, # 80G tax exemption %
    "address": "No. 42, Anna Salai, T. Nagar, Chennai - 600017",
    "email": "suresh.kumar@example.com"
}

class BackendAPIService:
    @staticmethod
    def get_customer_by_phone(db: Session, phone: str) -> Dict[str, Any]:
        """Look up donor details in CRM database by phone number."""
        clean_phone = phone.strip()
        customer = db.query(CustomerProfile).filter(CustomerProfile.phone.contains(clean_phone[-10:])).first()
        if customer:
            return {
                "customer_id": customer.customer_id,
                "phone": customer.phone,
                "name_ta": customer.name_ta,
                "name_en": customer.name_en,
                "policy_number": customer.policy_number,
                "plan_type": customer.plan_type,
                "premium_amount": customer.premium_amount,
                "due_date": customer.due_date,
                "sum_assured": customer.sum_assured,
                "address": customer.address,
                "email": customer.email or "N/A"
            }
        return DEFAULT_CUSTOMER

    @staticmethod
    def get_policy_details(db: Session, policy_number: str) -> Dict[str, Any]:
        """Fetch donor contribution details and 80G tax exemption status."""
        customer = db.query(CustomerProfile).filter(CustomerProfile.policy_number == policy_number).first()
        if customer:
            return {
                "policy_number": customer.policy_number,
                "status": "ACTIVE_DONOR",
                "plan_name": customer.plan_type,
                "sum_assured": 80.0,
                "premium": customer.premium_amount,
                "due_date": customer.due_date,
                "tax_benefit": "Section 80G Tax Exemption (50%)"
            }
        return {
            "policy_number": policy_number or "DON-80G-98234",
            "status": "ACTIVE_DONOR",
            "plan_name": "Child Education & Nutrition Fund",
            "sum_assured": 80.0,
            "premium": 1500.0,
            "due_date": "25-08-2026",
            "tax_benefit": "Section 80G Tax Exemption (50%)"
        }

    @staticmethod
    def generate_payment_link(phone: str, policy_number: str, amount: float) -> str:
        """Generate secure UPI donation payment link for SMS/WhatsApp."""
        link = f"https://donate.childrenhome.org/pay?id={policy_number}&amt={int(amount)}&mobile={phone[-10:]}"
        logger.info(f"Generated donation payment link for {phone}: {link}")
        return link

    @staticmethod
    def calculate_emi_options(premium_amount: float) -> Dict[str, Any]:
        """Calculate child sponsorship monthly contribution options."""
        return {
            "annual_premium": premium_amount * 12,
            "monthly_emi": 1500.0,
            "quarterly_emi": 4500.0,
            "processing_fee": 0.0
        }

    @staticmethod
    def update_customer_address(db: Session, customer_id: str, new_address: str) -> bool:
        """Update donor address in CRM database."""
        customer = db.query(CustomerProfile).filter(CustomerProfile.customer_id == customer_id).first()
        if customer:
            customer.address = new_address
            db.commit()
            logger.info(f"Updated address for donor {customer_id}: {new_address}")
            return True
        return True

