import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database import engine, Base, SessionLocal
from app.models import Campaign, CustomerProfile, AgentEscalation, CallSessionModel, CallTurnModel, QueryLog, SupervisorCallback

def seed_database():
    print("Initializing SQLite Database Tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Campaign
        existing_campaign = db.query(Campaign).first()
        if not existing_campaign:
            c = Campaign(
                name="Q3 Renewal & Policy Assistance Campaign (Tamil)",
                description="Automated Tamil outbound calls for upcoming policy renewal dues, EMI assistance, and policy enquiries.",
                status="ACTIVE",
                total_customers=5,
                completed_calls=3,
                escalated_calls=1
            )
            db.add(c)
            print("Seeded Outbound Campaign record.")

        # 2. Seed Customer Profiles
        existing_cust = db.query(CustomerProfile).first()
        if not existing_cust:
            customers = [
                CustomerProfile(
                    customer_id="CUST-90821",
                    phone="+91 98765 43210",
                    name_ta="சுரேஷ் குமார்",
                    name_en="Suresh Kumar",
                    policy_number="POL-98234-TA",
                    plan_type="ABC Jeevan Suraksha Health & Life Plan",
                    premium_amount=4500.0,
                    due_date="25-08-2026",
                    sum_assured=500000.0,
                    address="No. 42, Anna Salai, T. Nagar, Chennai - 600017",
                    email="suresh.kumar@example.com"
                ),
                CustomerProfile(
                    customer_id="CUST-90822",
                    phone="+91 98765 43211",
                    name_ta="பிரியா ராமச்சந்திரன்",
                    name_en="Priya Ramachandran",
                    policy_number="POL-77124-TA",
                    plan_type="ABC Family Health Kavach",
                    premium_amount=6200.0,
                    due_date="28-08-2026",
                    sum_assured=1000000.0,
                    address="Door 12, MG Road, Coimbatore - 641001",
                    email="priya.r@example.com"
                ),
                CustomerProfile(
                    customer_id="CUST-90823",
                    phone="+91 98765 43212",
                    name_ta="கார்த்திக் சுப்ரமணியம்",
                    name_en="Karthik Subramaniam",
                    policy_number="POL-55412-TA",
                    plan_type="ABC Senior Citizen Suraksha",
                    premium_amount=3800.0,
                    due_date="30-08-2026",
                    sum_assured=300000.0,
                    address="Plot 5, KK Nagar, Madurai - 625020",
                    email="karthik.s@example.com"
                ),
                CustomerProfile(
                    customer_id="CUST-90824",
                    phone="+91 98765 43213",
                    name_ta="லக்ஷ்மி நாராயணன்",
                    name_en="Lakshmi Narayanan",
                    policy_number="POL-33901-TA",
                    plan_type="ABC Smart Term Life Insurance",
                    premium_amount=8500.0,
                    due_date="05-09-2026",
                    sum_assured=2500000.0,
                    address="Flat 4A, Gandhi Nagar, Trichy - 620006",
                    email="lakshmi.n@example.com"
                )
            ]
            db.add_all(customers)
            print("Seeded Customer Profile records.")

        # 3. Seed Sample Human Escalation Ticket
        existing_esc = db.query(AgentEscalation).first()
        if not existing_esc:
            esc = AgentEscalation(
                session_id="CALL-DEMO-01",
                customer_id="CUST-90821",
                customer_name="சுரேஷ் குமார்",
                phone="+91 98765 43210",
                policy_number="POL-98234-TA",
                intent="COMPLAINT",
                confidence_score=0.45,
                conversation_summary="Customer Query: 'என் கணக்கில் இருமுறை பிரீமியம் பணம் பிடிக்கப்பட்டுவிட்டது'. Identified Intent: COMPLAINT (Conf: 0.45). Escalation Reason: Customer grievance/complaint detected.",
                responses_provided="வணக்கம் Suresh! ABC Insurance... | உங்கள் புகாரை நாங்கள் தீவிரமாக எடுத்துக்கொள்கிறோம். உங்கள் அழைப்பை மேலதிகாரியிடம் மாற்றுகிறேன்.",
                escalation_reason="Customer grievance regarding duplicate premium debit.",
                status="PENDING"
            )
            db.add(esc)
            print("Seeded Sample Agent Escalation Ticket.")

        db.commit()
        print("Database Seeding Completed Successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
