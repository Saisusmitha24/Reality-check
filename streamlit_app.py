import streamlit as st
from openai import OpenAI
import openai
import json

# Setup OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Title and instructions
st.title("Reality Check GPT")
st.subheader("Get AI-powered predictions on whether your business idea will actually work in your local area")

st.markdown("### Validate Your Idea")
idea = st.text_input("Enter your business idea", "coffee shop")
location = st.text_input("Enter your city or neighborhood", "penukonda")

if st.button("Get Reality Check"):
    with st.spinner("Analyzing your idea using local data..."):

        messages = [
            {
                "role": "system",
                "content": (
                    "You're an expert market analyst generating personalized local business evaluations. "
                    "Respond with structured JSON including success probability, competitor analysis, demand signal, "
                    "and key risks/opportunities."
                )
            },
            {
                "role": "user",
                "content": f"""Evaluate the business idea \"{idea}\" in the location \"{location}\" using local competition, demand signals, and market size. Return the result in this format:
{{
  \"success_probability\": \"45%\",
  \"market_size\": \"Medium\",
  \"competitors\": 3,
  \"location\": \"{location}\",
  \"local_demand\": {{
    \"search_volume\": \"High\",
    \"population_growth\": \"Medium\",
    \"competitor_density\": \"Low\"
  }},
  \"nearby_competitors\": [
    {{\"name\": \"Local Coffee Spot\", \"distance\": \"0.6 miles\", \"rating\": \"4.1\"}},
    {{\"name\": \"Main Street Café\", \"distance\": \"1.2 miles\", \"rating\": \"4.3\"}}
  ],
  \"key_insights\": [
    \"Strong local demand with moderate competition\",
    \"Opportunity to attract office crowd in the mornings\"
  ],
  \"risks\": [
    \"Low weekend foot traffic\",
    \"High initial investment for equipment\"
  ]
}"""
            }
        ]

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7
            )

            content = response.choices[0].message.content
            data = json.loads(content)

            # Display sections
            st.subheader("Success Probability")
            st.metric(label="Chance of Success", value=data["success_probability"])

            st.subheader("Market Insights")
            st.write(f"**Market Size:** {data['market_size']}")
            st.write(f"**Competitors Nearby:** {data['competitors']}")

            st.subheader("Local Demand Signals")
            for key, val in data["local_demand"].items():
                st.write(f"**{key.replace('_', ' ').title()}:** {val}")

            st.subheader("Nearby Competitors")
            for comp in data["nearby_competitors"]:
                st.markdown(f"- **{comp['name']}** — {comp['distance']} — ⭐ {comp['rating']}")

            st.subheader("Key Insights")
            for insight in data["key_insights"]:
                st.markdown(f"✅ {insight}")

            st.subheader("Potential Risks")
            for risk in data["risks"]:
                st.markdown(f"⚠️ {risk}")

        except json.JSONDecodeError:
            st.error("AI response could not be parsed. Please try again.")
        except Exception as e:
            st.error(f"Unexpected error: {e}")


