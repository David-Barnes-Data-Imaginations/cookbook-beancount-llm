import pandas as pd
import uuid

INPUT_FILE = "bank_statement_sft.csv"
OUTPUT_FILE = "bank_statement_sft_randomized.csv"

def main():
    print(f"📖 Reading {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    
    # Generate new random IDs (using first 10 chars of UUID for similar format)
    print(f"🎲 Randomizing {len(df)} Beancount_Id values...")
    df['Beancount_Id'] = [uuid.uuid4().hex[:10] for _ in range(len(df))]
    
    # Save to new file
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Saved to {OUTPUT_FILE}")
    print(f"🔍 Sample new IDs: {df['Beancount_Id'].head(3).tolist()}")

if __name__ == "__main__":
    main()
