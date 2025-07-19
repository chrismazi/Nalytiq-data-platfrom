import streamlit as st
import pandas as pd
import plotly.express as px
import ollama  # Import Ollama for Gemma 2B integration


# Load the dataset
@st.cache_data
def load_data():
    file_path = r"C:\Users\educa\Downloads\EICV4_a\cs_s1_s2_s3_s4_s6a_s6e_s6f_person.dta"
    data = pd.read_stata(file_path)
    columns_to_keep = ['poverty', 'province', 'ur2_2012', 'Consumption', 's1q3y', 's3q2', 's1q1', 'district', 's4aq2']
    return data[columns_to_keep]


data = load_data()


# Convert Consumption column to numeric
data["Consumption"] = pd.to_numeric(data["Consumption"], errors="coerce")


# Education Mapping
education_mapping = {
    'Pre-primary': 'Nursery',
    'Primary 1': 'Primary',
    'Primary 2': 'Primary',
    'Primary 3': 'Primary',
    'Primary 4': 'Primary',
    'Primary 5': 'Primary',
    'Primary 6,7,8': 'Primary',
    'Not complete P1': 'Primary Dropout',
    'Secondary 1': 'Secondary',
    'Secondary 2': 'Secondary',
    'Secondary 3': 'Secondary',
    'Secondary 4': 'Secondary',
    'Secondary 5': 'Secondary',
    'Post primary 1': 'Post-Secondary',
    'Post primary 2': 'Post-Secondary',
    'Post primary 3': 'Post-Secondary',
    'Post primary 4': 'Post-Secondary',
    'Post primary 5': 'Post-Secondary',
    'Post primary 6,7,8': 'Post-Secondary',
    'University 1': 'Bachelors',
    'University 2': 'Bachelors',
    'University 3': 'Bachelors',
    'University 4': 'Masters',
    'University 5': 'Masters',
    'University 6': 'PhD',
    'University 7': 'PhD',
    'Missing': 'Unknown',
    'nan': 'Unknown',
    'Unknown': 'Unknown'
}


# Apply education mapping
data["education_level"] = data["s4aq2"].map(education_mapping)


# Sidebar filters
st.sidebar.header("Filters")
selected_province = st.sidebar.selectbox("Select Province", ["All"] + list(data["province"].dropna().unique()))
selected_gender = st.sidebar.selectbox("Select Gender (s1q1)", ["All"] + list(data["s1q1"].dropna().unique()))


if selected_province != "All":
    data = data[data["province"] == selected_province]
if selected_gender != "All":
    data = data[data["s1q1"] == selected_gender]


st.title("Poverty and Consumption Insights Dashboard")


# Chart 1: Poverty Distribution by Province
st.subheader("Poverty Distribution by Province")
poverty_province = data.groupby("province")["poverty"].mean().reset_index()
fig1 = px.pie(
    poverty_province,
    names="province",
    values="poverty",
    title="Poverty Rate by Province",
    color_discrete_sequence=px.colors.qualitative.Set3
)
st.plotly_chart(fig1)


# Chart 2: Average Consumption by Province
st.subheader("Average Consumption by Province")
avg_consumption_province = data.groupby("province")["Consumption"].mean().reset_index()
avg_consumption_province.dropna(subset=["Consumption"], inplace=True)  # Drop NaN values
fig2 = px.scatter(
    avg_consumption_province,
    x="province",
    y="Consumption",
    size="Consumption",
    title="Average Consumption by Province",
    color="province",
    color_discrete_sequence=px.colors.qualitative.Prism
)
st.plotly_chart(fig2)


# Chart 3: Top 5 Districts by Consumption
st.subheader("Top 5 Districts by Consumption")
top_districts = data.groupby("district")["Consumption"].mean().nlargest(5).reset_index()
fig3 = px.bar(
    top_districts,
    x="district",
    y="Consumption",
    title="Top 5 Districts by Consumption",
    color="district",
    color_discrete_sequence=px.colors.qualitative.Pastel
)
st.plotly_chart(fig3)


