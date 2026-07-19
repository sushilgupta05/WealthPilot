import gradio as gr
import time
import random

# ==========================================
# CUSTOM PREMIUM CSS
# ==========================================
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

.gradio-container {
    font-family: 'Inter', sans-serif !important;
    background-color: #f4f7f6;
}
.header-bar {
    background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
    color: white;
    padding: 15px 20px;
    border-radius: 8px;
    margin-bottom: 20px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.header-bar h1 { margin: 0; font-size: 24px; font-weight: 600; color: white !important; }
.header-bar p { margin: 5px 0 0 0; opacity: 0.9; font-size: 14px; }
.telemetry-box {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background-color: #ffffff;
    padding: 10px;
    margin-bottom: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.chat-container {
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    background-color: white;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}
"""

# ==========================================
# MOCK BACKEND LOGIC
# ==========================================
def mock_agent_response(user_message, history):
    message_lower = user_message.lower()
    
    # Trace States
    guardrail_status = "🟢 PASS: Safe"
    cache_status = "⚪ N/A"
    tool_status = "⚪ None"
    rag_context = "⚪ None"
    
    bot_reply = ""

    if "buy" in message_lower or "sell" in message_lower or "bitcoin" in message_lower:
        guardrail_status = "🔴 BLOCKED: Directive Advice / High Risk"
        bot_reply = (
            "I cannot provide definitive buy or sell advice, especially for highly volatile assets like Bitcoin. "
            "Based on your profile, you are a moderate-risk investor. Moving heavily into crypto exceeds your stated risk tolerance.\n\n"
            "---\n*Disclaimer: This information is for educational purposes only. Please consult a licensed professional.*"
        )
        
    elif "fund" in message_lower or "index" in message_lower or "vti" in message_lower:
        rag_context = "📄 SOURCE: VTI Fact Sheet\n- Exp Ratio: 0.03%\n- Class: Equities"
        bot_reply = (
            "Based on the fund fact sheets, Vanguard Total Stock Market ETF (VTI) is a widely used low-cost index fund. "
            "It has an expense ratio of 0.03% and tracks the broader U.S. equity market.\n\n"
            "---\n*Disclaimer: Past performance is not indicative of future results.*"
        )
        
    elif "price" in message_lower:
        tool_status = "🛠️ get_quote('VTI')"
        if random.choice([True, False]):
            cache_status = "⚡ HIT (12ms)"
        else:
            cache_status = "🐢 MISS (1.2s API Call)"
            
        bot_reply = (
            "The current price of VTI is **$265.42**. *(Data is simulated and may be delayed)*.\n\n"
            "---\n*Disclaimer: Educational purposes only.*"
        )
        
    else:
        bot_reply = "I am Finassist. Ask me about fund performance, portfolio allocation, or market prices!"

    return bot_reply, guardrail_status, cache_status, tool_status, rag_context

# ==========================================
# FEEDBACK HANDLER (Inspired by Langfuse Tracing)
# ==========================================
def handle_feedback(data: gr.LikeData):
    """
    Simulates capturing user feedback for observability (thumbs up/down).
    In Week 4, this will send data to Langfuse/your observability platform.
    """
    feedback = "Positive 👍" if data.liked else "Negative 👎"
    print(f"[OBSERVABILITY LOG] User Feedback on message: {feedback}")
    gr.Info(f"Feedback recorded: {feedback}. Traced to session ID.")

# ==========================================
# GRADIO UI LAYOUT
# ==========================================
with gr.Blocks(title="Finassist") as demo:
    
    # Custom Header
    gr.HTML("""
    <div class="header-bar">
        <h1>🧭 Finassist</h1>
        <p>Enterprise Personal Finance Assistant | Secure, Guardrailed, & Traceable</p>
    </div>
    """)
    
    with gr.Row():
        
        # --- LEFT SIDEBAR: Session & Profile ---
        with gr.Column(scale=2):
            gr.Markdown("### 👤 User Profile")
            with gr.Group(elem_classes="telemetry-box"):
                gr.Markdown("**Name:** Marcus Chen\n\n**Risk Tolerance:** Moderate\n\n**Horizon:** Long-term\n\n**Constraints:** <10% Crypto")
            
            gr.Markdown("### 🗂️ Sessions")
            gr.Button("➕ New Chat", size="sm")
            gr.Button("💬 Portfolio Rebalance (Yesterday)", size="sm", variant="secondary")
            gr.Button("💬 401k Setup (Last Week)", size="sm", variant="secondary")
            
        # --- CENTER: Main Chat Interface ---
        with gr.Column(scale=6, elem_classes="chat-container"):
            # Using Gradio 4+ chat features: Avatars and Feedback
            chatbot = gr.Chatbot(
                height=600, 
                show_label=False,
                avatar_images=("static/images/sushil.jpeg", "static/images/finassist_logo.png")
            )
            
            with gr.Row():
                msg = gr.Textbox(
                    placeholder="Message Finassist (e.g., 'What is a good index fund?')...", 
                    show_label=False, 
                    scale=8,
                    container=False
                )
                submit_btn = gr.Button("Send", variant="primary", scale=1, min_width=80)
                
        # --- RIGHT SIDEBAR: Observability & Telemetry ---
        with gr.Column(scale=3):
            gr.Markdown("### 🔍 Observability Trace")
            gr.Markdown("Live telemetry of agent actions. (Visible to Dev/Compliance)")
            
            with gr.Group(elem_classes="telemetry-box"):
                gr.Markdown("**🛡️ Guardrail Layer**")
                guardrail_box = gr.Textbox(show_label=False, value="IDLE", interactive=False, container=False)
                
            with gr.Group(elem_classes="telemetry-box"):
                gr.Markdown("**📚 RAG Retrieval**")
                rag_box = gr.Textbox(show_label=False, value="IDLE", interactive=False, container=False, lines=3)
                
            with gr.Group(elem_classes="telemetry-box"):
                gr.Markdown("**🛠️ Tool Calls (MCP)**")
                tool_box = gr.Textbox(show_label=False, value="IDLE", interactive=False, container=False)
                
            with gr.Group(elem_classes="telemetry-box"):
                gr.Markdown("**💾 Market Data Cache**")
                cache_box = gr.Textbox(show_label=False, value="IDLE", interactive=False, container=False)

    # ==========================================
    # EVENT HANDLING
    # ==========================================
    def process_chat(user_message, history):
        # 1. Append user message immediately
        history.append((user_message, None))
        yield history, gr.update(), gr.update(), gr.update(), gr.update()
        
        # 2. Process Backend
        bot_message, guardrail, cache, tool, rag = mock_agent_response(user_message, history[:-1])
        
        # 3. Stream Response
        history[-1] = (user_message, "")
        for character in bot_message:
            history[-1] = (user_message, history[-1][1] + character)
            time.sleep(0.01) # Simulate generation speed
            yield history, guardrail, cache, tool, rag

    # Wire chat submission
    submit_events = [msg.submit, submit_btn.click]
    for event in submit_events:
        event(
            process_chat, 
            [msg, chatbot], 
            [chatbot, guardrail_box, cache_box, tool_box, rag_box], 
            queue=True
        ).then(
            lambda: "", None, [msg], queue=False # Clear the input box
        )
        
    # Wire Langfuse-style feedback mechanism
    chatbot.like(handle_feedback, None, None)

# Launch with queue enabled for streaming
if __name__ == "__main__":
    demo.launch(
        share=True,
        theme=gr.themes.Default(neutral_hue="slate"),
        css=custom_css
    )