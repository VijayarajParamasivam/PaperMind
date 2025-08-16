def build_context_chunks(results):
    answers = results['documents']
    return "\n".join([item for sublist in answers for item in sublist])

def build_history_text(history):
    history_text = ""
    for role, msg in history:
        if role == "user":
            history_text += f"User: {msg}\n"
        else:
            history_text += f"Assistant: {msg}\n"
    return history_text

def build_prompt(context_chunks, history_text, user_input):
    return (
        "You are a helpful assistant. Answer as briefly and directly as possible, "
        "using only the provided context from the PDF. If the answer is not in the context, say so.\n\n"
        f"PDF Context:\n{context_chunks}\n\n"
        f"Chat History:\n{history_text}\n"
        f"User: {user_input}\nAssistant:"
    )
