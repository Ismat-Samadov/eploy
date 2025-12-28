#!/usr/bin/env python3
"""
Healthcare Provider Market Analysis - Chart Generation Script
Generates business intelligence visualizations from medportal.az provider data
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configuration
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10
CHARTS_DIR = Path('charts')
CHARTS_DIR.mkdir(exist_ok=True)

def load_data():
    """Load and prepare the dataset"""
    df = pd.read_csv('doctors_data.csv')
    return df

def save_chart(filename):
    """Save chart with consistent formatting"""
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / filename, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Generated: {filename}")

def chart1_top_specialties(df):
    """Chart 1: Top 15 Medical Specialties - Market Demand Analysis"""
    specialty_counts = df['specialty'].value_counts().head(15)

    fig, ax = plt.subplots(figsize=(12, 8))
    colors = sns.color_palette("viridis", len(specialty_counts))
    bars = ax.barh(range(len(specialty_counts)), specialty_counts.values, color=colors)

    ax.set_yticks(range(len(specialty_counts)))
    ax.set_yticklabels(specialty_counts.index)
    ax.set_xlabel('Number of Providers', fontsize=12, fontweight='bold')
    ax.set_title('Top 15 Healthcare Specialties by Provider Count',
                 fontsize=14, fontweight='bold', pad=20)
    ax.invert_yaxis()

    # Add value labels
    for i, (bar, value) in enumerate(zip(bars, specialty_counts.values)):
        ax.text(value + 1, i, f'{value}', va='center', fontsize=10)

    save_chart('01_top_specialties.png')

def chart2_top_clinics(df):
    """Chart 2: Top 15 Healthcare Facilities - Market Leaders"""
    clinic_counts = df['clinic_name'].value_counts().head(15)

    fig, ax = plt.subplots(figsize=(12, 8))
    colors = sns.color_palette("rocket", len(clinic_counts))
    bars = ax.barh(range(len(clinic_counts)), clinic_counts.values, color=colors)

    ax.set_yticks(range(len(clinic_counts)))
    ax.set_yticklabels(clinic_counts.index)
    ax.set_xlabel('Number of Provider Listings', fontsize=12, fontweight='bold')
    ax.set_title('Top 15 Healthcare Facilities by Provider Listings',
                 fontsize=14, fontweight='bold', pad=20)
    ax.invert_yaxis()

    # Add value labels
    for i, (bar, value) in enumerate(zip(bars, clinic_counts.values)):
        ax.text(value + 1, i, f'{value}', va='center', fontsize=10)

    save_chart('02_top_clinics.png')

def chart3_working_hours(df):
    """Chart 3: Service Availability Patterns - Operating Hours Analysis"""
    working_hours = df['working_hours'].value_counts().head(10)

    fig, ax = plt.subplots(figsize=(12, 7))
    colors = sns.color_palette("mako", len(working_hours))
    bars = ax.bar(range(len(working_hours)), working_hours.values, color=colors)

    ax.set_xticks(range(len(working_hours)))
    ax.set_xticklabels(working_hours.index, rotation=45, ha='right')
    ax.set_ylabel('Number of Providers', fontsize=12, fontweight='bold')
    ax.set_title('Healthcare Provider Availability by Working Schedule',
                 fontsize=14, fontweight='bold', pad=20)

    # Add value labels on bars
    for bar, value in zip(bars, working_hours.values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    save_chart('03_working_hours_pattern.png')

def chart4_data_completeness(df):
    """Chart 4: Data Quality Metrics - Information Completeness"""
    total = len(df)
    completeness = {
        'Phone Number': (df['phone'].notna().sum() / total) * 100,
        'Clinic Name': (df['clinic_name'].notna().sum() / total) * 100,
        'Working Hours': (df['working_hours'].notna().sum() / total) * 100,
        'All Fields': (df[['phone', 'clinic_name', 'working_hours']].notna().all(axis=1).sum() / total) * 100
    }

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#2ecc71', '#3498db', '#f39c12', '#9b59b6']
    bars = ax.bar(completeness.keys(), completeness.values(), color=colors)

    ax.set_ylabel('Completion Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Provider Data Completeness Analysis',
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_ylim(0, 105)
    ax.axhline(y=95, color='red', linestyle='--', alpha=0.3, label='95% Target')

    # Add percentage labels
    for bar, (key, value) in zip(bars, completeness.items()):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax.legend()
    save_chart('04_data_completeness.png')

def chart5_provider_types(df):
    """Chart 5: Healthcare Service Categories - Market Composition"""

    # Categorize specialties into meaningful groups
    def categorize_specialty(specialty):
        specialty_lower = specialty.lower()

        if any(word in specialty_lower for word in ['klinika', 'hospital', 'xəstəxana']):
            return 'Medical Facilities'
        elif any(word in specialty_lower for word in ['uşaq', 'pediatr']):
            return 'Pediatric Services'
        elif any(word in specialty_lower for word in ['qadın', 'doğum', 'ginekoloq', 'mama']):
            return 'Women\'s Health'
        elif any(word in specialty_lower for word in ['stomato', 'dental']):
            return 'Dental Services'
        elif any(word in specialty_lower for word in ['kardio', 'nevro', 'qastro', 'endo']):
            return 'Specialist Care'
        elif any(word in specialty_lower for word in ['cərrah', 'ortoped', 'uroloq']):
            return 'Surgical Services'
        elif any(word in specialty_lower for word in ['oftalmo', 'lor', 'dermato']):
            return 'Diagnostic & Treatment'
        elif any(word in specialty_lower for word in ['laboratoriya', 'radio', 'mrt']):
            return 'Diagnostic Labs'
        else:
            return 'Other Services'

    df['category'] = df['specialty'].apply(categorize_specialty)
    category_counts = df['category'].value_counts()

    fig, ax = plt.subplots(figsize=(12, 7))
    colors = sns.color_palette("Set2", len(category_counts))
    bars = ax.barh(range(len(category_counts)), category_counts.values, color=colors)

    ax.set_yticks(range(len(category_counts)))
    ax.set_yticklabels(category_counts.index)
    ax.set_xlabel('Number of Providers', fontsize=12, fontweight='bold')
    ax.set_title('Healthcare Service Distribution by Category',
                 fontsize=14, fontweight='bold', pad=20)
    ax.invert_yaxis()

    # Add value and percentage labels
    total = category_counts.sum()
    for i, (bar, value) in enumerate(zip(bars, category_counts.values)):
        percentage = (value / total) * 100
        ax.text(value + 2, i, f'{value} ({percentage:.1f}%)',
                va='center', fontsize=10, fontweight='bold')

    save_chart('05_service_categories.png')

def chart6_market_concentration(df):
    """Chart 6: Market Concentration - Provider Distribution Analysis"""

    provider_listing_counts = df['name'].value_counts()

    distribution = {
        'Single Location': (provider_listing_counts == 1).sum(),
        '2-3 Locations': ((provider_listing_counts >= 2) & (provider_listing_counts <= 3)).sum(),
        '4+ Locations': (provider_listing_counts >= 4).sum()
    }

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#3498db', '#e74c3c', '#f39c12']
    bars = ax.bar(distribution.keys(), distribution.values(), color=colors)

    ax.set_ylabel('Number of Providers', fontsize=12, fontweight='bold')
    ax.set_title('Provider Market Presence - Multi-Location Analysis',
                 fontsize=14, fontweight='bold', pad=20)

    # Add value labels
    total_providers = sum(distribution.values())
    for bar, (key, value) in zip(bars, distribution.items()):
        height = bar.get_height()
        percentage = (value / total_providers) * 100
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value}\n({percentage:.1f}%)',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    save_chart('06_market_concentration.png')

def chart7_weekend_availability(df):
    """Chart 7: Weekend Service Availability - Competitive Analysis"""

    def categorize_schedule(hours):
        if pd.isna(hours):
            return 'Not Specified'
        hours_lower = str(hours).lower()

        if 'bazar' in hours_lower and 'şənbə' not in hours_lower:
            return '7 Days/Week'
        elif 'şənbə' in hours_lower:
            return 'Monday-Saturday'
        elif 'cümə' in hours_lower:
            return 'Monday-Friday'
        else:
            return 'Other Schedule'

    df['schedule_type'] = df['working_hours'].apply(categorize_schedule)
    schedule_counts = df['schedule_type'].value_counts()

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = sns.color_palette("coolwarm", len(schedule_counts))
    bars = ax.bar(range(len(schedule_counts)), schedule_counts.values, color=colors)

    ax.set_xticks(range(len(schedule_counts)))
    ax.set_xticklabels(schedule_counts.index, rotation=15, ha='right')
    ax.set_ylabel('Number of Providers', fontsize=12, fontweight='bold')
    ax.set_title('Healthcare Provider Availability by Schedule Type',
                 fontsize=14, fontweight='bold', pad=20)

    # Add value and percentage labels
    total = schedule_counts.sum()
    for bar, value in zip(bars, schedule_counts.values):
        height = bar.get_height()
        percentage = (value / total) * 100
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value}\n({percentage:.1f}%)',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    save_chart('07_weekend_availability.png')

def chart8_specialty_diversity(df):
    """Chart 8: Top Individual Medical Specialties - Specialist Availability"""

    # Filter out facility types, focus on individual medical specialties
    facility_keywords = ['klinika', 'hospital', 'xəstəxana', 'poliklinika',
                         'mərkəz', 'laboratoriya', 'avadanlıq', 'məsləhət', 'doğum']

    specialty_counts = df['specialty'].value_counts()
    individual_specialties = specialty_counts[
        ~specialty_counts.index.str.lower().str.contains('|'.join(facility_keywords))
    ].head(15)

    fig, ax = plt.subplots(figsize=(12, 8))
    colors = sns.color_palette("husl", len(individual_specialties))
    bars = ax.barh(range(len(individual_specialties)), individual_specialties.values, color=colors)

    ax.set_yticks(range(len(individual_specialties)))
    ax.set_yticklabels(individual_specialties.index)
    ax.set_xlabel('Number of Specialists', fontsize=12, fontweight='bold')
    ax.set_title('Top 15 Individual Medical Specialties - Specialist Availability',
                 fontsize=14, fontweight='bold', pad=20)
    ax.invert_yaxis()

    # Add value labels
    for i, (bar, value) in enumerate(zip(bars, individual_specialties.values)):
        ax.text(value + 0.3, i, f'{value}', va='center', fontsize=10)

    save_chart('08_top_individual_specialties.png')

def chart9_contact_availability(df):
    """Chart 9: Contact Information Availability - Communication Channels"""

    contact_metrics = {
        'Complete Info\n(All Fields)': df[['phone', 'clinic_name', 'working_hours']].notna().all(axis=1).sum(),
        'Phone Only': (df['phone'].notna() & (df['clinic_name'].isna() | df['working_hours'].isna())).sum(),
        'Missing Phone': df['phone'].isna().sum(),
        'All Contact Fields': df[['phone', 'clinic_name', 'working_hours']].notna().sum().sum()
    }

    # Calculate actual useful metrics
    total = len(df)
    metrics = {
        'Phone Available': df['phone'].notna().sum(),
        'Clinic Listed': df['clinic_name'].notna().sum(),
        'Hours Listed': df['working_hours'].notna().sum(),
        'Complete Profile': df[['phone', 'clinic_name', 'working_hours']].notna().all(axis=1).sum()
    }

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#27ae60', '#2980b9', '#8e44ad', '#c0392b']
    bars = ax.bar(metrics.keys(), metrics.values(), color=colors)

    ax.set_ylabel('Number of Providers', fontsize=12, fontweight='bold')
    ax.set_title('Provider Contact Information Availability',
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_ylim(0, total + 20)

    # Add count and percentage labels
    for bar, (key, value) in zip(bars, metrics.items()):
        height = bar.get_height()
        percentage = (value / total) * 100
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value}\n({percentage:.1f}%)',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    save_chart('09_contact_availability.png')

def chart10_clinic_size_distribution(df):
    """Chart 10: Clinic Size Distribution - Provider Scale Analysis"""

    clinic_provider_counts = df[df['clinic_name'].notna()]['clinic_name'].value_counts()

    size_distribution = {
        'Small (1-2 providers)': ((clinic_provider_counts >= 1) & (clinic_provider_counts <= 2)).sum(),
        'Medium (3-5 providers)': ((clinic_provider_counts >= 3) & (clinic_provider_counts <= 5)).sum(),
        'Large (6-10 providers)': ((clinic_provider_counts >= 6) & (clinic_provider_counts <= 10)).sum(),
        'Enterprise (11+ providers)': (clinic_provider_counts >= 11).sum()
    }

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#16a085', '#2980b9', '#8e44ad', '#c0392b']
    bars = ax.bar(size_distribution.keys(), size_distribution.values(), color=colors)

    ax.set_ylabel('Number of Clinics', fontsize=12, fontweight='bold')
    ax.set_title('Healthcare Facility Size Distribution',
                 fontsize=14, fontweight='bold', pad=20)

    # Add value labels
    total_clinics = sum(size_distribution.values())
    for bar, (key, value) in zip(bars, size_distribution.items()):
        height = bar.get_height()
        percentage = (value / total_clinics) * 100
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value}\n({percentage:.1f}%)',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    save_chart('10_clinic_size_distribution.png')

def main():
    """Generate all business intelligence charts"""
    print("\n" + "="*60)
    print("HEALTHCARE PROVIDER MARKET ANALYSIS")
    print("Generating Business Intelligence Visualizations")
    print("="*60 + "\n")

    df = load_data()
    print(f"Dataset loaded: {len(df)} provider records\n")

    print("Generating charts...")
    chart1_top_specialties(df)
    chart2_top_clinics(df)
    chart3_working_hours(df)
    chart4_data_completeness(df)
    chart5_provider_types(df)
    chart6_market_concentration(df)
    chart7_weekend_availability(df)
    chart8_specialty_diversity(df)
    chart9_contact_availability(df)
    chart10_clinic_size_distribution(df)

    print("\n" + "="*60)
    print(f"✓ All charts generated successfully in '{CHARTS_DIR}/' directory")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
