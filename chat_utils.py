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
    "You are a helpful assistant. Answer concisely and accurately, "
    "using primarily the provided context from the PDF. "
    "For casual or friendly messages (like greetings), respond naturally and empathetically, "
    "even if the content is not in the PDF. "
    "For technical questions, stick closely to the PDF and keep answers brief."
    "If a question requires technical knowledge not present in the PDF, "
    "you may use your own knowledge to answer, but do not go beyond that.\n\n"
    f"PDF Context:\n{context_chunks}\n\n"
    f"Chat History:\n{history_text}\n"
    f"User: {user_input}\nAssistant:"
)






