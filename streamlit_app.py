import streamlit as st
from openai import OpenAI
import openai           # only if you use openai.__version__ for debugging
from geopy.exc import GeocoderUnavailable, GeocoderTimedOut
from geopy.geocoders import Nominatim
from pytrends.request import TrendReq

# If you were debugging, you can keep this for a moment to confirm version:
st.write("🔍 OpenAI library version:", openai.__version__)

# Instantiate the OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def find_competitors(idea, location, limit=5):
    """
    Attempt to geocode the location. If geocoding fails, return an empty list
    (or use placeholders instead).
    """
    try:
        geolocator = Nominatim(user_agent="mvp_app", timeout=10)
        loc = geolocator.geocode(location)
    except (GeocoderUnavailable, GeocoderTimedOut):
        # Free Nominatim is unavailable or timed out
        return []  # or: [f"{idea} Placeholder {i+1}" for i in range(limit)]
    except Exception:
        # Any other error (e.g., parsing), fail gracefully
        return []

    if not loc:
        return []

    return [f"{idea} Shop {i+1}" for i in range(limit)]


def demand_signal(idea, location):
    pytrends = TrendReq()
    kw = [idea]
    pytrends.build_payload(kw, geo="IN")  # Or your desired country code
    data = pytrends.interest_over_time()
    if data.empty:
        return "No Google Trends data"
    avg = int(data[idea].mean())
    return f"Average interest: {avg}"


def predict(idea, location):
    comps = find_competitors(idea, location)
    trend = demand_signal(idea, location)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a local startup advisor. Given the following info, "
                "predict if the idea will succeed locally and explain why or why not."
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

    # Use the v1+ ChatCompletion client syntax
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=300,
        temperature=0.7
    )

    return response.choices[0].message.content.strip()


# ─── Streamlit UI ──────────────────────────────────────────────────────────────────────────

st.title("Reality Check GPT — Local Idea Validator")

idea = st.text_input("Your business idea")
location = st.text_input("Your city or neighborhood", "")

if st.button("Validate my idea"):
    if not idea:
        st.warning("Please enter an idea!")
    else:
        with st.spinner("Crunching local data…"):
            result = predict(idea, location)
            competitors = find_competitors(idea, location)
            demand = demand_signal(idea, location)

        st.subheader("Reality Check")
        st.write(result)
        st.write("**Nearby competitors:**", ", ".join(competitors) if competitors else "None found")
        st.write("**Demand signal:**", demand)
