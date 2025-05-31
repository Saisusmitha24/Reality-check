import os
import streamlit as st
import openai
st.write("🔍 OpenAI library version:", openai.__version__)

from geopy.geocoders import Nominatim
from pytrends.request import TrendReq

openai.api_key = st.secrets["OPENAI_API_KEY"]

def find_competitors(idea, location, limit=5):
    geolocator = Nominatim(user_agent="mvp_app")
    loc = geolocator.geocode(location)
    if not loc:
        return []
    return [f"{idea} Shop {i+1}" for i in range(limit)]

def demand_signal(idea, location):
    pytrends = TrendReq()
    kw = [idea]
    pytrends.build_payload(kw, geo="IN")  # You can change to location_iso(location)
    data = pytrends.interest_over_time()
    if data.empty:
        return "No Google Trends data"
    avg = int(data[idea].mean())
    return f"Average interest: {avg}"

def predict(idea, location):
    comps = find_competitors(idea, location)
    trend = demand_signal(idea, location)

    # Construct a “system” + “user” conversation
    messages = [
        {
            "role": "system",
            "content": "You are a local startup advisor. Use the data below to predict if the idea can succeed locally."
        },
        {
            "role": "user",
            "content": (
                f"Idea: {idea}\n"
                f"Location: {location}\n"
                f"Competitors nearby: {', '.join(comps) or 'None found'}\n"
                f"Demand signal: {trend}\n\n"
                "Based on this information, give a concise prediction: will it succeed locally? Explain why or why not."
            )
        }
    ]

    # Call the new ChatCompletion endpoint
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=300,
        temperature=0.7
    )

    # Extract the assistant’s reply
    return response.choices[0].message.content.strip()


# Streamlit UI
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
