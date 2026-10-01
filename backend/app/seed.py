import datetime as dt, hashlib
from .models import *
def hp(p): return hashlib.pbkdf2_hmac("sha256", p.encode(), b"agentos", 100000).hex()
L = [("Ahmed Khan","Khan Logistics","Website","Hi, I'm interested in your enterprise plan. Can someone explain the pricing? I'd like to start this week."),
("Sarah Ali","Ali & Co","Referral","We need a demo today if possible - our team is ready to buy before month end."),
("Usman Malik","Malik Traders","WhatsApp","Please send enterprise pricing. Urgent, our board meets tomorrow and we want to purchase."),
("Fatima Noor","Noor Boutique","Instagram","How much does the starter plan cost?"),
("Bilal Ahmed","Ahmed Textiles","Email","Your dashboard shows an error when I export reports. This is not working since yesterday."),
("Hina Raza","","Website","Just browsing, maybe later in the year."),
("Omar Farooq","Farooq Foods","Existing customer","We're on Pro and want to upgrade to the team plan, ready to start this week."),
("Zainab Shah","","Facebook","hello"),
("Imran Qureshi","Qureshi Clinics","Phone","Can your system integrate with our appointment software and support Urdu messages?"),
("Ayesha Siddiqui","Siddiqui Realty","Website","Following up on last week's call - please send the proposal, we can sign up today."),
("Hamza Tariq","Tariq Auto","Event","Met your team at the expo. Not sure yet, just curious about what you offer in general terms."),
("Mariam Yusuf","Yusuf Pharma","LinkedIn","Cold intro from your campaign. No budget right now, maybe later.")]
def seed(s):
    if s.query(User).count(): return
    s.add(User(email="demo@agentos.ai", password_hash=hp("AgentOS-Demo-2026"), role="admin"))
    for i, (n, c, src, m) in enumerate(L):
        s.add(Lead(id=f"L-{i+1:03d}", name=n, email=n.lower().replace(" ", ".") + "@example.com", phone=f"+92 300 {1000000+i*7919:07d}",
            company=c, source=src, message=m, conversation_history=[{"from": "lead", "text": m}], status="New",
            created_at=dt.datetime.utcnow() - dt.timedelta(hours=i), last_contact=dt.datetime.utcnow() - dt.timedelta(days=i % 5)))
    s.commit()
