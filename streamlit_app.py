import streamlit as st
from openai import OpenAI
import openai       # only for version check (can remove once confirmed)
import json
import pandas as pd
from geopy.exc import GeocoderUnavailable, GeocoderTimedOut
from geopy.geocoders import Nominatim
from pytrends.request import TrendReq

# ─── INITIAL SETUP ────────────────────────────────────────────────────────────────

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ─── HELPER FUNCTIONS ────────────────────────────────────────────────────────────

def find_competitors(idea, location, limit=5):
    """
    Try to geocode with Nominatim; if unavailable, return empty list.
    Otherwise return a list of dicts with dummy competitors.
    """
    try:
        geolocator = Nominatim(user_agent="mvp_app", timeout=10)
        loc = geolocator.geocode(location)
    except (GeocoderUnavailable, GeocoderTimedOut):
        return []
    except Exception:
        return []

    if not loc:
        return []

    # For demonstration, create fake competitor entries
    competitors = []
    for i in range(limit):
        competitors.append({
            "name": f"{idea.title()} Shop {i+1}",
            "distance": f"{round(0.4 + i * 0.6, 1)} miles",
            "rating": f"{round(3.5 + 0.2 * i, 1)}"
        })
    return competitors

def demand_signal(idea, location):
    """
    Return a dictionary of fake local demand metrics.
    Replace with real Google Trends or other local data as needed.
    """
    # For demonstration, return placeholders
    return {
        "search_volume": "High",
        "population_growth": "Medium",
        "competitor_density": "Low"
    }

def get_success_probability(comps, trend):
    """
    Simple heuristic for success probability as a string.
    (In reality, have your LLM return a numeric value.)
    """
    base = 50
    base -= len(comps) * 5
    if trend["search_volume"] == "High":
        base += 20
    if trend["population_growth"] == "High":
        base += 10
    if trend["competitor_density"] == "High":
        base -= 10
    val = max(0, min(100, base))
    return f"{val}%"

def predict(idea, location):
    """
    Call GPT to return a structured JSON (string) with:
      - success_probability
      - market_size
      - competitors_count
      - location
      - local_demand (dict)
      - nearby_competitors (list of dicts)
      - key_insights (list of strings)
      - risks (list of strings)
    """
    comps = find_competitors(idea, location)
    trend = demand_signal(idea, location)

    # Build the system + user messages. Note how we have to double {{ }} around JSON fields.
    prompt = f"""Evaluate the business idea \"{idea}\" in the location \"{location}\" using local competition, demand signals, and market size. 
Return the result in valid JSON with these exact keys and types:

{{
  "success_probability": "string, percentage, e.g. \"45%\"",
  "market_size": "small|medium|large",
  "competitors": integer,
  "location": "{location}",
  "local_demand": {{
    "search_volume": "Low|Medium|High",
    "population_growth": "Low|Medium|High",
    "competitor_density": "Low|Medium|High"
  }},
  "nearby_competitors": [
    {{
      "name": "Competitor Name",
      "distance": "X.X miles",
      "rating": "4.2"
    }},
    ...
  ],
  "key_insights": [
    "Insight 1",
    "Insight 2"
  ],
  "risks": [
    "Risk 1",
    "Risk 2"
  ]
}}

Here are the inputs you should use:
Idea: {idea}
Location: {location}
Competitors (dummy list): {[c['name'] for c in comps]}
Demand signals: {trend}
"""
    messages = [
        {"role": "system", "content": "You are an expert local market analyst. Return exactly valid JSON with no extra text."},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7
    )
    raw = response.choices[0].message.content.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # If parsing fails, return None so the UI can show an error
        return None

    return data

# ─── STREAMLIT UI ─────────────────────────────────────────────────────────────────

st.title("Reality Check GPT")
st.markdown("Get AI-powered predictions on whether your business idea will actually work in your local area")

st.markdown("---")
st.markdown("### Validate Your Idea")

# Input fields
idea = st.text_input("Your business concept", "")
location = st.text_input("Your city or neighborhood", "")

if st.button("Get Reality Check"):
    if not idea or not location:
        st.error("Please provide both a business idea and a location.")
    else:
        with st.spinner("Crunching local data and running AI..."):
            data = predict(idea, location)

        if data is None:
            st.error("Failed to parse AI response. Please try again.")
        else:
            # If we have valid JSON, unpack all fields:
            success_pct = data.get("success_probability", "N/A")
            market_size = data.get("market_size", "N/A")
            comps_count = data.get("competitors", 0)
            loc_name = data.get("location", location)
            local_demand = data.get("local_demand", {})
            nearby_comps = data.get("nearby_competitors", [])
            insights = data.get("key_insights", [])
            risks = data.get("risks", [])

            # ─── TOP METRICS CARDS ───────────────────────────────────────────────
            top_cols = st.columns(4)
            top_cols[0].metric("Success %", success_pct)
            top_cols[1].metric("Market Size", market_size.title())
            top_cols[2].metric("Competitors", str(comps_count))
            top_cols[3].metric("Location", loc_name.title())

            st.markdown("---")

            # ─── TWO-COLUMN LAYOUT ──────────────────────────────────────────────
            left, right = st.columns([3, 1])

            with left:
                # Local Demand Signals
                st.subheader("Local Demand Signals")
                if local_demand:
                    st.write(f"- **Google Search Volume:** {local_demand.get('search_volume', 'N/A')}")
                    st.write(f"- **Population Growth:** {local_demand.get('population_growth', 'N/A')}")
                    st.write(f"- **Competitor Density:** {local_demand.get('competitor_density', 'N/A')}")
                else:
                    st.write("No demand data available.")

                st.markdown("---")

                # Nearby Competitors Table
                st.subheader("Nearby Competitors")
                if nearby_comps:
                    df = pd.DataFrame(nearby_comps)
                    df = df.rename(columns={
                        "name": "Name",
                        "distance": "Distance (miles)",
                        "rating": "★ Rating"
                    })
                    st.table(df)
                else:
                    st.write("No competitors found.")

                st.markdown("---")

                # Key Insights
                st.subheader("Key Insights")
                if insights:
                    for insight in insights:
                        st.markdown(f"✔️ {insight}")
                else:
                    st.write("No insights provided.")

                st.markdown("---")

                # Potential Risks
                st.subheader("Potential Risks")
                if risks:
                    for r in risks:
                        st.markdown(f"⚠️ {r}")
                else:
                    st.write("No risks provided.")

                st.markdown("---")
                st.markdown("*Powered by AI analysis of local market data, demographics, and competition*")

            with right:
                # Sidebar‐style summary (duplicating key metrics)
                st.markdown("### Summary")
                st.metric(label="Success %", value=success_pct)
                st.metric(label="Market Size", value=market_size.title())
                st.metric(label="Competitors", value=str(comps_count))

                st.markdown("---")
                st.markdown("### Demand Signals")
                if local_demand:
                    st.write(f"- {local_demand.get('search_volume', 'N/A')} search volume")
                    st.write(f"- {local_demand.get('population_growth', 'N/A')} population growth")
                    st.write(f"- {local_demand.get('competitor_density', 'N/A')} density")
                else:
                    st.write("N/A")

# ─── END ─────────────────────────────────────────────────────────────────────────────────


