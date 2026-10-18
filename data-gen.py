import csv
import random
from datetime import datetime, timedelta

# Configuration
NUM_RECORDS = 200
FILENAME = 'students_data.csv'

# Synthetic Data Pools
regions = ['Ariana', 'Tunis', 'Sfax', 'Sousse', 'Mahdia', 'Ben Arous', 'Bizerte']
school_types = ['Middle School', 'High School']
grade_trends = ['stable', 'declining', 'improving']
statuses = ['intake', 'assessment', 'intervention', 'closed']

def generate_random_date():
    start_date = datetime(2026, 1, 1)
    random_days = random.randint(0, 130)
    return (start_date + timedelta(days=random_days)).strftime('%Y-%m-%dT%H:%M:%SZ')

# Generate Data
with open(FILENAME, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    # Write Header
    writer.writerow([
        'student_id', 'region', 'school_type', 'attendance_rate_30_days',
        'grade_trend', 'behavior_notes_count', 'operator_id', 'status', 'recorded_at'
    ])
    
    # Write 200 Rows
    for i in range(1, NUM_RECORDS + 1):
        # Create a mix of healthy records and "at-risk" records
        is_at_risk = random.choice([True, False, False]) # 33% chance of being at risk
        
        student_id = f"STU-2026-{str(i).zfill(3)}"
        region = random.choice(regions)
        school_type = random.choice(school_types)
        
        if is_at_risk:
            attendance = round(random.uniform(50.0, 85.0), 1)
            trend = 'declining'
            behavior = random.randint(2, 6)
            status = random.choice(['assessment', 'intervention'])
        else:
            attendance = round(random.uniform(86.0, 100.0), 1)
            trend = random.choice(['stable', 'improving'])
            behavior = random.randint(0, 1)
            status = random.choice(['intake', 'closed'])
            
        operator_id = random.randint(1, 15)
        recorded_at = generate_random_date()
        
        writer.writerow([
            student_id, region, school_type, attendance,
            trend, behavior, operator_id, status, recorded_at
        ])

print(f"Success: {FILENAME} generated with {NUM_RECORDS} rows.")