from memory_tool import MemorySummarizer

# Initialiserer summarizer – trenger ikke lenger sende inn llm
memory_tool = MemorySummarizer()

# Eksempel på samtale
conversation = [
    {"role": "user", "content": "I'm looking for some running shoes."},
    {"role": "assistant", "content": "What kind of terrain or running style?"},
    {"role": "user", "content": "Mostly road running, and I like shoes with good cushioning."},
]

# Oppsummer og lagre samtalen
summary = memory_tool.process_and_save(conversation)

# Print oppsummeringen
print("Saved memory:", summary)

conversation2 = [
    {"role": "user", "content": "I want to test the product in a store."},
    {"role": "assistant", "content": "Where do you live?"},
    {"role": "user", "content": "Trento"},
]

# Oppsummer og lagre samtalen
summary = memory_tool.process_and_save(conversation2)

# Print oppsummeringen
print("Saved memory:", summary)


#Test extraction
summarizer = MemorySummarizer()

# At the start of a new conversation
prior_context = summarizer.load_latest_memory()

if prior_context:
    print("Starting with prior memory:\n", prior_context)
else:
    print("No previous memory found. Starting fresh.")

