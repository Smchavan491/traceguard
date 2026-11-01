from app.answer import Answer, build_system_prompt, check_citations, parse_answer
from app.llm import ask_llm


def answer_alert(alert_text, search, ask=ask_llm):
    # Step 1: the Finder looks for runbook pieces that match the alert.
    chunks = search(alert_text)

    # Step 2: if nothing was found, stop here. Don't call Gemini with no evidence.
    if not chunks:
        return Answer(
            answer="Not enough evidence.",
            cited_chunk_ids=[],
            sufficient_evidence=False,
        )

    # Step 3: the Packer writes the rules and labels each piece with its ID.
    prompt = build_system_prompt(chunks)

    # Step 4: the Caller sends the prompt and the alert to Gemini.
    raw_reply = ask(prompt, alert_text)

    # Step 5: the Cleaner cuts out the JSON and checks its shape.
    answer = parse_answer(raw_reply)

    # Step 6: the Inspector checks that every cited ID was really retrieved.
    retrieved_ids = {chunk_id for chunk_id, _ in chunks}
    check_citations(answer, retrieved_ids)

    # Everything passed, so hand back the answer.
    return answer