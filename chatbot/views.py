from django.shortcuts import render

def chatbot_ui(request):
    answer = ""
    if request.method == "POST":
        question = request.POST.get('question', '').lower()
        if "hi" in question or "hello" in question:
            answer = "Hello Shamili! How can I help you today?"
        elif "your name" in question:
            answer = "I'm your chatbot"
        elif "how are you" in question:
            answer = "I'm good and how are you?"
        elif "bye" in question:
            answer = "Bye Shamili! Come back soon!"
        else:
            answer = "Sorry Shamili, I didn't understand that"
    return render(request, 'chatbot/chat_ui.html', {'answer': answer})
