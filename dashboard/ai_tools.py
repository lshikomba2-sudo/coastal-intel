import streamlit as st
import sqlite3
import json
import urllib.request
import urllib.error

DB_PATH = "database/properties.db"

GROQ_API_KEY = "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"
GROQ_MODEL = "llama-3.3-70b-versatile"

def call_ai(prompt, system):
    try:
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", 
            "install", "groq", "-q"])
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        chat = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.3
        )
        return chat.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def get_airbnb_avg(area):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "SELECT AVG(price_per_night) FROM airbnb_listings WHERE area=?",
            (area,)
        )
        result = c.fetchone()[0]
        conn.close()
        return int(result or 1000)
    except:
        return 1000

def render_ai_tools():
    st.markdown("""
        <div style='background:#0F6E56;padding:1.25rem;
        border-radius:12px;margin-bottom:1rem'>
        <h2 style='color:white;margin:0;font-size:1.3rem'>
        Exokino AI Deal Engine</h2>
        <p style='color:#9FE1CB;margin:.4rem 0 0 0;font-size:.85rem'>
        Powered by Groq Llama 3 — find, analyse and close deals faster 
        than any agency in Namibia</p></div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "🏦 Bank Feasibility",
        "📈 Rental Arbitrage",
        "🎯 Distressed Scout"
    ])

    with tab1:
        st.subheader("Bank Feasibility Report")
        col1, col2 = st.columns(2)
        with col1:
            price = st.number_input("Property price (N$)",
                min_value=500000, max_value=20000000,
                value=2500000, step=50000)
            area = st.selectbox("Area",
                ["Langstrand","Swakopmund","Walvis Bay",
                 "Henties Bay","Windhoek"])
            units = st.number_input("Number of units",
                min_value=1, max_value=20, value=1)
        with col2:
            nightly = st.number_input("Airbnb nightly rate (N$)",
                min_value=400, max_value=5000,
                value=get_airbnb_avg(area), step=50)
            occ = st.slider("Expected occupancy %", 30, 90, 65)

        deposit = price * 0.25
        loan = price * 0.75
        r = (0.115 + 0.015) / 12
        n = 15 * 12
        repayment = loan * (r * (1+r)**n) / ((1+r)**n - 1)
        gross = nightly * (occ/100) * 30 * units
        noi = gross * (1 - 0.15 - 0.10 - 0.20)
        dscr = noi / repayment

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Deposit (25%)", f"N${deposit:,.0f}")
        c2.metric("Monthly Repayment", f"N${repayment:,.0f}")
        c3.metric("Net Operating Income", f"N${noi:,.0f}")
        c4.metric("DSCR", f"{dscr:.2f}")

        if dscr >= 1.25:
            st.success("✅ APPROVED FOR BANK PITCH — DSCR above 1.25")
        else:
            st.error("❌ REJECTED BY BANK CRITERIA — DSCR below 1.25")

        if st.button("Generate Full AI Report", type="primary",
                     key="bank_btn"):
            with st.spinner("Analysing deal with AI..."):
                prompt = f"""
Property: {area}, Namibia
Purchase Price: N${price:,}
Units: {units}
Nightly Rate: N${nightly}
Occupancy: {occ}%
Deposit: N${deposit:,.0f}
Loan: N${loan:,.0f}
Monthly Repayment: N${repayment:,.0f}
Gross Monthly Revenue: N${gross:,.0f}
Net Operating Income: N${noi:,.0f}
DSCR: {dscr:.2f}
Decision: {"APPROVED" if dscr >= 1.25 else "REJECTED"}

Write a professional 1-page bank feasibility report for this 
Namibian property investment. Include deal strengths, risks, 
and a recommended negotiation strategy. Be specific to the 
Namibian coastal property market.
"""
                system = """You are a senior commercial real estate 
underwriter specializing in the Namibian property market. Write 
clear, professional reports that would satisfy a Namibian bank's 
credit committee."""
                result = call_ai(prompt, system)
                st.markdown(result)

    with tab2:
        st.subheader("Rental Arbitrage Analyser")
        col1, col2 = st.columns(2)
        with col1:
            arb_area = st.selectbox("Area",
                ["Langstrand","Swakopmund","Walvis Bay","Henties Bay"],
                key="arb_area")
            monthly_rent = st.number_input("Monthly rent (N$)",
                min_value=3000, max_value=30000,
                value=8000, step=500)
        with col2:
            arb_rate = st.number_input("Airbnb nightly rate (N$)",
                min_value=400, max_value=3000,
                value=get_airbnb_avg(arb_area), step=50,
                key="arb_rate")
            prop_desc = st.text_area("Property description",
                placeholder="3 bed apartment, sea view...",
                height=80)

        airbnb_rev = arb_rate * 0.50 * 30
        margin = airbnb_rev - monthly_rent - 1500
        score = min(100, max(0, int((margin / monthly_rent) * 100)))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Airbnb Revenue (50%)", f"N${airbnb_rev:,.0f}/mo")
        c2.metric("Rent Cost", f"N${monthly_rent:,}/mo")
        c3.metric("Net Margin", f"N${margin:,.0f}/mo",
            delta="Positive" if margin > 0 else "Negative")
        c4.metric("Arbitrage Score", f"{score}/100")

        if st.button("Generate Landlord Pitch", type="primary",
                     key="arb_btn"):
            with st.spinner("Generating pitch script..."):
                prompt = f"""
Location: {arb_area}, Namibia
Monthly Rent: N${monthly_rent:,}
Airbnb Nightly Rate: N${arb_rate}
Airbnb Monthly Revenue (50% occ): N${airbnb_rev:,.0f}
Net Arbitrage Margin: N${margin:,.0f}
Property: {prop_desc or 'Coastal apartment'}
Arbitrage Score: {score}/100

Generate:
1. Rental Arbitrage Score justification
2. A professional landlord pitch script for Exokino Property Group
   offering to sublease this property for Airbnb. Emphasize 
   guaranteed rent, professional cleaning, corporate backing, 
   and zero hassle for the landlord.
"""
                system = """You are a property growth strategist 
and expert negotiator in the Namibian rental market. Generate 
compelling, warm and professional pitch scripts."""
                result = call_ai(prompt, system)
                st.markdown(result)

    with tab3:
        st.subheader("Distressed Property Scout")
        listing_text = st.text_area(
            "Paste property listing descriptions",
            height=200,
            placeholder="""Paste listings here...

Example:
URGENT SALE - Block of flats Swakopmund, 8 units, 
N$4,200,000 neg. Owner relocating. Bank mandate."""
        )

        if st.button("Scan for Opportunities", type="primary",
                     key="scout_btn"):
            if not listing_text.strip():
                st.warning("Please paste some listing text first.")
            else:
                with st.spinner("Scanning with AI..."):
                    prompt = f"""
Scan these Namibian property listings for high-value 
Airbnb conversion opportunities:

{listing_text}

Flag listings with these triggers:
MULTI-UNIT: block of flats, complex, multiple units, 
townhouse park, back rooms, multiple dwellings
DISTRESSED: repossessed, bank mandate, urgent sale, 
price reduced, owner relocating, négociable, urgent

For each match provide a table with:
Property Type | Town | Price | Urgency | Why it is a target

Then write a deal memo for the top opportunity including:
- Estimated Airbnb revenue potential
- Negotiation strategy  
- Immediate next action
"""
                    system = """You are a distressed property scout 
and Airbnb investment strategist for the Namibian market. Be 
direct, analytical and opportunity-focused."""
                    result = call_ai(prompt, system)
                    st.markdown(result)

