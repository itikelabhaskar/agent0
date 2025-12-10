"""
Seed test data with planted data quality issues
Covers: missing DOB, negative payments, invalid formats, duplicates, date inconsistencies
"""
import pandas as pd
from datetime import datetime, timedelta
import random
import uuid

def generate_customers_with_issues(n=100):
    """
    Generate customer data with planted DQ issues:
    - Missing DOB (20%)
    - Invalid email formats (10%)
    - Duplicate records (5%)
    - Future DOB dates (5%)
    - Invalid phone formats (10%)
    """
    customers = []
    used_ids = set()
    
    for i in range(n):
        cus_id = f"CUS{i+1:05d}"
        
        # 5% chance of duplicate ID
        if random.random() < 0.05 and len(used_ids) > 10:
            cus_id = random.choice(list(used_ids))
        else:
            used_ids.add(cus_id)
        
        # Generate base data
        forename = random.choice(['John', 'Jane', 'Bob', 'Alice', 'Charlie', 'Diana'])
        surname = random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Davis'])
        
        # 20% missing DOB
        if random.random() < 0.20:
            dob = None
        # 5% future DOB (invalid)
        elif random.random() < 0.05:
            dob = (datetime.now() + timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d')
        else:
            # Valid DOB between 1940-2005
            days_old = random.randint(18*365, 80*365)
            dob = (datetime.now() - timedelta(days=days_old)).strftime('%Y-%m-%d')
        
        # 10% invalid email format
        if random.random() < 0.10:
            email = f"{forename.lower()}{surname.lower()}@@@invalid"
        else:
            email = f"{forename.lower()}.{surname.lower()}@example.com"
        
        # 10% invalid phone format
        if random.random() < 0.10:
            phone = "INVALID"
        else:
            phone = f"+1-555-{random.randint(100,999)}-{random.randint(1000,9999)}"
        
        customers.append({
            'CUS_ID': cus_id,
            'CUS_FORNAME': forename,
            'CUS_SURNAME': surname,
            'CUS_DOB': dob,
            'email': email,
            'phone': phone,
            'created_date': datetime.now().strftime('%Y-%m-%d')
        })
    
    return pd.DataFrame(customers)

def generate_holdings_with_issues(customers_df, n_holdings=300):
    """
    Generate holdings data with planted DQ issues:
    - Negative amounts (10%)
    - Missing customer references (5%)
    - Invalid date formats (5%)
    - Negative premiums (8%)
    - Extreme outliers (3%)
    """
    holdings = []
    customer_ids = customers_df['CUS_ID'].tolist()
    
    for i in range(n_holdings):
        # 5% chance of orphaned/missing customer reference
        if random.random() < 0.05:
            customer_id = f"CUS99999"  # Non-existent customer
        else:
            customer_id = random.choice(customer_ids)
        
        # 10% chance of negative transaction amount
        if random.random() < 0.10:
            tran_amt = -random.uniform(100, 5000)
        # 3% chance of extreme outlier
        elif random.random() < 0.03:
            tran_amt = random.uniform(1000000, 10000000)
        else:
            tran_amt = random.uniform(100, 50000)
        
        # 8% chance of negative premium
        if random.random() < 0.08:
            gross_pmt = -random.uniform(50, 2000)
        else:
            gross_pmt = random.uniform(50, 5000)
        
        # 5% chance of invalid date
        if random.random() < 0.05:
            effective_date = "INVALID_DATE"
        else:
            days_ago = random.randint(0, 730)
            effective_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        holdings.append({
            'holding_id': str(uuid.uuid4())[:8],
            'customer_id': customer_id,
            'holding_amount': round(tran_amt, 2),
            'UNT_TRAN_AMT': round(tran_amt, 2),
            'POLI_GROSS_PMT': round(gross_pmt, 2),
            'effective_date': effective_date,
            'status': random.choice(['active', 'pending', 'closed']),
            'created_ts': datetime.now().isoformat()
        })
    
    return pd.DataFrame(holdings)

def main():
    """Generate and save test datasets"""
    print("🌱 Generating seed data with planted DQ issues...")
    
    # Generate customers
    customers_df = generate_customers_with_issues(n=100)
    print(f"✅ Generated {len(customers_df)} customer records")
    
    # Count issues
    missing_dob = customers_df['CUS_DOB'].isna().sum()
    invalid_emails = customers_df['email'].str.contains('@@@').sum()
    duplicates = len(customers_df) - customers_df['CUS_ID'].nunique()
    
    print(f"   📊 Planted issues:")
    print(f"      - Missing DOB: {missing_dob}")
    print(f"      - Invalid emails: {invalid_emails}")
    print(f"      - Duplicate IDs: {duplicates}")
    
    # Generate holdings
    holdings_df = generate_holdings_with_issues(customers_df, n_holdings=300)
    print(f"✅ Generated {len(holdings_df)} holdings records")
    
    # Count issues
    negative_amounts = (holdings_df['holding_amount'] < 0).sum()
    negative_premiums = (holdings_df['POLI_GROSS_PMT'] < 0).sum()
    invalid_dates = (holdings_df['effective_date'] == 'INVALID_DATE').sum()
    orphaned = (~holdings_df['customer_id'].isin(customers_df['CUS_ID'])).sum()
    
    print(f"   📊 Planted issues:")
    print(f"      - Negative amounts: {negative_amounts}")
    print(f"      - Negative premiums: {negative_premiums}")
    print(f"      - Invalid dates: {invalid_dates}")
    print(f"      - Orphaned records: {orphaned}")
    
    # Save to CSV
    customers_df.to_csv('fake_data/customers_sample.csv', index=False)
    holdings_df.to_csv('fake_data/holdings_sample.csv', index=False)
    
    print(f"\n💾 Saved to:")
    print(f"   - fake_data/customers_sample.csv")
    print(f"   - fake_data/holdings_sample.csv")
    
    print(f"\n📤 To load into BigQuery:")
    print(f"   bq load --autodetect --source_format=CSV \\")
    print(f"     hackathon-practice-480508:dev_dataset.customers \\")
    print(f"     fake_data/customers_sample.csv")
    print(f"   ")
    print(f"   bq load --autodetect --source_format=CSV \\")
    print(f"     hackathon-practice-480508:dev_dataset.holdings \\")
    print(f"     fake_data/holdings_sample.csv")

if __name__ == "__main__":
    main()

