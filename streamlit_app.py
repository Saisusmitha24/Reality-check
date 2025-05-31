%%bash
cat > streamlit_app.py << 'EOF'
import os
import streamlit as st
import openai
from geopy.geocoders import Nominatim
from pytrends.request import TrendReq

openai.api_key = os.getenv("OPENAI_API_KEY")

def find_competitors(idea, location, limit=5):
    geolocator = Nominatim(user_agent="mvp_app")
    loc = geolocator.geocode(location)
    if not loc:
        return []
    # search for businesses matching keywords in radius
    query = f"{idea} near {location}"
    # Nominatim “amenity” search is limited—here we just return the location coords
    # In a real MVP you’d hit a proper Places API, but this gives you a placeholder.
    return [f"{idea} Shop {i+1}" for i in range(limit)]

def demand_signal(idea, location):
    pytrends = TrendReq()
    kw = [idea]
    pytrends.build_payload(kw, geo=location_iso(location))
    data = pytrends.interest_over_time()
    if data.empty:
        return "No Google Trends data"
    avg = int(data[idea].mean())
    return f"Average interest: {avg}"

def location_iso(loc_name):
    # crude mapping of city to ISO2 for Google Trends, e.g. “US-NY”
    # For a proper MVP, ask user to input region code or default to country.
    return st.session_state.get("geo", "US")

def predict(idea, location):
    comps = find_competitors(idea, location)
    trend = demand_signal(idea, location)
    prompt = f"""
You are a local startup advisor.
Idea: {idea}
Location: {location}
Competitors nearby: {', '.join(comps) or 'None found'}
Demand signal: {trend}

Given these, predict whether the idea will succeed locally, and why.
"""
    resp = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=300,
        temperature=0.7
    )
    return resp.choices[0].text.strip()

st.title("Reality Check GPT — Local Idea Validator")
idea = st.text_input("Your business idea")
location = st.text_input("Your city or neighborhood", "Bangalore")
if st.button("Validate my idea"):
    if not idea:
        st.warning("Please enter an idea!")
    else:
        with st.spinner("Crunching local data…"):
            result = predict(idea, location)
        st.subheader("Reality Check")
        st.write(result)
        st.write("**Nearby competitors:**", find_competitors(idea, location))
        st.write("**Demand signal:**", demand_signal(idea, location))
EOF
