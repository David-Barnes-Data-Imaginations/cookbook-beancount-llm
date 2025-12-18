import csv
import argparse
import hashlib
from beancount import loader
from beancount.core.data import Transaction

def export_to_csv(beancount_file, account_name, output_csv):
    print(f"Loading {beancount_file}...")
    try:
        entries, errors, options = loader.load_file(beancount_file)
    except Exception as e:
        print(f"Critical error loading file: {e}")
        return

    # Filter out any non-critical errors (Beancount is strict!)
    if errors:
        print(f"Note: {len(errors)} errors found in beancount file (often normal for generated data).")

    print(f"Filtering for account: {account_name}...")
    
    headers = ['Date', 'Payee', 'Description', 'Amount', 'Currency', 'Beancount_Id']
    rows = []
    
    for entry in entries:
        if isinstance(entry, Transaction):
            for posting in entry.postings:
                if posting.account == account_name:
                    amount = posting.units.number
                    currency = posting.units.currency
                    date = entry.date
                    payee = entry.payee if entry.payee else ""
                    description = entry.narration if entry.narration else ""
                    
                    # FIX: Create a stable ID by hashing the string representation
                    # We encode it to utf-8 because hashlib expects bytes
                    unique_string = f"{date}{payee}{description}{amount}{account_name}"
                    txn_id = hashlib.md5(unique_string.encode('utf-8')).hexdigest()[:10]

                    rows.append([date, payee, description, amount, currency, txn_id])

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"Success! Exported {len(rows)} transactions to {output_csv}")

if __name__ == "__main__":
    DEFAULT_BEAN = "my_accounts.beancount" 
    DEFAULT_ACCOUNT = "Assets:US:BofA:Checking"
    DEFAULT_OUTPUT = "bank_statement.csv"

    parser = argparse.ArgumentParser(description='Convert Beancount account to Bank CSV')
    parser.add_argument('--file', default=DEFAULT_BEAN, help='Input beancount file')
    parser.add_argument('--account', default=DEFAULT_ACCOUNT, help='Account to extract')
    parser.add_argument('--out', default=DEFAULT_OUTPUT, help='Output CSV file')

    args = parser.parse_args()
    
    export_to_csv(args.file, args.account, args.out)
