from django.shortcuts import render
import fitz  # PyMuPDF
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import logging

logger = logging.getLogger(__name__)

# Load models
embedder = SentenceTransformer("all-MiniLM-L6-v2")
qa_pipeline = pipeline("text2text-generation", model="google/flan-t5-base")

# Extract text from PDF
def extract_text_from_pdf(pdf_file):
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        return "\n\n".join([page.get_text() for page in doc])

# Clean and split into chunks
def split_context(text):
    return [p.strip() for p in text.split('\n\n') if len(p.strip()) > 30]

# Build FAISS index
def build_faiss_index(embeddings):
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index

# Get top-k relevant chunks using FAISS
def get_top_chunks(question, chunks, embeddings, k=5):
    q_embedding = embedder.encode([question])
    index = build_faiss_index(np.array(embeddings))
    _, indices = index.search(np.array(q_embedding), k)
    return [chunks[i] for i in indices[0]]

# Generate answer using text2text model
def get_best_answer(question, top_chunks):
    context = " ".join(top_chunks)
    prompt = f"Answer the question based on the text below:\n\n{context}\n\nQuestion: {question}"
    try:
        result = qa_pipeline(prompt, max_length=256, do_sample=False)[0]['generated_text']
        return result.strip()
    except Exception as e:
        logger.warning(f"Error in text generation: {e}")
        return "Sorry Shamili, I couldn't generate an answer."

# Main chatbot view
def chatbot_ui(request):
    answer = ""
    context = ""
    chunks = []
    embeddings = []

    if request.method == "POST":
        question = request.POST.get("question", "")
        pdf_file = request.FILES.get("pdf_file")

        if pdf_file:
            context = extract_text_from_pdf(pdf_file)
            chunks = split_context(context)
            embeddings = embedder.encode(chunks).tolist()

            request.session['pdf_context'] = context
            request.session['pdf_chunks'] = chunks
            request.session['pdf_embeddings'] = embeddings
        else:
            context = request.session.get('pdf_context', '')
            chunks = request.session.get('pdf_chunks', [])
            embeddings = request.session.get('pdf_embeddings', [])

        if context and chunks and embeddings:
            np_embeddings = np.array(embeddings)
            top_chunks = get_top_chunks(question, chunks, np_embeddings, k=5)
            answer = get_best_answer(question, top_chunks)
        else:
            q = question.lower()
            if "hi" in q or "hello" in q:
                answer = "Hello Shamili! How can I help you today?"
            elif "your name" in q:
                answer = "I'm your chatbot"
            elif "how are you" in q:
                answer = "I'm good and how are you?"
            elif "bye" in q:
                answer = "Bye Shamili! Come back soon!"
            else:
                answer = "Sorry Shamili, I didn't understand that."

    return render(request, 'chatbot/chat_ui.html', {'answer': answer})
