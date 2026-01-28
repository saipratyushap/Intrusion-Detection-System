"""
Enhanced Plotly Analytics Module
Provides interactive Plotly-based charts for real-time monitoring analytics
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st


def create_detection_timeline(detection_data):
    """Create interactive line chart for detections over time"""
    if detection_data.empty:
        return go.Figure().add_annotation(text="No detection data available")
    
    df = detection_data.copy()
    
    # Handle various column name options
    date_col = None
    if 'Date' in df.columns:
        date_col = 'Date'
    elif 'datetime' in df.columns:
        date_col = 'datetime'
    elif 'Timestamp' in df.columns:
        date_col = 'Timestamp'
    
    if date_col is None:
        return go.Figure().add_annotation(text="Date/datetime column required")
    
    df[date_col] = pd.to_datetime(df[date_col])
    data_grouped = df.groupby(df[date_col].dt.date).size()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data_grouped.index,
        y=data_grouped.values,
        mode='lines+markers',
        name='Detections',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8),
        hovertemplate='<b>Date:</b> %{x}<br><b>Detections:</b> %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Detection Timeline',
        xaxis_title='Date',
        yaxis_title='Number of Detections',
        hovermode='x unified',
        template='plotly_white',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig


def create_detection_class_bar_chart(detection_data):
    """Create interactive bar chart for detection classes"""
    if detection_data.empty:
        return go.Figure().add_annotation(text="No class data available")
    
    # Handle column name variations
    class_col = 'Class' if 'Class' in detection_data.columns else 'class'
    
    if class_col not in detection_data.columns:
        return go.Figure().add_annotation(text="Class column not found")
    
    class_counts = detection_data[class_col].value_counts()
    
    fig = go.Figure(data=[
        go.Bar(
            x=class_counts.index,
            y=class_counts.values,
            marker=dict(
                color=class_counts.values,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title='Count')
            ),
            hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title='Detection Classes Distribution',
        xaxis_title='Class',
        yaxis_title='Count',
        hovermode='x',
        template='plotly_white',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig


def create_confidence_distribution(detection_data):
    """Create interactive histogram for confidence scores"""
    if detection_data.empty:
        return go.Figure().add_annotation(text="No confidence data available")
    
    # Handle column name variations
    conf_col = 'Confidence' if 'Confidence' in detection_data.columns else 'confidence'
    
    if conf_col not in detection_data.columns:
        return go.Figure().add_annotation(text="Confidence column not found")
    
    fig = go.Figure(data=[
        go.Histogram(
            x=detection_data[conf_col],
            nbinsx=20,
            marker=dict(color='#ff7f0e'),
            hovertemplate='<b>Confidence Range:</b> %{x}<br><b>Count:</b> %{y}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title='Confidence Score Distribution',
        xaxis_title='Confidence Score',
        yaxis_title='Frequency',
        hovermode='x',
        template='plotly_white',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig


def create_detection_heatmap(detection_data, time_period='hourly'):
    """Create heatmap showing detection patterns over time"""
    if detection_data.empty:
        return go.Figure().add_annotation(text="No data for heatmap")
    
    # Create a copy to avoid modifying original
    df = detection_data.copy()
    
    # Handle column name variations
    date_col = None
    hour_col = None
    
    if 'Date' in df.columns:
        date_col = 'Date'
    elif 'datetime' in df.columns:
        date_col = 'datetime'
    elif 'Timestamp' in df.columns:
        date_col = 'Timestamp'
    
    if 'Hour' in df.columns:
        hour_col = 'Hour'
    elif 'hour' in df.columns:
        hour_col = 'hour'
    
    if date_col is None or hour_col is None:
        return go.Figure().add_annotation(text="Date and Hour columns required for heatmap")
    
    df[date_col] = pd.to_datetime(df[date_col])
    df['heatmap_date'] = df[date_col].dt.date
    df['heatmap_hour'] = df[hour_col]
    
    heatmap_data = df.groupby(['heatmap_date', 'heatmap_hour']).size().unstack(fill_value=0)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=[str(d) for d in heatmap_data.index],
        colorscale='YlOrRd',
        hovertemplate='<b>Date:</b> %{y}<br><b>Hour:</b> %{x}:00<br><b>Detections:</b> %{z}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Detection Heatmap (Hour vs Date)',
        xaxis_title='Hour of Day',
        yaxis_title='Date',
        height=500,
        margin=dict(l=100, r=50, t=50, b=50)
    )
    
    return fig


def create_detection_radar_chart(detection_data):
    """Create radar chart for multi-class detection comparison"""
    if detection_data.empty:
        return go.Figure().add_annotation(text="No class data available")
    
    # Handle column name variations
    class_col = 'Class' if 'Class' in detection_data.columns else 'class'
    
    if class_col not in detection_data.columns:
        return go.Figure().add_annotation(text="Class column not found")
    
    class_counts = detection_data[class_col].value_counts()
    
    fig = go.Figure(data=go.Scatterpolar(
        r=class_counts.values,
        theta=class_counts.index,
        fill='toself',
        marker=dict(size=8),
        hovertemplate='<b>%{theta}</b><br>Count: %{r}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Detection Classes - Radar View',
        polar=dict(radialaxis=dict(visible=True)),
        height=500,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig


def create_confidence_gauge(current_confidence, label="Average Confidence"):
    """Create gauge chart for confidence score"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=current_confidence * 100,
        title={'text': label},
        delta={'reference': 80},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': 'darkblue'},
            'steps': [
                {'range': [0, 50], 'color': 'lightgray'},
                {'range': [50, 80], 'color': 'gray'}
            ],
            'threshold': {
                'line': {'color': 'red', 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig


def create_class_confidence_box_plot(detection_data):
    """Create box plot comparing confidence scores by class"""
    if detection_data.empty:
        return go.Figure().add_annotation(text="No data for box plot")
    
    # Handle column name variations
    class_col = 'Class' if 'Class' in detection_data.columns else 'class'
    conf_col = 'Confidence' if 'Confidence' in detection_data.columns else 'confidence'
    
    if class_col not in detection_data.columns or conf_col not in detection_data.columns:
        return go.Figure().add_annotation(text="Class and Confidence columns required")
    
    fig = go.Figure()
    
    for class_name in detection_data[class_col].unique():
        class_data = detection_data[detection_data[class_col] == class_name][conf_col]
        fig.add_trace(go.Box(
            y=class_data,
            name=str(class_name),
            boxmean='sd'
        ))
    
    fig.update_layout(
        title='Confidence Score Distribution by Class',
        yaxis_title='Confidence Score',
        xaxis_title='Class',
        hovermode='y unified',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig


def create_detection_pie_chart(detection_data):
    """Create pie chart for class distribution"""
    if detection_data.empty:
        return go.Figure().add_annotation(text="No class data available")
    
    # Handle column name variations
    class_col = 'Class' if 'Class' in detection_data.columns else 'class'
    
    if class_col not in detection_data.columns:
        return go.Figure().add_annotation(text="Class column not found")
    
    class_counts = detection_data[class_col].value_counts()
    
    fig = go.Figure(data=[go.Pie(
        labels=class_counts.index,
        values=class_counts.values,
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title='Detection Classes Distribution (Pie)',
        height=500,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig


def create_detection_scatter_plot(detection_data):
    """Create scatter plot of confidence vs detection count"""
    if detection_data.empty:
        return go.Figure().add_annotation(text="No data for scatter plot")
    
    df = detection_data.copy()
    
    # Handle column name variations
    conf_col = 'Confidence' if 'Confidence' in df.columns else 'confidence'
    class_col = 'Class' if 'Class' in df.columns else 'class'
    
    date_col = None
    if 'Timestamp' in df.columns:
        date_col = 'Timestamp'
    elif 'datetime' in df.columns:
        date_col = 'datetime'
    elif 'Date' in df.columns:
        date_col = 'Date'
    
    if conf_col not in df.columns or date_col is None:
        return go.Figure().add_annotation(text="Confidence and datetime columns required")
    
    df[date_col] = pd.to_datetime(df[date_col])
    
    fig = go.Figure(data=go.Scatter(
        x=df[date_col],
        y=df[conf_col],
        mode='markers',
        marker=dict(
            size=8,
            color=df[conf_col],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title='Confidence')
        ),
        text=[f"Class: {c}" for c in df.get(class_col, ['N/A'] * len(df))],
        hovertemplate='<b>Time:</b> %{x}<br><b>Confidence:</b> %{y:.3f}<br>%{text}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Detection Confidence Over Time',
        xaxis_title='Time',
        yaxis_title='Confidence Score',
        hovermode='closest',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig


def create_hourly_trend(detection_data):
    """Create line chart showing hourly detection trends"""
    if detection_data.empty:
        return go.Figure().add_annotation(text="No data for hourly trend")
    
    df = detection_data.copy()
    
    # Handle column name variations
    hour_col = None
    if 'Hour' in df.columns:
        hour_col = 'Hour'
    elif 'hour' in df.columns:
        hour_col = 'hour'
    else:
        # Try to extract from datetime
        date_col = None
        if 'Timestamp' in df.columns:
            date_col = 'Timestamp'
        elif 'datetime' in df.columns:
            date_col = 'datetime'
        elif 'Date' in df.columns:
            date_col = 'Date'
        
        if date_col is None:
            return go.Figure().add_annotation(text="Hour or datetime column required")
        
        df[date_col] = pd.to_datetime(df[date_col])
        df['hour_tmp'] = df[date_col].dt.hour
        hour_col = 'hour_tmp'
    
    hourly_counts = df.groupby(hour_col).size()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hourly_counts.index,
        y=hourly_counts.values,
        mode='lines+markers',
        name='Detections',
        line=dict(color='#2ca02c', width=3),
        fill='tozeroy',
        hovertemplate='<b>Hour:</b> %{x}:00<br><b>Detections:</b> %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Hourly Detection Trend',
        xaxis_title='Hour of Day',
        yaxis_title='Number of Detections',
        hovermode='x unified',
        template='plotly_white',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50),
        xaxis=dict(
            tickmode='linear',
            tick0=0,
            dtick=1
        )
    )
    
    return fig


def create_daily_trend(detection_data):
    """Create line chart showing daily detection trends"""
    if detection_data.empty:
        return go.Figure().add_annotation(text="No data for daily trend")
    
    df = detection_data.copy()
    
    # Handle column name variations
    date_col = None
    if 'Date' in df.columns:
        date_col = 'Date'
    elif 'datetime' in df.columns:
        date_col = 'datetime'
    elif 'Timestamp' in df.columns:
        date_col = 'Timestamp'
    
    if date_col is None:
        return go.Figure().add_annotation(text="Date or datetime column required")
    
    df[date_col] = pd.to_datetime(df[date_col])
    daily_counts = df.groupby(df[date_col].dt.date).size()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_counts.index,
        y=daily_counts.values,
        mode='lines+markers',
        name='Detections',
        line=dict(color='#d62728', width=3),
        marker=dict(size=8),
        hovertemplate='<b>Date:</b> %{x}<br><b>Detections:</b> %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Daily Detection Trend',
        xaxis_title='Date',
        yaxis_title='Number of Detections',
        hovermode='x unified',
        template='plotly_white',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig


def create_class_timeline(detection_data):
    """Create stacked area chart showing class distribution over time"""
    if detection_data.empty:
        return go.Figure().add_annotation(text="No class data available")
    
    df = detection_data.copy()
    
    # Handle column name variations
    class_col = 'Class' if 'Class' in df.columns else 'class'
    
    date_col = None
    if 'Date' in df.columns:
        date_col = 'Date'
    elif 'datetime' in df.columns:
        date_col = 'datetime'
    elif 'Timestamp' in df.columns:
        date_col = 'Timestamp'
    
    if class_col not in df.columns or date_col is None:
        return go.Figure().add_annotation(text="Class and Date columns required")
    
    df[date_col] = pd.to_datetime(df[date_col])
    df['date_tmp'] = df[date_col].dt.date
    
    class_timeline = df.groupby(['date_tmp', class_col]).size().unstack(fill_value=0)
    
    fig = go.Figure()
    
    for class_name in class_timeline.columns:
        fig.add_trace(go.Scatter(
            x=class_timeline.index,
            y=class_timeline[class_name],
            mode='lines',
            name=str(class_name),
            stackgroup='one',
            hovertemplate='<b>Date:</b> %{x}<br><b>' + str(class_name) + ':</b> %{y}<extra></extra>'
        ))
    
    fig.update_layout(
        title='Detection Classes Timeline (Stacked)',
        xaxis_title='Date',
        yaxis_title='Number of Detections',
        hovermode='x unified',
        template='plotly_white',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig


def create_comparison_dashboard(detection_data, metric1='class', metric2='confidence'):
    """Create a comparison dashboard with multiple metrics"""
    if detection_data.empty:
        return go.Figure().add_annotation(text="No data available")
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Class Distribution', 'Confidence Distribution', 'Hourly Trend', 'Daily Trend'),
        specs=[[{'type': 'bar'}, {'type': 'histogram'}],
               [{'type': 'scatter'}, {'type': 'scatter'}]]
    )
    
    # Class distribution
    class_counts = detection_data['class'].value_counts()
    fig.add_trace(
        go.Bar(x=class_counts.index, y=class_counts.values, name='Classes'),
        row=1, col=1
    )
    
    # Confidence distribution
    fig.add_trace(
        go.Histogram(x=detection_data['confidence'], name='Confidence', nbinsx=20),
        row=1, col=2
    )
    
    # Hourly trend
    detection_data['datetime'] = pd.to_datetime(detection_data['datetime'])
    detection_data['hour'] = detection_data['datetime'].dt.hour
    hourly = detection_data.groupby('hour').size()
    fig.add_trace(
        go.Scatter(x=hourly.index, y=hourly.values, mode='lines+markers', name='Hourly'),
        row=2, col=1
    )
    
    # Daily trend
    detection_data['date'] = detection_data['datetime'].dt.date
    daily = detection_data.groupby('date').size()
    fig.add_trace(
        go.Scatter(x=daily.index, y=daily.values, mode='lines+markers', name='Daily'),
        row=2, col=2
    )
    
    fig.update_xaxes(title_text='Class', row=1, col=1)
    fig.update_xaxes(title_text='Confidence', row=1, col=2)
    fig.update_xaxes(title_text='Hour', row=2, col=1)
    fig.update_xaxes(title_text='Date', row=2, col=2)
    
    fig.update_yaxes(title_text='Count', row=1, col=1)
    fig.update_yaxes(title_text='Frequency', row=1, col=2)
    fig.update_yaxes(title_text='Detections', row=2, col=1)
    fig.update_yaxes(title_text='Detections', row=2, col=2)
    
    fig.update_layout(
        height=800,
        showlegend=True,
        title_text='Analytics Dashboard',
        template='plotly_white'
    )
    
    return fig
