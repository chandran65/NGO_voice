import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import engine, Base, SessionLocal
from app.models import Campaign, CustomerProfile, AgentEscalation, CallSessionModel, CallTurnModel, QueryLog, SupervisorCallback

def seed_database(db_session=None):
    print("Initializing SQLite Database Tables for NGO Fundraising Platform...")
    Base.metadata.create_all(bind=engine)
    db = db_session or SessionLocal()

    try:
        # Clear old mock data
        db.query(Campaign).delete()
        db.query(CustomerProfile).delete()
        db.query(AgentEscalation).delete()
        db.commit()

        # 1. Seed Campaign
        c = Campaign(
            name="NGO Outbound Donor Support & 80G Tax Renewal Campaign (Tamil)",
            description="Automated Tamil outbound calls for donor renewals, child sponsorship, 80G tax exemption certificates, and donation payment links.",
            status="ACTIVE",
            total_customers=4,
            completed_calls=3,
            escalated_calls=1
        )
        db.add(c)
        db.commit()
        db.refresh(c)
        print("Seeded NGO Outbound Campaign record.")

        # 2. Seed Customer Profiles (Donors)
        customers = [
            CustomerProfile(
                customer_id="DONOR-90821",
                phone="+91 98765 43210",
                name_ta="சுரேஷ் குமார்",
                name_en="Suresh Kumar",
                policy_number="DON-80G-98234",
                plan_type="Child Education & Nutrition Sponsor Plan",
                premium_amount=1500.0,
                due_date="25-08-2026",
                sum_assured=80.0, # 80G Tax exemption %
                address="No. 42, Anna Salai, T. Nagar, Chennai - 600017",
                email="suresh.kumar@example.com"
            ),
            CustomerProfile(
                customer_id="DONOR-90822",
                phone="+91 98765 43211",
                name_ta="பிரியா ராமச்சந்திரன்",
                name_en="Priya Ramachandran",
                policy_number="DON-80G-77124",
                plan_type="Elder Shelter Care & Medical Support Fund",
                premium_amount=3000.0,
                due_date="28-08-2026",
                sum_assured=80.0,
                address="Door 12, MG Road, Coimbatore - 641001",
                email="priya.r@example.com"
            ),
            CustomerProfile(
                customer_id="DONOR-90823",
                phone="+91 98765 43212",
                name_ta="கார்த்திக் சுப்ரமணியம்",
                name_en="Karthik Subramaniam",
                policy_number="DON-80G-55412",
                plan_type="Monthly Child Sponsorship Fund",
                premium_amount=1500.0,
                due_date="30-08-2026",
                sum_assured=80.0,
                address="Plot 5, KK Nagar, Madurai - 625020",
                email="karthik.s@example.com"
            ),
            CustomerProfile(
                customer_id="DONOR-90824",
                phone="+91 98765 43213",
                name_ta="லக்ஷ்மி நாராயணன்",
                name_en="Lakshmi Narayanan",
                policy_number="DON-80G-33901",
                plan_type="Orphanage Infrastructure & Food Support",
                premium_amount=5000.0,
                due_date="05-09-2026",
                sum_assured=80.0,
                address="Flat 4A, Gandhi Nagar, Trichy - 620006",
                email="lakshmi.n@example.com"
            )
        ]
        db.add_all(customers)
        print("Seeded Donor Profile records.")

        # 3. Seed Sample Human Escalation Ticket for Agent Console
        esc = AgentEscalation(
            session_id="CALL-DEMO-01",
            customer_id="DONOR-90821",
            customer_name="சுரேஷ் குமார்",
            phone="+91 98765 43210",
            policy_number="DON-80G-98234",
            intent="COMPLAINT",
            confidence_score=0.45,
            conversation_summary="Donor Query: 'என் 80G வரி விலக்கு சான்றிதழ் இன்னும் வாட்ஸ்அப்பில் வரவில்லை'. Identified Intent: COMPLAINT (Conf: 0.45). Escalation Reason: Donor grievance regarding 80G certificate delay.",
            responses_provided="வணக்கம் Suresh! எங்கள் குழந்தைகள் இல்ல அறக்கட்டளையிலிருந்து அழைக்கிறோம்... | உங்கள் கோரிக்கையை நாங்கள் தீவிரமாக எடுத்துக்கொள்கிறோம். உங்கள் அழைப்பை மேலதிகாரியிடம் மாற்றுகிறேன்.",
            escalation_reason="Donor grievance regarding 80G Tax Exemption Certificate delivery delay.",
            status="PENDING"
        )
        db.add(esc)
        print("Seeded Sample Human Agent Escalation Ticket.")

        db.commit()
        print("NGO Database Seeding Completed Successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

seed_ngo_database = seed_database

if __name__ == "__main__":
    seed_database()
