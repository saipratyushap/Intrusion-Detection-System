"""
=============================================================================
ENHANCED ANALYTICS MODULE
=============================================================================
This module adds 7 advanced analytics features to the Streamlit app:
1. Custom Date Range Picker
2. Comparison Analytics
3. Trend Forecasting
4. Anomaly Detection
5. PDF Report Export
6. Interactive Charts (Plotly)
7. Correlation Analysis
=============================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from fpdf import FPDF


# =============================================================================
# 1. CUSTOM DATE RANGE PICKER
# =============================================================================
def show_date_range_picker(df):
    """Replace the selectbox with a calendar date picker for custom date selection."""
    st.markdown('<div class="section-header">📅 Custom Date Range</div>', unsafe_allow_html=True)
    
    if 'Timestamp' in df.columns:
        df['Date'] = pd.to_datetime(df['Timestamp']).dt.date
        min_date = df['Date'].min()
        max_date = df['Date'].max()
    else:
        min_date = datetime.now().date() - timedelta(days=30)
        max_date = datetime.now().date()
    
    date_option = st.radio(
        "Select Date Range Type:",
        ["Quick Select", "Custom Range"],
        horizontal=True
    )
    
    filtered_df = df.copy()
    
    if date_option == "Quick Select":
        time_filter = st.selectbox(
            "Select Time Range",
            ["All Time", "Last 24 Hours", "Last 7 Days", "Last 30 Days", "Last 90 Days"]
        )
        
        if time_filter == "All Time":
            filtered_df = df.copy()
        elif time_filter == "Last 24 Hours":
            if 'Timestamp' in df.columns:
                cutoff = datetime.now() - timedelta(hours=24)
                filtered_df = df[df['Timestamp'] >= cutoff]
        elif time_filter == "Last 7 Days":
            if 'Timestamp' in df.columns:
                cutoff = datetime.now() - timedelta(days=7)
                filtered_df = df[df['Timestamp'] >= cutoff]
        elif time_filter == "Last 30 Days":
            if 'Timestamp' in df.columns:
                cutoff = datetime.now() - timedelta(days=30)
                filtered_df = df[df['Timestamp'] >= cutoff]
        elif time_filter == "Last 90 Days":
            if 'Timestamp' in df.columns:
                cutoff = datetime.now() - timedelta(days=90)
                filtered_df = df[df['Timestamp'] >= cutoff]
    else:
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=min_date if min_date else datetime.now().date() - timedelta(days=7),
                min_value=min_date if min_date else datetime(2024, 1, 1),
                max_value=max_date if max_date else datetime.now().date()
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=max_date if max_date else datetime.now().date(),
                min_value=start_date,
                max_value=datetime.now().date()
            )
        
        if 'Timestamp' in df.columns:
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())
            filtered_df = df[(df['Timestamp'] >= start_dt) & (df['Timestamp'] <= end_dt)]
    
    st.markdown(f"📊 Showing **{len(filtered_df)}** records", unsafe_allow_html=True)
    return filtered_df


# =============================================================================
# 2. COMPARISON ANALYTICS
# =============================================================================
def show_comparison_analytics(filtered_df, df):
    """Show comparison between current period and previous period."""
    st.markdown('<div class="section-header">📈 Comparison Analytics</div>', unsafe_allow_html=True)
    
    if 'Timestamp' in filtered_df.columns:
        current_start = filtered_df['Timestamp'].min()
        current_end = filtered_df['Timestamp'].max()
        current_days = (current_end - current_start).days + 1
        
        previous_start = current_start - timedelta(days=current_days)
        previous_end = current_start - timedelta(days=1)
        
        previous_df = df[(df['Timestamp'] >= previous_start) & (df['Timestamp'] <= previous_end)]
        
        current_detections = len(filtered_df)
        previous_detections = len(previous_df)
        
        current_violations = len(filtered_df[filtered_df["Restricted Area Violation"] == "Yes"]) if not filtered_df.empty else 0
        previous_violations = len(previous_df[previous_df["Restricted Area Violation"] == "Yes"]) if not previous_df.empty else 0
        
        current_avg_conf = filtered_df["Confidence"].mean() * 100 if not filtered_df.empty else 0
        previous_avg_conf = previous_df["Confidence"].mean() * 100 if not previous_df.empty else 0
        
        def calc_change(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return ((current - previous) / previous) * 100
        
        det_change = calc_change(current_detections, previous_detections)
        viol_change = calc_change(current_violations, previous_violations)
        conf_change = calc_change(current_avg_conf, previous_avg_conf)
        
        st.markdown("#### Current Period vs Previous Period")
        
        st.markdown(f"""
        <div style="background: rgba(124, 58, 237, 0.1); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
            <strong>Current Period:</strong> {current_start.strftime('%Y-%m-%d')} to {current_end.strftime('%Y-%m-%d')} ({current_days} days)<br>
            <strong>Previous Period:</strong> {previous_start.strftime('%Y-%m-%d')} to {previous_end.strftime('%Y-%m-%d')} ({current_days} days)
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("##### Detections")
            st.metric("Total Detections", f"{current_detections:,}", delta=f"{det_change:+.1f}%", delta_color="normal")
            st.caption(f"Previous: {previous_detections:,}")
        
        with col2:
            st.markdown("##### Violations")
            st.metric("Total Violations", f"{current_violations:,}", delta=f"{viol_change:+.1f}%", delta_color="inverse" if viol_change > 0 else "normal")
            st.caption(f"Previous: {previous_violations:,}")
        
        with col3:
            st.markdown("##### Avg Confidence")
            st.metric("Avg Confidence", f"{current_avg_conf:.1f}%", delta=f"{conf_change:+.1f}%", delta_color="normal")
            st.caption(f"Previous: {previous_avg_conf:.1f}%")
        
        if len(filtered_df) > 1 and len(previous_df) > 1:
            st.markdown("#### Daily Comparison Chart")
            
            filtered_df_copy = filtered_df.copy()
            previous_df_copy = previous_df.copy()
            
            filtered_df_copy['Date'] = pd.to_datetime(filtered_df_copy['Timestamp']).dt.date
            previous_df_copy['Date'] = pd.to_datetime(previous_df_copy['Timestamp']).dt.date
            
            daily_current = filtered_df_copy.groupby('Date').size().reset_index(name='Current')
            daily_previous = previous_df_copy.groupby('Date').size().reset_index(name='Previous')
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=daily_current['Date'], y=daily_current['Current'], name='Current Period', marker_color='#00d4ff'))
            fig.add_trace(go.Bar(x=daily_previous['Date'], y=daily_previous['Previous'], name='Previous Period', marker_color='#7c3aed', opacity=0.7))
            
            fig.update_layout(title="Daily Detections Comparison", xaxis_title="Date", yaxis_title="Number of Detections", barmode='group', template='plotly_dark', height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        return filtered_df
    
    return filtered_df


# =============================================================================
# 3. TREND FORECASTING
# =============================================================================
def show_trend_forecasting(filtered_df):
    """Show trend forecasting using linear regression."""
    st.markdown('<div class="section-header">🔮 Trend Forecasting</div>', unsafe_allow_html=True)
    
    if filtered_df.empty or len(filtered_df) < 3:
        st.info("Not enough data for trend forecasting. Need at least 3 days of data.")
        return
    
    df_copy = filtered_df.copy()
    df_copy['Date'] = pd.to_datetime(df_copy['Timestamp']).dt.date
    daily_counts = df_copy.groupby('Date').size().reset_index(name='Detections')
    daily_counts['Date'] = pd.to_datetime(daily_counts['Date'])
    daily_counts = daily_counts.sort_values('Date')
    
    violation_df = df_copy[df_copy["Restricted Area Violation"] == "Yes"]
    daily_violations = violation_df.groupby('Date').size().reset_index(name='Violations')
    daily_violations['Date'] = pd.to_datetime(daily_violations['Date'])
    
    forecast_df = daily_counts.merge(daily_violations, on='Date', how='left').fillna(0)
    forecast_df['DayNumber'] = (forecast_df['Date'] - forecast_df['Date'].min()).dt.days
    
    forecast_days = st.slider("Forecast Duration (days)", 3, 30, 7)
    
    X = forecast_df['DayNumber'].values.reshape(-1, 1)
    y_detections = forecast_df['Detections'].values
    model_detections = LinearRegression()
    model_detections.fit(X, y_detections)
    
    y_violations = forecast_df['Violations'].values
    model_violations = LinearRegression()
    model_violations.fit(X, y_violations)
    
    last_date = forecast_df['Date'].max()
    future_dates = [last_date + timedelta(days=i+1) for i in range(forecast_days)]
    future_day_numbers = [(d - forecast_df['Date'].min()).days for d in future_dates]
    
    future_X = np.array(future_day_numbers).reshape(-1, 1)
    predicted_detections = model_detections.predict(future_X)
    predicted_violations = model_violations.predict(future_X)
    
    predicted_detections = np.maximum(predicted_detections, 0)
    predicted_violations = np.maximum(predicted_violations, 0)
    
    forecast_result = pd.DataFrame({'Date': future_dates, 'Predicted_Detections': predicted_detections.round(1), 'Predicted_Violations': predicted_violations.round(1)})
    
    det_trend = "📈 Increasing" if model_detections.coef_[0] > 0 else "📉 Decreasing" if model_detections.coef_[0] < 0 else "➡️ Stable"
    viol_trend = "📈 Increasing" if model_violations.coef_[0] > 0 else "📉 Decreasing" if model_violations.coef_[0] < 0 else "➡️ Stable"
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""<div class="glass-card" style="text-align: center; padding: 1.5rem;"><div style="font-size: 2rem;">🎯</div><div style="font-size: 1.5rem; font-weight: bold; color: #00d4ff;">{det_trend}</div><div style="color: #94a3b8;">Detection Trend</div><div style="font-size: 0.9rem; margin-top: 0.5rem;">Slope: {model_detections.coef_[0]:.2f} per day</div></div>""", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""<div class="glass-card" style="text-align: center; padding: 1.5rem;"><div style="font-size: 2rem;">🚨</div><div style="font-size: 1.5rem; font-weight: bold; color: #ef4444;">{viol_trend}</div><div style="color: #94a3b8;">Violation Trend</div><div style="font-size: 0.9rem; margin-top: 0.5rem;">Slope: {model_violations.coef_[0]:.2f} per day</div></div>""", unsafe_allow_html=True)
    
    st.markdown("#### Detection Forecast")
    
    historical_dates = forecast_df['Date'].tolist()
    historical_detections = forecast_df['Detections'].tolist()
    all_dates = historical_dates + future_dates
    all_detections = historical_detections + predicted_detections.tolist()
    types = ['Historical'] * len(historical_dates) + ['Forecast'] * len(future_dates)
    
    plot_df = pd.DataFrame({'Date': all_dates, 'Detections': all_detections, 'Type': types})
    
    fig = px.line(plot_df, x='Date', y='Detections', color='Type', markers=True, color_discrete_map={'Historical': '#00d4ff', 'Forecast': '#f59e0b'})
    
    upper_bound = list(historical_detections) + (predicted_detections * 1.2).tolist()
    lower_bound = list(historical_detections) + (predicted_detections * 0.8).tolist()
    
    fig.add_trace(go.Scatter(x=all_dates + all_dates[::-1], y=upper_bound + lower_bound[::-1], fill='toself', fillcolor='rgba(245, 158, 11, 0.2)', line=dict(color='rgba(255,255,255,0)'), name='Confidence Interval', showlegend=True))
    
    fig.update_layout(title="Detection Trend with Forecast", template='plotly_dark', height=400, xaxis_title="Date", yaxis_title="Predicted Detections")
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("#### Forecast Table")
    st.dataframe(forecast_result, use_container_width=True)
    
    return forecast_result


