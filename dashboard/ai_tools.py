import streamlit as st
import sqlite3
import json
import urllib.request
import urllib.error
import os
import pandas as pd

DB_PATH = "database/properties.db"

import os
try:
    import streamlit as st
    GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "") or os.environ.get("GROQ_API_KEY", "")
except:
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
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

    tab1, tab2, tab3, tab4 = st.tabs([
        "🏦 Bank Feasibility",
        "📈 Rental Arbitrage",
        "🎯 Distressed Scout",
        "🏡 Property Valuation"
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
            col_a, col_b = st.columns(2)
            with col_a:
                bedrooms = st.number_input("Bedrooms per unit",
                    min_value=0, max_value=10, value=2,
                    help="Bedrooms in each unit/flat")
            with col_b:
                units = st.number_input("Number of units",
                    min_value=1, max_value=50, value=1,
                    help="1 = single property, 2+ = block of flats or complex")
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
        # Revenue = nightly rate x occupancy x 30 days x number of units
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
Bedrooms per unit: {bedrooms}
Number of units: {units}
Deal type: {"Single property" if units == 1 else f"Multi-unit complex ({units} units)"}
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

    with tab4:
        st.subheader("Property Valuation Tool")
        st.caption("Estimate fair market value using real Namibian comps from our database")

        col1, col2 = st.columns(2)
        with col1:
            val_area = st.selectbox("Area", [
                "Swakopmund", "Walvis Bay", "Langstrand",
                "Henties Bay", "Windhoek", "Rundu",
                "Rehoboth", "Otjiwarongo", "Oshakati"
            ], key="val_area")
            val_type = st.selectbox("Property type", [
                "Apartment/Flat", "House", "Townhouse",
                "Commercial", "Industrial/Land"
            ], key="val_type")
            val_listing = st.selectbox("Looking to", [
                "Buy (for-sale comps)",
                "Rent (to-rent comps)"
            ], key="val_listing")

        with col2:
            val_beds = st.number_input("Bedrooms",
                min_value=0, max_value=10, value=2,
                key="val_beds")
            val_size = st.number_input("Size (m²)",
                min_value=0, max_value=2000, value=80,
                key="val_size")
            val_asking = st.number_input(
                "Asking price / rent (N$)",
                min_value=0, max_value=20000000,
                value=0, step=10000,
                key="val_asking")

        if st.button("Value This Property", 
                     type="primary", key="val_btn"):
            
            listing_type = "for-sale" if "Buy" in val_listing else "to-rent"
            
            try:
                conn_val = sqlite3.connect(DB_PATH)
                
                comps_df = pd.read_sql_query("""
                    SELECT price, bedrooms, size_m2, 
                    price_per_m2, location, title
                    FROM listings
                    WHERE location LIKE ?
                    AND listing_type = ?
                    AND price > 0
                    AND bedrooms BETWEEN ? AND ?
                    ORDER BY date_scraped DESC
                    LIMIT 20
                """, conn_val, params=[
                    f"%{val_area}%",
                    listing_type,
                    max(0, val_beds - 1),
                    val_beds + 1
                ])
                
                broad_df = pd.read_sql_query("""
                    SELECT price, bedrooms, size_m2,
                    price_per_m2, location, title
                    FROM listings
                    WHERE location LIKE ?
                    AND listing_type = ?
                    AND price > 0
                    ORDER BY date_scraped DESC
                    LIMIT 50
                """, conn_val, params=[
                    f"%{val_area}%",
                    listing_type
                ])
                
                conn_val.close()
                
            except Exception as e:
                st.error(f"Database error: {e}")
                comps_df = pd.DataFrame()
                broad_df = pd.DataFrame()

            if not comps_df.empty:
                avg_comp_price = comps_df["price"].mean()
                median_comp = comps_df["price"].median()
                min_comp = comps_df["price"].min()
                max_comp = comps_df["price"].max()
                
                avg_per_m2 = broad_df[
                    broad_df["price_per_m2"] > 0
                ]["price_per_m2"].mean() if not broad_df.empty else 0
                
                size_based = (avg_per_m2 * val_size 
                              if avg_per_m2 > 0 and val_size > 0 
                              else 0)
                
                if size_based > 0:
                    estimated_value = (avg_comp_price * 0.6 + 
                                      size_based * 0.4)
                else:
                    estimated_value = avg_comp_price

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Estimated Value", 
                    f"N${estimated_value:,.0f}")
                c2.metric("Comp Average", 
                    f"N${avg_comp_price:,.0f}")
                c3.metric("Comp Range",
                    f"N${min_comp:,.0f}–N${max_comp:,.0f}")
                c4.metric("Comps Found", len(comps_df))

                if avg_per_m2 > 0:
                    st.metric("Avg Price per m²", 
                        f"N${avg_per_m2:,.0f}/m²")

                if val_asking > 0:
                    diff = val_asking - estimated_value
                    diff_pct = (diff / estimated_value) * 100
                    if diff > 0:
                        st.warning(
                            f"Asking price is **N${diff:,.0f} "
                            f"({diff_pct:.1f}%) above** estimated "
                            f"market value. Room to negotiate.")
                    else:
                        st.success(
                            f"Asking price is **N${abs(diff):,.0f} "
                            f"({abs(diff_pct):.1f}%) below** estimated "
                            f"market value. Good deal.")

                st.subheader("Comparable Properties")
                display = comps_df[["title","price",
                                    "bedrooms","location"]].copy()
                display["price"] = display["price"].apply(
                    lambda x: f"N${x:,.0f}")
                display.columns = ["Property","Price",
                                   "Beds","Area"]
                st.dataframe(display, use_container_width=True,
                            hide_index=True)

                with st.spinner("Generating AI valuation summary..."):
                    prompt = f"""
Property Valuation Request:
- Area: {val_area}, Namibia
- Type: {val_type}
- Bedrooms: {val_beds}
- Size: {val_size}m²
- Listing type: {val_listing}
- Asking price: {"N$" + f"{val_asking:,}" if val_asking > 0 else "Not provided"}

Market Data from Database:
- Comparable properties found: {len(comps_df)}
- Average comp price: N${avg_comp_price:,.0f}
- Median comp price: N${median_comp:,.0f}
- Price range: N${min_comp:,.0f} to N${max_comp:,.0f}
- Avg price per m²: N${avg_per_m2:,.0f}
- Estimated market value: N${estimated_value:,.0f}

Write a professional 1-paragraph property valuation summary 
for {val_area}. Include market context, whether the asking 
price is fair, and a negotiation recommendation. 
Be specific to the Namibian market.
"""
                    system = """You are a certified property 
valuer with 15 years experience in the Namibian real estate 
market. Write concise, professional valuation summaries."""
                    
                    result = call_ai(prompt, system)
                    st.markdown("**AI Valuation Summary**")
                    st.markdown(result)

            else:
                st.info(
                    f"Not enough comp data for {val_area} yet. "
                    f"Try a nearby area or run the scrapers to "
                    f"build more data. Broad market data below:")
                
                if not broad_df.empty:
                    st.metric("Area avg price (all beds)",
                        f"N${broad_df['price'].mean():,.0f}")
                    st.metric("Listings in area",
                        len(broad_df))

