import csv
import json
import random
from datetime import datetime, timedelta
from faker import Faker

# Initialize Faker
fake = Faker('en_GB')  # UK context for your Guildford connection

def generate_b2b_invoices(num_invoices=50):
    invoices = []
    
    # 1. Setup some "Fixed" Vendors to mimic a real firm's repeated suppliers
    vendors = []
    for _ in range(10):
        vendors.append({
            "name": fake.company(),
            "address": fake.address().replace('\n', ', '),
            "tax_id": f"GB{fake.random_number(digits=9)}"
        })

    # 2. Setup some service types (for line items)
    services = [
        ("Consulting", 500, 2000),
        ("Server Hosting", 100, 5000),
        ("Software License", 50, 300),
        ("Audit Services", 1000, 5000),
        ("Legal Retainer", 500, 1500),
        ("Office Supplies", 10, 200),
        ("IT Services", 50, 200),
        ("Marketing Agency", 100, 5000),
        ("Recruitment Agency - Temporary", 500, 40000),
        ("Recruitment Agency - Permanent", 500, 40000),
        ("Accounting", 100, 5000),
        ("Staff Compensation", 500, 2000),
        ("Travel", 500, 2000),
        ("Office ", 500, 2000),
        ("Legal ", 500, 2000),
        ("Catering ", 500, 2000),
        ("Building ", 500, 2000),
        ("Insurance ", 500, 2000),
        ("Telecommunications ", 500, 2000),
        ("Printing ", 500, 2000),
        ("Postage ", 500, 2000),
        ("Hardware", 500, 2000),
    ]
        
    for _ in range(num_invoices):
        # Pick a random vendor
        vendor = random.choice(vendors)
        
        invoice_date = fake.date_between(start_date='-1y', end_date='today')
        due_date = invoice_date + timedelta(days=30)
        
        invoice_id = f"INV-{fake.random_number(digits=6)}"
        
        # Generate 1 to 5 line items per invoice
        line_items = []
        subtotal = 0.0
        
        for _ in range(random.randint(1, 5)):
            service_name, min_price, max_price = random.choice(services)
            qty = random.randint(1, 10)
            unit_price = round(random.uniform(min_price, max_price), 2)
            line_total = round(qty * unit_price, 2)
            
            subtotal += line_total
            
            line_items.append({
                "description": f"{service_name} - {fake.catch_phrase()}",
                "quantity": qty,
                "unit_price": unit_price,
                "line_total": line_total
            })
            
        # Calculate Tax (20% VAT)
        tax_rate = 0.20
        tax_amount = round(subtotal * tax_rate, 2)
        total_amount = round(subtotal + tax_amount, 2)

        # Structure the data
        invoice_record = {
            "invoice_id": invoice_id,
            "date": invoice_date.isoformat(),
            "due_date": due_date.isoformat(),
            "vendor_name": vendor['name'],
            "vendor_address": vendor['address'],
            "vendor_tax_id": vendor['tax_id'],
            "customer_name": fake.company(),
            "line_items": line_items,
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "currency": "GBP"
        }
        invoices.append(invoice_record)

    return invoices

def save_to_csv(invoices, filename="synthetic_b2b_invoices.csv"):
    # Flattening the data for CSV (repeating header info for each line item)
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Header matches a standard "Export" format
        writer.writerow([
        "Invoice_ID", "Date", "Vendor", "Customer", 
        "Description", "Quantity", "Unit_Price", "Line_Total", 
        "Invoice_Subtotal", "Invoice_Tax", "Invoice_Total"
    ])
    
        for inv in invoices:
            for item in inv['line_items']:
                writer.writerow([
                    inv['invoice_id'],
                    inv['date'],
                    inv['vendor_name'],
                    inv['customer_name'],
                    item['description'],
                    item['quantity'],
                    item['unit_price'],
                    item['line_total'],
                    inv['subtotal'],
                    inv['tax_amount'],
                    inv['total_amount']
                ])
    print(f"Saved {len(invoices)} invoices to {filename}")

# Run it
data = generate_b2b_invoices(100)
save_to_csv(data)

# Optional: Save JSON if you want to train an Agent to read the whole structure later
with open("synthetic_b2b_invoices.json", "w") as f:
    json.dump(data, f, indent=2)