# =============================================================================
# 4. ANOMALY DETECTION
# =============================================================================
def show_anomaly_detection(filtered_df):
    """Detect and highlight unusual patterns in the data."""
    st.markdown('<div class="section-header">⚠️ Anomaly Detection</div>', unsafe_allow_html=True)
    
    if filtered_df.empty or len(filtered_df) < 5:
        st.info("Not enough data for anomaly detection. Need at least 5 detections.")
        return
    
    df_copy = filtered_df.copy()
    df_copy['Date'] = pd.to_datetime(df_copy['Timestamp']).dt.date
    daily_counts = df_copy.groupby('Date').size().reset_index(name='Count')
    
    mean_count = daily_counts['Count'].mean()
    std_count = daily_counts['Count'].std()
    
    daily_counts['ZScore'] = (daily_counts['Count'] - mean_count) / std_count
    anomalies = daily_counts[abs(daily_counts['ZScore']) > 2]
    
    violation_df = df_copy[df_copy["Restricted Area Violation"] == "Yes"]
    daily_violations = violation_df.groupby('Date').size().reset_index(name='ViolationCount')
    
    if not daily_violations.empty:
        mean_violations = daily_violations['ViolationCount'].mean()
        std_violations = daily_violations['ViolationCount'].std()
        high_violation_days = daily_violations[daily_violations['ViolationCount'] > mean_violations + 2*std_violations]
    else:
        mean_violations = 0
        std_violations = 0
        high_violation_days = pd.DataFrame()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Detection Anomalies")
        if not anomalies.empty:
            st.markdown(f"Found **{len(anomalies)}** unusual days:")
            for _, row in anomalies.iterrows():
                z = row['ZScore']
                direction = "📈 High" if z > 0 else "📉 Low"
                st.markdown(f"""<div style="background: rgba(239, 68, 68, 0.2); padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem;"><strong>{row['Date']}</strong> - {direction} activity ({int(row['Count'])} detections)<br><small style="color: #94a3b8;">Z-Score: {z:.2f}</small></div>""", unsafe_allow_html=True)
        else:
            st.success("✅ No detection anomalies detected!")
    
    with col2:
        st.markdown("#### High Violation Days")
        if not high_violation_days.empty:
            st.markdown(f"Found **{len(high_violation_days)}** high-violation days:")
            for _, row in high_violation_days.iterrows():
                st.markdown(f"""<div style="background: rgba(245, 158, 11, 0.2); padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem;"><strong>{row['Date']}</strong> - {int(row['ViolationCount'])} violations<br><small style="color: #94a3b8;">Above average by {row['ViolationCount'] - mean_violations:.1f}</small></div>""", unsafe_allow_html=True)
        else:
            st.success("✅ No high-violation anomalies detected!")
    
    st.markdown("#### Anomaly Visualization")
    
    fig = go.Figure()
    fig.add_trace(go.Box(y=daily_counts['Count'], name='Daily Detections', marker_color='#00d4ff', boxpoints='all', jitter=0.3))
    
    if not anomalies.empty:
        anomaly_y = anomalies['Count'].tolist()
        fig.add_trace(go.Scatter(x=[0.85] * len(anomaly_y), y=anomaly_y, mode='markers', marker=dict(color='#ef4444', size=12, symbol='x'), name='Anomalies'))
    
    fig.update_layout(title="Daily Detection Distribution (Outliers Marked in Red)", template='plotly_dark', height=350, yaxis_title="Detections per Day")
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("#### Statistical Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Mean Daily", f"{mean_count:.1f}")
    col2.metric("Std Deviation", f"{std_count:.1f}")
    col3.metric("Min Day", f"{daily_counts['Count'].min()}")
    col4.metric("Max Day", f"{daily_counts['Count'].max()}")


