import csv
import re

INPUT_FILE = 'outreach/brevo_import_fixed.csv'
OUTPUT_FILE = 'outreach/brevo_import_final.csv'

def deduplicate_and_clean(input_path, output_path):
    rows = []
    fieldnames = []
    
    try:
        with open(input_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                rows.append(row)
    except FileNotFoundError:
        print(f"Error: {input_path} not found.")
        return

    print(f"Loaded {len(rows)} rows from {input_path}.")

    # 1. Remove exact duplicates (same email and same name/website/etc)
    # We'll use a tuple of all values as the key for uniqueness
    seen_rows = set()
    unique_rows = []
    
    for row in rows:
        # Create a unique identifier for the row based on all its content
        row_tuple = tuple(row.values())
        if row_tuple not in seen_rows:
            seen_rows.add(row_tuple)
            unique_rows.append(row)
    
    print(f"After removing exact duplicates: {len(unique_rows)} rows remaining.")

    # 2. Handle duplicates with different metadata but SAME email
    # If multiple rows have the same email, we want to keep only one.
    # We'll prioritize rows that have more information (e.g., phone, address, etc.)
    email_to_row = {}
    
    for row in unique_rows:
        email = row.get('email', '').strip().lower()
        if not email:
            # If no email, we can't deduplicate by email, so we just keep it for now
            # or we could treat it as a unique entry.
            # Let's add it to a separate list or just keep it.
            # For now, let's just keep it.
            continue
            
        if email not in email_to_row:
            email_to_row[email] = row
        else:
            # We found a duplicate email. Compare current row with existing one.
            existing_row = email_to_row[email]
            
            # Scoring function: more info is better
            def score_row(r):
                score = 0
                for key in r:
                    if r[key] and r[key].strip():
                        score += 1
                return score
            
            if score_row(row) > score_row(existing_row):
                email_to_row[email] = row

    # Reconstruct the list of rows
    # We need to include rows that didn't have an email AND the deduplicated email rows
    final_rows = []
    emails_processed = set()
    
    # First, add the rows that have emails (deduplicated)
    for email, row in email_to_row.items():
        final_rows.append(row)
        emails_processed.add(email)
        
    # Second, add the rows that didn't have an email (from the unique_rows list)
    for row in unique_rows:
        email = row.get('email', '').strip().lower()
        if not email:
            final_rows.append(row)
            
    print(f"After deduplicating by email: {len(final_rows)} rows remaining.")

    # Write to output
    try:
        with open(output_path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(final_rows)
        print(f"Successfully wrote final data to {output_path}.")
    except Exception as e:
        print(f"Error writing to {output_path}: {e}")

if __name__ == "__main__":
    deduplicate_and_clean(INPUT_FILE, OUTPUT_FILE)
