import numpy as np
from fastembed import TextEmbedding

# 1. Our tiny "runbook library".
documents = [
    "Connection pool exhausted: the service cannot get a free database "
    "connection, so requests wait and time out.",
    "The TLS certificate has expired, so clients refuse to connect and "
    "see handshake errors.",
    "Disk is full on the log server, so new log files cannot be written.",
    "DNS lookups are failing, so the service cannot find the hostname "
    "of its dependency.",
]

# 2. A question that shares almost no exact words with the right document.
question = "checkout is slow and the database seems too busy"

# 3. Load a small embedding model (downloads about 130 MB the first time).
model = TextEmbedding("BAAI/bge-small-en-v1.5")

# 4. Turn text into vectors (lists of numbers that represent meaning).
doc_vectors = np.array(list(model.embed(documents)))
question_vector = np.array(list(model.embed([question]))[0])

print(f"Each text becomes {len(question_vector)} numbers.")
print(f"First 5 numbers of the question: {question_vector[:5].round(3)}\n")


# 5. Cosine similarity: closer to 1.0 means closer in meaning.
def cosine(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


scores = [cosine(v, question_vector) for v in doc_vectors]

# 6. Print documents from best match to worst match.
print(f"Question: {question}\n")
for i in np.argsort(scores)[::-1]:
    print(f"{scores[i]:.3f}  {documents[i]}")
