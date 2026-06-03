import streamlit as st
import os
import google.generativeai as genai
import json
import sqlite3

DB_PATH = "database/properties.db"

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def call_ai(prompt, system):
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system
        )
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=2000
            )
        )
        return response.text
    except Exception as e:
        return f"API Error: {str(e)}"

def get_airbnb_avg(area):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT AVG(price_per_night) FROM airbnb_listings WHERE area=?", (area,))
    result = c.fetchone()[0]
    conn.close()
    return round(result or 1000, 0)

def render_ai_tools():
    st.header("Exokino AI Deal Engine")
    st.caption("Powered by Google AI — three tools to find, analyse and pitch deals")

    st.markdown("""
    <div style='background: linear-gradient(135deg, #0F6E56, #1D9E75); 
    padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;'>
    <h2 style='color: white; margin: 0; font-size: 1.4rem;'>
    Exokino AI Deal Engine</h2>
    <p style='color: #9FE1CB; margin: 0.5rem 0 0 0; font-size: 0.9rem;'>
    Three AI-powered tools to find, analyse and close property deals 
    faster than any agency in Namibia</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "🏦 Bank Feasibility",
        "📈 Rental Arbitrage",
        "🎯 Distressed Scout",
        "🏠 Property Valuation"
    ])

    with tab4:
        st.subheader("Property Valuation")
        st.caption("Compare asking price against local sale comps")

        col1, col2 = st.columns(2)
        with col1:
            valuation_area = st.selectbox(
                "Area",
                ["Langstrand", "Swakopmund", "Walvis Bay", "Henties Bay", "Windhoek"],
                key="valuation_area"
            )
            property_type = st.selectbox(
                "Property type",
                ["apartment", "house", "townhouse"],
                key="valuation_property_type"
            )
            bedrooms = st.number_input(
                "Bedrooms",
                min_value=1,
                max_value=5,
                value=2,
                step=1,
                key="valuation_bedrooms"
            )
        with col2:
            size_m2 = st.number_input(
                "Size in m2",
                min_value=20,
                max_value=2000,
                value=100,
                step=5,
                key="valuation_size_m2"
            )
            asking_price = st.number_input(
                "Asking price (N$)",
                min_value=100000,
                max_value=50000000,
                value=1500000,
                step=50000,
                key="valuation_asking_price"
            )

        if st.button("Run Valuation", type="primary"):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute(
                """
                SELECT AVG(price), AVG(price_per_m2), COUNT(*) 
                FROM listings 
                WHERE location LIKE ? AND bedrooms = ? 
                AND listing_type = 'for-sale'
                AND price > 0
                """,
                (f"%{valuation_area}%", bedrooms)
            )
            avg_price, avg_price_per_m2, comp_count = c.fetchone()
            conn.close()

            if not comp_count or not avg_price_per_m2:
                st.warning("Not enough comparable sale listings found for this area and bedroom count.")
            else:
                fair_market_value = avg_price_per_m2 * size_m2
                price_gap = asking_price - fair_market_value
                price_gap_pct = (price_gap / fair_market_value) * 100 if fair_market_value else 0
                market_position = "above market" if price_gap > 0 else "below market"

                metric1, metric2, metric3, metric4 = st.columns(4)
                metric1.metric("Comps Found", int(comp_count))
                metric2.metric("Avg Comp Price", f"N${avg_price:,.0f}")
                metric3.metric("Avg Price/m2", f"N${avg_price_per_m2:,.0f}")
                metric4.metric("Fair Value", f"N${fair_market_value:,.0f}")

                if price_gap > 0:
                    st.error(f"Asking price is N${abs(price_gap):,.0f} ({abs(price_gap_pct):.1f}%) above market.")
                else:
                    st.success(f"Asking price is N${abs(price_gap):,.0f} ({abs(price_gap_pct):.1f}%) below market.")

                with st.spinner("Writing valuation summary..."):
                    prompt = f"""
Property Valuation:
- Area: {valuation_area}, Namibia
- Property Type: {property_type}
- Bedrooms: {bedrooms}
- Size: {size_m2} m2
- Asking Price: N${asking_price:,.0f}
- Comparable Sale Count: {comp_count}
- Average Comparable Price: N${avg_price:,.0f}
- Average Comparable Price per m2: N${avg_price_per_m2:,.0f}
- Estimated Fair Market Value: N${fair_market_value:,.0f}
- Asking Price Position: {market_position}
- Difference: N${price_gap:,.0f} ({price_gap_pct:.1f}%)

Write one concise paragraph explaining whether this asking price looks fair, overpriced, or attractive based on the comparable sales data.
"""
                    system = "You are a Namibian property valuation analyst. Write clear, practical valuation summaries using comparable sale data."
                    result = call_ai(prompt, system)
                    st.markdown(result)

    with tab1:
        st.subheader("Bank Feasibility Report")
        st.caption("Enter a property and get a full underwriter analysis")

        col1, col2 = st.columns(2)
        with col1:
            price = st.number_input("Property price (N$)", 
                min_value=500000, max_value=20000000, 
                value=2500000, step=50000)
            area = st.selectbox("Area", 
                ["Langstrand", "Swakopmund", "Walvis Bay", 
                 "Henties Bay", "Windhoek"])
            units = st.number_input("Number of units", 
                min_value=1, max_value=20, value=1)
        with col2:
            nightly_rate = st.number_input("Airbnb nightly rate (N$)", 
                min_value=400, max_value=5000, 
                value=int(get_airbnb_avg(area)), step=50)
            occupancy = st.slider("Expected occupancy %", 
                30, 90, 65)

        if st.button("Generate Bank Report", type="primary"):
            with st.spinner("Analysing deal..."):
                prompt = f"""
Property Details:
- Purchase Price: N${price:,}
- Location: {area}, Namibia
- Number of Units: {units}
- Airbnb Nightly Rate: N${nightly_rate}
- Expected Occupancy: {occupancy}%

Generate a comprehensive Bank Feasibility Report:
1. Calculate 25% cash deposit and remaining loan amount
2. Estimate monthly bond repayment at Namibian Prime Rate (11.5%) + 1.5% = 13% over 15 years
3. Factor in: 15% Airbnb platform/cleaning fees, 10% maintenance/municipal rates, 20% vacancy buffer
4. Calculate DSCR. State APPROVED FOR BANK PITCH if DSCR above 1.25, else REJECTED BY BANK CRITERIA
5. Output clean JSON with: Deposit_Required, Loan_Amount, Monthly_Repayment, Gross_Revenue, Net_Operating_Income, DSCR, Bank_Decision

Be precise with calculations. Show your working clearly.
"""
                system = "You are an expert commercial real estate underwriter specialized in the Namibian property market. Provide precise financial analysis with clear calculations."
                
                result = call_ai(prompt, system)
                st.markdown(result)

                try:
                    import re
                    json_match = re.search(r'\{[^{}]+\}', result, re.DOTALL)
                    if json_match:
                        deal_data = json.loads(json_match.group())
                        st.subheader("Deal Summary")
                        cols = st.columns(len(deal_data))
                        for i, (k, v) in enumerate(deal_data.items()):
                            if k != "Bank_Decision":
                                cols[i % len(cols)].metric(
                                    k.replace("_", " "), 
                                    f"N${v:,}" if isinstance(v, (int, float)) else str(v)
                                )
                        decision = deal_data.get("Bank_Decision", "")
                        if "APPROVED" in str(decision):
                            st.success(f"✅ {decision}")
                        else:
                            st.error(f"❌ {decision}")
                except:
                    pass

    with tab2:
        st.subheader("Rental Arbitrage Analyser")
        st.caption("Find properties where Airbnb revenue beats long-term rental cost")

        col1, col2 = st.columns(2)
        with col1:
            arb_area = st.selectbox("Area", 
                ["Langstrand", "Swakopmund", "Walvis Bay", "Henties Bay"],
                key="arb_area")
            monthly_rent = st.number_input("Monthly rent asking price (N$)", 
                min_value=3000, max_value=30000, 
                value=8000, step=500)
        with col2:
            arb_rate = st.number_input("Airbnb nightly rate (N$)", 
                min_value=400, max_value=3000, 
                value=int(get_airbnb_avg(arb_area)), step=50,
                key="arb_rate")
            prop_description = st.text_area(
                "Property description (optional)", 
                placeholder="3 bed apartment, sea view, parking...",
                height=100)

        if st.button("Calculate Arbitrage Score", type="primary"):
            with st.spinner("Calculating arbitrage opportunity..."):
                airbnb_monthly = arb_rate * 0.50 * 30
                margin = airbnb_monthly - monthly_rent - 1500

                col1, col2, col3 = st.columns(3)
                col1.metric("Airbnb Revenue (50% occ)", f"N${airbnb_monthly:,.0f}/mo")
                col2.metric("Monthly Rent Cost", f"N${monthly_rent:,}/mo")
                col3.metric("Net Arbitrage Margin", f"N${margin:,.0f}/mo",
                    delta="Positive" if margin > 0 else "Negative")

                prompt = f"""
Property Rental Arbitrage Analysis:
- Location: {arb_area}, Namibia
- Monthly Long-term Rent: N${monthly_rent:,}
- Airbnb Nightly Rate: N${arb_rate}
- Property: {prop_description or 'Coastal apartment'}
- Airbnb Monthly Revenue (50% occupancy): N${airbnb_monthly:,.0f}
- Estimated Costs (cleaning/wifi): N$1,500/month
- Net Arbitrage Margin: N${margin:,.0f}/month

1. Calculate the Rental Arbitrage Score (1-100)
2. Assess whether the net margin exceeds monthly rent by 40%
3. If viable, generate a professional Landlord Pitch Script for Exokino Property Group
   - Emphasize: guaranteed monthly rent, professional cleaning, corporate backing
   - Keep it warm, professional and persuasive
   - Sign off as Exokino Property Group
"""
                system = "You are a property growth strategist specializing in Airbnb rental arbitrage in Namibia. Generate compelling, professional analysis and pitch scripts."
                
                result = call_ai(prompt, system)
                st.markdown(result)

    with tab3:
        st.subheader("Distressed Property Scout")
        st.caption("Paste raw listing text — AI flags high-value targets automatically")

        listing_text = st.text_area(
            "Paste property listing descriptions here",
            height=200,
            placeholder="""Paste multiple listings separated by blank lines...

Example:
URGENT SALE - Block of flats Swakopmund, 8 units, N$4,200,000 neg. Owner relocating. Bank mandate.

Townhouse park Walvis Bay - 6 units on one title, N$3,800,000. Price reduced from N$4.5m."""
        )

        if st.button("Scan for Opportunities", type="primary"):
            if not listing_text.strip():
                st.warning("Please paste some listing text first.")
            else:
                with st.spinner("Scanning listings..."):
                    prompt = f"""
Scan these Namibian property listings and extract high-value Airbnb conversion opportunities:

{listing_text}

Flag listings containing:
MULTI-UNIT keywords: "block of flats", "complex", "multiple units", "townhouse park", "back rooms", "multiple dwellings"
DISTRESSED keywords: "repossessed", "bank mandate", "urgent sale", "price reduced", "owner relocating", "négociable", "urgent", "emigrating"

For each match, provide a structured table with:
- Property Type
- Town/Suburb  
- Listed Price
- Urgency Level (High/Medium/Low)
- Why it's a prime Airbnb target (1 sentence)

Then for the top opportunity, write a short Deal Memo with:
- Estimated Airbnb revenue potential
- Recommended negotiation strategy
- Immediate next action
"""
                    system = "You are a distressed property scout and Airbnb investment strategist for the Namibian market. Be direct, analytical and opportunity-focused."
                    
                    result = call_ai(prompt, system)
                    st.markdown(result)

                    st.info("💡 Tip: Copy the top target details and run them through the Bank Feasibility tool to get a full deal analysis.")
