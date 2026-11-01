def fake_search(query):
    return [("rb-1", "Check pool size.")]

def run(query, search):
    return search(query)

print(run("checkout is slow", fake_search))