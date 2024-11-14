import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import joblib
from io import BytesIO
from statsmodels.tsa.arima.model import ARIMA
from datetime import datetime

# Helper functions
def classify_patient_condition(systolic, diastolic, pulse, temp, spo2):
    if (90 <= systolic <= 120 and 60 <= diastolic <= 80 and 60 <= pulse <= 100 
            and 36.5 <= temp <= 37.5 and 95 <= spo2 <= 100):
        return "Normal"
    return "At Risk"

def disease_recommendation(condition):
    if condition == "Normal":
        return "No immediate diseases suggested based on normal readings."
    else:
        return ("Possibilities include hypertension, heart disease, respiratory issues, "
                "or other conditions requiring further medical assessment.")

# App setup
st.title("Patient Condition Prediction App")

# Sidebar for user input
st.sidebar.header("Patient Input Features")
systolic = st.sidebar.slider("Systolic Pressure (mmHg)", 70, 180, 110)
diastolic = st.sidebar.slider("Diastolic Pressure (mmHg)", 40, 120, 75)
pulse = st.sidebar.slider("Pulse Rate (bpm)", 40, 180, 85)
temperature = st.sidebar.slider("Temperature (°C)", 35.0, 40.0, 37.0)
spo2 = st.sidebar.slider("SPO2 (%)", 70, 100, 98)

# Predict patient condition
input_data = pd.DataFrame([[systolic, diastolic, pulse, temperature, spo2]], 
                          columns=["Systolic", "Diastolic", "Pulse", "Temperature", "SPO2"])
predicted_condition = classify_patient_condition(systolic, diastolic, pulse, temperature, spo2)
disease_suggestion = disease_recommendation(predicted_condition)

# Main output
st.subheader("Patient Condition Prediction")
st.write(f"Predicted Condition: **{predicted_condition}**")
st.write("### Input Parameters")
st.write(input_data)
st.write("### Suggested Disease Considerations")
st.write(disease_suggestion)

# Explore Page with charts and recommendations
st.subheader("Explore Patient Condition Data")

# Time series data using today's date for the hourly timeline
today = datetime.now().date()
time_data = pd.date_range(start=today, periods=24, freq="H")

# Adjust the condition distribution based on predicted condition
if predicted_condition == "Normal":
    condition_data = ["Normal"] * 18 + ["At Risk"] * 6
else:
    condition_data = ["At Risk"] * 18 + ["Normal"] * 6

plot_data = pd.DataFrame({
    "Time": time_data,
    "Condition": condition_data
})

# Charting functions
def plot_condition_distribution(data):
    fig, ax = plt.subplots()
    condition_counts = data["Condition"].value_counts()
    ax.pie(condition_counts, labels=condition_counts.index, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    return fig

def plot_hourly_condition_counts(data):
    fig, ax = plt.subplots()
    data.groupby("Condition").size().plot(kind="bar", ax=ax, color=["skyblue", "salmon"])
    ax.set_ylabel("Count")
    return fig

def plot_time_series(data):
    fig, ax = plt.subplots()
    data.set_index("Time")["Condition"].apply(lambda x: 1 if x == "At Risk" else 0).plot(ax=ax)
    ax.set_ylabel("Condition (1 = At Risk, 0 = Normal)")
    return fig

# Display charts
st.write("#### Condition Distribution")
st.pyplot(plot_condition_distribution(plot_data))

st.write("#### Hourly Condition Counts")
st.pyplot(plot_hourly_condition_counts(plot_data))

st.write("#### Time Series of Patient Condition")
st.pyplot(plot_time_series(plot_data))

# Automated Time Series Prediction (Example with ARIMA)
plot_data['Condition_Binary'] = plot_data["Condition"].apply(lambda x: 1 if x == "At Risk" else 0)
model = ARIMA(plot_data['Condition_Binary'], order=(1, 1, 1))
model_fit = model.fit()
future_pred = model_fit.forecast(steps=24)

# Generate report with embedded images
st.write("#### Download Report")
report_buffer = BytesIO()
with pd.ExcelWriter(report_buffer, engine="xlsxwriter") as writer:
    input_data.to_excel(writer, sheet_name="Patient Input Data")
    plot_data.to_excel(writer, sheet_name="Time Series Data")
    condition_counts = plot_data["Condition"].value_counts()
    condition_counts.to_excel(writer, sheet_name="Condition Distribution")
    
    # Add charts to Excel
    workbook = writer.book
    worksheet = writer.sheets["Condition Distribution"]
    
    # Save and insert pie chart
    pie_chart_fig = plot_condition_distribution(plot_data)
    pie_image = BytesIO()
    pie_chart_fig.savefig(pie_image, format='png')
    pie_image.seek(0)
    worksheet.insert_image("G2", "Pie Chart", {'image_data': pie_image})
    
    # Save and insert bar chart
    bar_chart_fig = plot_hourly_condition_counts(plot_data)
    bar_image = BytesIO()
    bar_chart_fig.savefig(bar_image, format='png')
    bar_image.seek(0)
    worksheet.insert_image("G20", "Bar Graph", {'image_data': bar_image})
    
    # Save and insert time series chart
    ts_chart_fig = plot_time_series(plot_data)
    ts_image = BytesIO()
    ts_chart_fig.savefig(ts_image, format='png')
    ts_image.seek(0)
    worksheet.insert_image("G40", "Time Series", {'image_data': ts_image})

    # Insert the disease suggestion
    worksheet.write("B2", "Disease Suggestion: " + disease_suggestion)

report_buffer.seek(0)
st.download_button("Download Report", data=report_buffer, file_name="patient_condition_report_with_charts.xlsx")
