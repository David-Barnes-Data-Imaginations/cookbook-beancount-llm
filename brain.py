from beancount import loader
from beancount.core.data import Transaction
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class ContextCompiler:
    def __init__(self, beancount_file):
        print("🧠 Accountant Brain: Loading history...")
        self.history = []
        self.descriptions = []
        self.embeddings = None
        
        # 1. Load the "Gold Standard" history
        self.model = SentenceTransformer('all-MiniLM-L6-v2') # Small, fast model
        self._load_beancount_history(beancount_file)
        
        # 2. Vectorize the history (The "Learning" Phase)
        if self.descriptions:
            print(f"🧠 Accountant Brain: Memorizing {len(self.descriptions)} past transactions...")
            self.embeddings = self.model.encode(self.descriptions)
        else:
            print("⚠️ Warning: No history found in file!")

    def _load_beancount_history(self, filename):
        """Parses the beancount file to find patterns."""
        entries, _, _ = loader.load_file(filename)
        
        for entry in entries:
            if isinstance(entry, Transaction):
                # We combine Payee + Narration for the "search key"
                # Example: "Starbucks Morning Coffee"
                desc = f"{entry.payee or ''} {entry.narration or ''}".strip()
                
                # We find the 'destination' account (usually an Expense or Income)
                # We skip the 'Source' (like Assets:Checking) because that's obvious
                target_account = None
                for posting in entry.postings:
                    # heuristic: usually the one that ISN'T the bank account
                    if not posting.account.startswith("Assets:"):
                        target_account = posting.account
                        break
                
                if desc and target_account:
                    self.history.append({
                        'description': desc,
                        'account': target_account,
                        'full_entry': entry # We might want the full object later
                    })
                    self.descriptions.append(desc)

    def retrieve_context(self, current_payee, current_desc, k=3):
        """
        The ADK 'Context Compiler'. 
        Given a new row, find the k most similar past decisions.
        """
        if self.embeddings is None:
            return "No history available."

        # 1. Embed the CURRENT query
        query_text = f"{current_payee} {current_desc}".strip()
        query_embedding = self.model.encode([query_text])
        
        # 2. Calculate Similarity (Vector Search)
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # 3. Get Top K matches
        # argsort gives lowest-to-highest, so we take the last k and reverse
        top_k_indices = similarities.argsort()[-k:][::-1]
        
        matches = []
        for idx in top_k_indices:
            score = similarities[idx]
            if score > 0.3: # Filter out total garbage matches
                matches.append(self.history[idx])
        
        return self._format_prompt(matches)

    def _format_prompt(self, matches):
        """Formats the retrieved data into an XML block for the LLM."""
        if not matches:
            return "<history>No relevant past transactions found.</history>"
        
        xml_output = "<history>\n"
        xml_output += "  \n"
        for m in matches:
            xml_output += f"  <example>\n"
            xml_output += f"    <description>{m['description']}</description>\n"
            xml_output += f"    <account>{m['account']}</account>\n"
            xml_output += f"  </example>\n"
        xml_output += "</history>"
        return xml_output

# --- Improved Diagnostic Test ---
if __name__ == "__main__":
    import random
    
    filename = "my_accounts.beancount"
    
    # 1. Initialize
    try:
        brain = ContextCompiler(filename)
    except Exception as e:
        print(f"❌ Error initializing brain: {e}")
        exit()

    # 2. Check if we actually learned anything
    if not brain.history:
        print("❌ Error: The brain is empty! It found no transactions in the file.")
        print("   -> Check if 'my_accounts.beancount' actually has transaction data.")
        exit()
    
    print(f"✅ Brain successfully memorized {len(brain.history)} past examples.")

    # 3. Pick a REAL example from the file to test "Recall"
    # We pick a random transaction from history to see if the brain can 'remember' it
    random_memory = random.choice(brain.history)
    real_desc = random_memory['description']
    real_account = random_memory['account']
    
    print(f"\n🧪 Test Case: Asking about a known past event: '{real_desc}'")
    print(f"   (Should map to: {real_account})")
    
    # 4. Run the retrieval
    context = brain.retrieve_context("Query:", real_desc)
    
    print("\n📝 Brain Output:")
    print("---------------------------------------------------")
    print(context)
    print("---------------------------------------------------")