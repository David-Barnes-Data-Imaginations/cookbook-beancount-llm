import pandas as pd

# 1. Load the file exactly as the Agent does
filename = "bank_statement.csv" 
df = pd.read_csv(filename)

print(f"📂 File: {filename}")
print(f"📊 Total Rows Detected: {len(df)}")

if len(df) == 300:
    print("❌ DIAGNOSIS: This is the old file! Find your new synthetic CSV.")
elif len(df) > 1000:
    print("✅ DIAGNOSIS: The file is correct. The issue is in the code.")