# =============================================================================
# 5. PDF REPORT EXPORT
# =============================================================================
def show_pdf_export(filtered_df, df):
    """Generate and export PDF reports."""
    st.markdown('<div class="section-header">📄 PDF Report Export</div>', unsafe_allow_html=True)
    
    report_type = st.selectbox("Select Report Type", ["Summary Report", "Detailed Report", "Violation Report", "Custom Report"])
    
    if 'Timestamp' in filtered_df.columns:
        start_date = filtered_df['Timestamp'].min().strftime('%Y-%m-%d')
        end_date = filtered_df['Timestamp'].max().strftime('%Y-%m-%d')
    else:
        start_date = "N/A"
        end_date = "N/A"
    
    if st.button("📄 Generate PDF Report"):
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_font("Arial", "B", 20)
        pdf.set_text_color(0, 212, 255)
        pdf.cell(0, 10, "Real-Time Intrusion Detection System", ln=True, align="C")
        
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(124, 58, 237)
        pdf.cell(0, 10, f"{report_type}", ln=True, align="C")
        
        pdf.set_font("Arial", size=12)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)
        pdf.cell(0, 10, f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        pdf.cell(0, 10, f"Date Range: {start_date} to {end_date}", ln=True)
        pdf.cell(0, 10, f"Total Records: {len(filtered_df)}", ln=True)
        
        pdf.ln(10)
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(0, 212, 255)
        pdf.cell(0, 10, "Summary Statistics", ln=True)
        
        pdf.set_font("Arial", size=12)
        pdf.set_text_color(0, 0, 0)
        
        total_detections = len(filtered_df)
        total_violations = len(filtered_df[filtered_df["Restricted Area Violation"] == "Yes"]) if not filtered_df.empty else 0
        avg_confidence = filtered_df["Confidence"].mean() * 100 if not filtered_df.empty else 0
        
        pdf.cell(0, 10, f"Total Detections: {total_detections}", ln=True)
        pdf.cell(0, 10, f"Total Violations: {total_violations}", ln=True)
        pdf.cell(0, 10, f"Average Confidence: {avg_confidence:.1f}%", ln=True)
        pdf.cell(0, 10, f"Violation Rate: {(total_violations/total_detections*100) if total_detections > 0 else 0:.1f}%", ln=True)
        
        if not filtered_df.empty:
            pdf.ln(10)
            pdf.set_font("Arial", "B", 14)
            pdf.set_text_color(0, 212, 255)
            pdf.cell(0, 10, "Top Detected Classes", ln=True)
            
            pdf.set_font("Arial", size=12)
            pdf.set_text_color(0, 0, 0)
            
            class_counts = filtered_df["Class"].value_counts().head(5)
            for class_name, count in class_counts.items():
                pdf.cell(0, 10, f"{class_name}: {count} ({count/total_detections*100:.1f}%)", ln=True)
        
        pdf.ln(20)
        pdf.set_font("Arial", "I", 10)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 10, "Generated by Real-Time Intrusion Detection System", ln=True, align="C")
        
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        
        st.download_button(label="📥 Download PDF Report", data=pdf_bytes, file_name=f"intrusion_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", mime="application/pdf")
    
    st.markdown("---")
    st.markdown("#### Quick Data Export")
    
    col1, col2 = st.columns(2)
    with col1:
        csv = filtered_df.to_csv(index=False)
        st.download_button(label="📥 Download Filtered Data (CSV)", data=csv, file_name=f"detection_data_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")