# Chart 4: Poverty Rate by Gender
st.subheader("Poverty Rate by Gender")
poverty_gender = data.groupby("s1q1")["poverty"].mean().reset_index()
fig4 = px.funnel(
    poverty_gender,
    x="poverty",
    y="s1q1",
    title="Poverty Rate by Gender",
    color="s1q1",
    color_discrete_sequence=px.colors.qualitative.Dark2
)
st.plotly_chart(fig4)


# Chart 5: Urban vs Rural Consumption
st.subheader("Urban vs Rural Consumption")
urban_rural_consumption = data.groupby("ur2_2012")["Consumption"].mean().reset_index()
fig5 = px.box(
    data,
    x="ur2_2012",
    y="Consumption",
    title="Urban vs Rural Consumption",
    color="ur2_2012",
    color_discrete_sequence=px.colors.qualitative.Bold
)
st.plotly_chart(fig5)


# Chart 6: Poverty Distribution by Education Level
st.subheader("Poverty Distribution by Education Level")
if "education_level" in data.columns:
    poverty_education = pd.crosstab(data["education_level"], data["poverty"]).reset_index()
    poverty_education = poverty_education.melt(
        id_vars=["education_level"],
        var_name="poverty_level",
        value_name="count"
    )
    fig9 = px.bar(
        poverty_education,
        x="count",
        y="poverty_level",
        color="education_level",
        barmode="stack",
        title="Poverty Distribution by Education Level",
        labels={"count": "Count", "poverty_level": "Poverty Level"},
        color_discrete_sequence=px.colors.qualitative.T10
    )
    st.plotly_chart(fig9)
else:
    st.warning("Education Level data is missing in the dataset.")


# AI Insights Section
st.sidebar.subheader("💬 Ask AI for Insights")
user_query = st.sidebar.text_input("Ask anything about the charts:")


def ask_gemma(query):
    """
    Uses the locally installed Gemma 2B model via Ollama to generate AI insights.
    This function passes the detailed chart data context to the LLM.
    """
    # Build a context string that includes both the description of each chart and the aggregated chart data.
    dashboard_context = (
        "You are Gemma, an expert data assistant. Here is the dashboard context including chart descriptions and aggregated data:\n\n"
        "1. **Poverty Rate by Province (Pie Chart):**\n"
        f"Data: {poverty_province.to_dict()}\n\n"
        "2. **Average Consumption by Province (Scatter Plot):**\n"
        f"Data: {avg_consumption_province.to_dict()}\n\n"
        "3. **Top 5 Districts by Consumption (Bar Chart):**\n"
        f"Data: {top_districts.to_dict()}\n\n"
        "4. **Poverty Rate by Gender (Funnel Chart):**\n"
        f"Data: {poverty_gender.to_dict()}\n\n"
        "5. **Urban vs Rural Consumption (Box Plot using aggregated averages):**\n"
        f"Data: {urban_rural_consumption.to_dict()}\n\n"
    )
    # Include the education-level data only if available.
    if "education_level" in data.columns:
        dashboard_context += (
            "6. **Poverty Distribution by Education Level (Stacked Bar Chart):**\n"
            f"Data: {poverty_education.to_dict()}\n\n"
        )
    dashboard_context += (
        "Please answer any questions with detailed, specific, and accurate insights based on this dashboard data."
    )


    messages = [
        {"role": "system", "content": dashboard_context},
        {"role": "user", "content": query}
    ]
    response = ollama.chat(model="gemma:2b", messages=messages)
    return response['message']['content'] if response and 'message' in response else "I couldn't generate an answer."


if user_query:
    ai_response = ask_gemma(user_query)
    st.sidebar.write("**AI Insight:**", ai_response)


# 📝 Dashboard description
st.write("""
This dashboard provides insights into poverty and consumption patterns based on various factors.
Use the sidebar to filter data and explore different insights.
""")



