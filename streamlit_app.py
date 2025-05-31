import os
import streamlit as st

# We import `openai` here just to check the version. 
# Once you verify that `openai.__version__` is ≥ 1.3.5, you can remove/comment out this import and the st.write line.
import openai  
from openai import OpenAI

from geopy.geocoders import Nominatim
from pytrends.request import TrendReq

# ─── Debug: Display the installed OpenAI version (remove/comment this out later) ─────────────────────
st.write("🔍 OpenAI library version:", openai.__version__)

# ─── Instantiate the new client using your secret key ───────────────────────────────────────────────
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def find_competitors(idea, location, limit=5):
    geolocator = Nominatim(user_agent="mvp_app")
    loc = geolocator.geocode(location)
    if not loc:
        return []
    return [f"{idea} Shop {i+1}" for i in range(limit)]


def demand_signal(idea, location):
    pytrends = TrendReq()
    kw = [idea]
    # For now, we default to India (“IN”). You can adjust or build a mapping function like location_iso(location) if needed.
    pytrends.build_payload(kw, geo="IN")
    data = pytrends.interest_over_time()
    if data.empty:
        return "No Google Trends data"
    avg = int(data[idea].mean())
    return f"Average interest: {avg}"


def predict(idea, location):
    comps = find_competitors(idea, location)
    trend = demand_signal(idea, location)

    # Assemble a simple “system” + “user” chat conversation
    messages = [
        {
            "role": "system",
            "content": (
                "You are a local startup advisor. "
                "Given the information below, decide if this idea will succeed locally and explain why or why not."
            )
        },
        {
            "role": "user",
            "content": (
                f"Idea: {idea}\n"
                f"Location: {location}\n"
                f"Competitors nearby: {', '.join(comps) or 'None found'}\n"
                f"Demand signal: {trend}\n\n"
                "Based on this data, will the idea succeed locally? Explain in a few sentences."
            )
        }
    ]

    # ─── Call the v1+ Chat API via the new `client` object ────────────────────────────────────────────
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=300,
        temperature=0.7
    )

    # Extract and return the assistant’s reply
    return response.choices[0].message.content.strip()


# ─── Streamlit UI ───────────────────────────────────────────────────────────────────────────────────
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

