import json

with open("data/json/postsft_data_246.json", "r") as f:
    data = json.load(f)

count = 0
for row in data:
    if "### Analysis" in row['text'] or "**Analysis:**" in row['text']:
        count += 1

print(f"🕵️‍♂️ Found {count} records with hidden Analysis footers out of {len(data)}")