# =============================================================================
# 6. INTERACTIVE CHARTS (PLOTLY)
# =============================================================================
def show_interactive_charts(filtered_df):
    """Show all charts using Plotly for interactivity."""
    st.markdown('<div class="section-header">📊 Interactive Charts</div>', unsafe_allow_html=True)
    
    if filtered_df.empty:
        st.info("No data available for charts.")
        return
    
    df_copy = filtered_df.copy()
    df_copy['Date'] = pd.to_datetime(df_copy['Timestamp']).dt.date
    df_copy['Hour'] = pd.to_datetime(df_copy['Timestamp']).dt.hour
    df_copy['DayOfWeek'] = pd.to_datetime(df_copy['Timestamp']).dt.dayofweek
    df_copy['DayName'] = pd.to_datetime(df_copy['Timestamp']).dt.day_name()
    
    chart_type = st.selectbox("Select Chart Type", ["Detection Trends Over Time", "Class Distribution", "Confidence Distribution", "Hourly Activity Heatmap", "Day of Week Analysis", "Violations Timeline", "Confidence vs Time Scatter"])
    
    if chart_type == "Detection Trends Over Time":
        daily_counts = df_copy.groupby('Date').size().reset_index(name='Detections')
        daily_counts['Date'] = pd.to_datetime(daily_counts['Date'])
        daily_counts = daily_counts.sort_values('Date')
        
        fig = px.line(daily_counts, x='Date', y='Detections', markers=True, title="Detection Trends Over Time (Click and Drag to Zoom)")
        fig.update_traces(line_color='#00d4ff', marker=dict(size=8))
        fig.update_layout(template='plotly_dark', hovermode='x unified', dragmode='zoom')
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 Use mouse to zoom, double-click to reset, hover for details")
    
    elif chart_type == "Class Distribution":
        class_counts = df_copy["Class"].value_counts().reset_index()
        class_counts.columns = ['Class', 'Count']
        
        fig = px.pie(class_counts, values='Count', names='Class', title="Class Distribution", color_discrete_sequence=px.colors.qualitative.Vivid)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Confidence Distribution":
        fig = px.histogram(df_copy, x='Confidence', nbins=20, title="Confidence Score Distribution", color_discrete_sequence=['#22c55e'])
        fig.update_layout(template='plotly_dark', bargap=0.1, xaxis_title="Confidence Score (%)", yaxis_title="Frequency")
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Hourly Activity Heatmap":
        hourly_data = df_copy.groupby(['DayOfWeek', 'Hour']).size().unstack(fill_value=0)
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        hourly_data.index = [day_names[i] for i in hourly_data.index]
        
        fig = px.imshow(hourly_data, labels=dict(x="Hour of Day", y="Day of Week", color="Detections"), x=list(range(24)), y=day_names, color_continuous_scale='Viridis', title="Hourly Activity Heatmap")
        fig.update_layout(template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Day of Week Analysis":
        day_counts = df_copy.groupby('DayName').size().reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']).reset_index()
        day_counts.columns = ['Day', 'Detections']
        
        fig = px.bar(day_counts, x='Day', y='Detections', title="Detections by Day of Week", color='Detections', color_continuous_scale='Bluered')
        fig.update_layout(template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_type == "Violations Timeline":
        violation_df = df_copy[df_copy["Restricted Area Violation"] == "Yes"]
        
        if not violation_df.empty:
            daily_violations = violation_df.groupby('Date').size().reset_index(name='Violations')
            daily_violations['Date'] = pd.to_datetime(daily_violations['Date'])
            daily_violations = daily_violations.sort_values('Date')
            
            fig = px.area(daily_violations, x='Date', y='Violations', title="Violation Timeline", line_color='#ef4444', fillcolor='rgba(239, 68, 68, 0.3)')
            fig.update_layout(template='plotly_dark', hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No violations recorded in the selected period.")
    
    elif chart_type == "Confidence vs Time Scatter":
        fig = px.scatter(df_copy, x='Hour', y='Confidence', color='Class', size='Confidence', title="Confidence vs Hour of Day", opacity=0.7, color_discrete_sequence=px.colors.qualitative.Vivid)
        fig.update_layout(template='plotly_dark', xaxis_title="Hour of Day", yaxis_title="Confidence Score")
        st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# 7. CORRELATION ANALYSIS
# =============================================================================
def show_correlation_analysis(filtered_df):
    """Analyze correlations between different variables."""
    st.markdown('<div class="section-header">🔗 Correlation Analysis</div>', unsafe_allow_html=True)
    
    if filtered_df.empty or len(filtered_df) < 5:
        st.info("Not enough data for correlation analysis.")
        return
    
    df_copy = filtered_df.copy()
    df_copy['Hour'] = pd.to_datetime(df_copy['Timestamp']).dt.hour
    df_copy['DayOfWeek'] = pd.to_datetime(df_copy['Timestamp']).dt.dayofweek
    df_copy['Confidence_Pct'] = df_copy['Confidence'] * 100
    
    corr_data = df_copy[['Confidence_Pct', 'Hour', 'DayOfWeek']].copy()
    corr_data['Violation'] = (df_copy["Restricted Area Violation"] == "Yes").astype(int)
    
    correlation_matrix = corr_data.corr()
    
    st.markdown("#### Correlation Matrix")
    
    fig = px.imshow(correlation_matrix, text_auto='.2f', aspect='auto', color_continuous_scale='RdBu_r', title="Correlation Heatmap")
    fig.update_layout(template='plotly_dark', xaxis_title="Variable", yaxis_title="Variable")
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("#### Detailed Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Confidence vs Hour")
        fig = px.scatter(df_copy, x='Hour', y='Confidence_Pct', trendline='ols', title="Confidence Score by Hour", opacity=0.6, color_discrete_sequence=['#00d4ff'])
        fig.update_layout(template='plotly_dark')
        st.plotly_chart(fig, use_container_width=True)
        
        corr = df_copy['Confidence_Pct'].corr(df_copy['Hour'])
        strength = "Strong" if abs(corr) > 0.5 else "Moderate" if abs(corr) > 0.3 else "Weak"
        direction = "positive" if corr > 0 else "negative"
        st.markdown(f"**Correlation: {corr:.3f}** ({strength} {direction})")
    
    with col2:
        st.markdown("##### Confidence vs Day of Week")
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df_copy['DayName'] = pd.Categorical(df_copy['DayName'], categories=day_order, ordered=True)
        
        fig = px.box(df_copy, x='DayName', y='Confidence_Pct', title="Confidence Distribution by Day", points='all', color='DayName')
        fig.update_layout(template='plotly_dark', showlegend=False, xaxis_title="Day of Week", yaxis_title="Confidence (%)")
        st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# MAIN FUNCTION
# =============================================================================
def show_enhanced_analytics(filtered_df, df):
    """Main function to display all enhanced analytics features."""
    st.markdown("""
    <style>
    .section-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f1f5f9;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(0, 212, 255, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)
    
    analytics_tabs = st.tabs(["📅 Date Range", "📈 Comparison", "🔮 Forecasting", "⚠️ Anomalies", "📄 Export", "📊 Interactive", "🔗 Correlation"])
    
    with analytics_tabs[0]:
        filtered_df = show_date_range_picker(filtered_df)
    
    with analytics_tabs[1]:
        filtered_df = show_comparison_analytics(filtered_df, df)
    
    with analytics_tabs[2]:
        show_trend_forecasting(filtered_df)
    
    with analytics_tabs[3]:
        show_anomaly_detection(filtered_df)
    
    with analytics_tabs[4]:
        show_pdf_export(filtered_df, df)
    
    with analytics_tabs[5]:
        show_interactive_charts(filtered_df)
    
    with analytics_tabs[6]:
        show_correlation_analysis(filtered_df)
    
    return filtered_df

