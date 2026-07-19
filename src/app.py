"""
Finassist — Premium Gradio Chat UI
A beautiful, personalized financial assistant UI with:
- User profile sidebar (Sushil)
- Streaming chat interface with RAG-grounded responses
- Live observability trace panel
- Dark navy + gold premium design system
"""
import time
import base64
from pathlib import Path
import gradio as gr
from src.rag_engine import RAGEngine
from src.user_profile_loader import get_user_profile, get_portfolio_summary
from src.config import format_inr

def get_image_base64(rel_path: str) -> str:
    """Read a local image and return its data URI (base64) for instant rendering in HTML."""
    img_path = Path(__file__).resolve().parent.parent / rel_path
    if not img_path.exists():
        return ""
    mime_type = "image/png" if img_path.suffix.lower() == ".png" else "image/jpeg"
    encoded = base64.b64encode(img_path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"

def get_image_absolute_path(rel_path: str) -> str:
    """Return absolute file path string for Gradio components (e.g. Chatbot avatars)."""
    img_path = Path(__file__).resolve().parent.parent / rel_path
    return str(img_path.resolve()) if img_path.exists() else ""

# ══════════════════════════════════════════════════════════════════════════
# PREMIUM DESIGN SYSTEM — Dark Navy + Gold + Glassmorphism
# ══════════════════════════════════════════════════════════════════════════
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ─── Global Reset ─── */
.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: linear-gradient(135deg, #0a0e27 0%, #131842 40%, #1a1f4e 70%, #0f1235 100%) !important;
    min-height: 100vh;
}
.gradio-container .main {
    max-width: 1600px !important;
}

/* ─── Header Bar ─── */
.finassist-header {
    background: linear-gradient(135deg, rgba(26,31,78,0.95) 0%, rgba(45,52,120,0.9) 50%, rgba(26,31,78,0.95) 100%);
    border: 1px solid rgba(212,175,55,0.3);
    border-radius: 16px;
    padding: 20px 30px;
    margin-bottom: 20px;
    backdrop-filter: blur(20px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(212,175,55,0.15);
    position: relative;
    overflow: hidden;
}
.finassist-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #d4af37, #f0d060, #d4af37, transparent);
}
.finassist-header h1 {
    color: #f0d060 !important;
    font-size: 28px !important;
    font-weight: 800 !important;
    margin: 0 !important;
    letter-spacing: -0.5px;
    text-shadow: 0 0 30px rgba(240,208,96,0.3);
}
.finassist-header p {
    color: rgba(255,255,255,0.7) !important;
    font-size: 13px !important;
    margin: 4px 0 0 0 !important;
    font-weight: 400;
    letter-spacing: 0.5px;
}

/* ─── Glass Card ─── */
.glass-card {
    background: rgba(20,24,66,0.6) !important;
    border: 1px solid rgba(212,175,55,0.15) !important;
    border-radius: 14px !important;
    backdrop-filter: blur(16px) !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.2) !important;
    padding: 16px !important;
    margin-bottom: 12px !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.glass-card:hover {
    border-color: rgba(212,175,55,0.35) !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3), 0 0 20px rgba(212,175,55,0.05) !important;
}

/* ─── Profile Card ─── */
.profile-card {
    background: linear-gradient(145deg, rgba(20,24,66,0.8), rgba(30,35,90,0.6)) !important;
    border: 1px solid rgba(212,175,55,0.25) !important;
    border-radius: 16px !important;
    padding: 20px !important;
    margin-bottom: 12px !important;
}
.profile-card h3 {
    color: #f0d060 !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 12px !important;
}

/* ─── Sidebar Text ─── */
.sidebar-text {
    color: rgba(255,255,255,0.85) !important;
    font-size: 13px !important;
    line-height: 1.7 !important;
}
.sidebar-text strong {
    color: #f0d060 !important;
}

/* ─── Risk Badge ─── */
.risk-badge-high {
    display: inline-block;
    background: linear-gradient(135deg, #dc2626, #ef4444);
    color: white;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
    box-shadow: 0 2px 8px rgba(220,38,38,0.4);
}

/* ─── Chat Container ─── */
.chat-area {
    background: rgba(15,18,53,0.5) !important;
    border: 1px solid rgba(212,175,55,0.12) !important;
    border-radius: 16px !important;
    overflow: hidden !important;
}

/* ─── Chatbot Styling ─── */
.chatbot-container {
    background: transparent !important;
}
.chatbot-container .message {
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    line-height: 1.7 !important;
}
.chatbot-container .bot {
    background: rgba(20,24,66,0.7) !important;
    border: 1px solid rgba(212,175,55,0.15) !important;
    color: rgba(255,255,255,0.9) !important;
}
.chatbot-container .user {
    background: linear-gradient(135deg, rgba(212,175,55,0.2), rgba(240,208,96,0.15)) !important;
    border: 1px solid rgba(212,175,55,0.3) !important;
    color: white !important;
}

/* ─── Input Box ─── */
.input-area textarea {
    background: rgba(20,24,66,0.6) !important;
    border: 1px solid rgba(212,175,55,0.2) !important;
    border-radius: 12px !important;
    color: white !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    transition: all 0.3s ease !important;
}
.input-area textarea:focus {
    border-color: rgba(212,175,55,0.5) !important;
    box-shadow: 0 0 0 3px rgba(212,175,55,0.1) !important;
}
.input-area textarea::placeholder {
    color: rgba(255,255,255,0.35) !important;
}

/* ─── Send Button ─── */
.send-btn {
    background: linear-gradient(135deg, #d4af37 0%, #f0d060 50%, #d4af37 100%) !important;
    color: #0a0e27 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 12px !important;
    font-size: 14px !important;
    letter-spacing: 0.5px;
    box-shadow: 0 4px 16px rgba(212,175,55,0.3) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.send-btn:hover {
    box-shadow: 0 6px 24px rgba(212,175,55,0.5) !important;
    transform: translateY(-1px) !important;
}

/* ─── Trace Panel ─── */
.trace-panel {
    background: rgba(15,18,53,0.7) !important;
    border: 1px solid rgba(100,120,200,0.15) !important;
    border-radius: 12px !important;
    padding: 12px !important;
    margin-bottom: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
}
.trace-panel textarea {
    background: transparent !important;
    border: none !important;
    color: rgba(180,200,255,0.8) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 11px !important;
}

/* ─── Section Headers ─── */
.section-header {
    color: rgba(255,255,255,0.5) !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 16px 0 8px 0 !important;
}

/* ─── Allocation Bar ─── */
.alloc-bar {
    background: rgba(15,18,53,0.5);
    border-radius: 8px;
    overflow: hidden;
    height: 8px;
    margin: 4px 0 12px 0;
}
.alloc-fill {
    height: 100%;
    border-radius: 8px;
    transition: width 1s ease;
}

/* ─── Scrollbar ─── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: rgba(15,18,53,0.3); }
::-webkit-scrollbar-thumb {
    background: rgba(212,175,55,0.3);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(212,175,55,0.5); }

/* ─── Animations ─── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes shimmer {
    0% { background-position: -200% center; }
    100% { background-position: 200% center; }
}
@keyframes pulse-gold {
    0%, 100% { box-shadow: 0 0 0 0 rgba(212,175,55,0.3); }
    50% { box-shadow: 0 0 0 6px rgba(212,175,55,0); }
}

/* ─── Status Indicators ─── */
.status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse-gold 2s infinite;
}
.status-online { background: #22c55e; box-shadow: 0 0 8px rgba(34,197,94,0.5); }

/* ─── Label overrides ─── */
.gradio-container label { color: rgba(255,255,255,0.6) !important; font-size: 12px !important; }
.gradio-container .prose { color: rgba(255,255,255,0.85) !important; }
.gradio-container h1, .gradio-container h2, .gradio-container h3 {
    color: rgba(255,255,255,0.9) !important;
}
.gradio-container .markdown-text { color: rgba(255,255,255,0.85) !important; }
"""

# ══════════════════════════════════════════════════════════════════════════
# INITIALIZE ENGINE
# ══════════════════════════════════════════════════════════════════════════
engine = None


def get_engine():
    """Lazy-initialize the RAG engine."""
    global engine
    if engine is None:
        engine = RAGEngine("Sushil")
    return engine


# ══════════════════════════════════════════════════════════════════════════
# PROFILE SIDEBAR HTML
# ══════════════════════════════════════════════════════════════════════════
def build_profile_html(user_name: str = "Sushil") -> str:
    """Build the rich profile sidebar HTML."""
    profile = get_user_profile(user_name)
    if not profile:
        return "<p>No profile found.</p>"

    allocation = profile.get("allocation", {})
    # Build allocation bars
    alloc_html = ""
    colors = ["#d4af37", "#3b82f6", "#22c55e", "#ef4444", "#8b5cf6", "#f97316"]
    for i, (key, alloc) in enumerate(allocation.items()):
        color = colors[i % len(colors)]
        pct = alloc["percentage"]
        alloc_html += f"""
        <div style="margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:3px;">
                <span style="color:rgba(255,255,255,0.7); font-size:11px; text-transform:capitalize;">{key.replace('_', ' ').title()}</span>
                <span style="color:{color}; font-size:11px; font-weight:600;">{pct}%</span>
            </div>
            <div style="background:rgba(15,18,53,0.5); border-radius:6px; height:6px; overflow:hidden;">
                <div style="width:{pct}%; height:100%; background:linear-gradient(90deg, {color}, {color}88); border-radius:6px; transition:width 1.5s ease;"></div>
            </div>
        </div>
        """

    # Risk badge color
    risk = profile.get("riskProfile", "")
    if "high" in risk.lower() or "aggressive" in risk.lower():
        badge_style = "background:linear-gradient(135deg,#dc2626,#ef4444); box-shadow:0 2px 8px rgba(220,38,38,0.4);"
    elif "moderate" in risk.lower():
        badge_style = "background:linear-gradient(135deg,#f59e0b,#fbbf24); box-shadow:0 2px 8px rgba(245,158,11,0.4);"
    else:
        badge_style = "background:linear-gradient(135deg,#22c55e,#4ade80); box-shadow:0 2px 8px rgba(34,197,94,0.4);"

    metrics = profile.get("yearlyFinancialMetrics", {})

    sushil_img_src = get_image_base64("static/images/sushil.jpeg")
    html = f"""
    <div style="text-align:center; margin-bottom:16px;">
        <img src="{sushil_img_src}" style="width:64px; height:64px; border-radius:50%;
             margin:0 auto 10px; display:block; object-fit:cover; border:2px solid rgba(212,175,55,0.5);
             box-shadow:0 4px 16px rgba(212,175,55,0.3);">
        <div style="color:white; font-size:18px; font-weight:700;">{profile['name']}</div>
        <div style="color:rgba(255,255,255,0.5); font-size:12px; margin-top:2px;">{profile['occupation']}</div>
        <div style="margin-top:8px;">
            <span style="{badge_style} color:white; padding:3px 14px; border-radius:20px; font-size:10px; font-weight:700; letter-spacing:0.5px; text-transform:uppercase;">
                {profile['riskProfile']}
            </span>
        </div>
    </div>

    <div style="background:rgba(15,18,53,0.4); border-radius:12px; padding:14px; margin-bottom:14px; border:1px solid rgba(212,175,55,0.1);">
        <div style="color:rgba(255,255,255,0.5); font-size:10px; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:4px;">Total Portfolio</div>
        <div style="color:#f0d060; font-size:22px; font-weight:800; letter-spacing:-0.5px;">₹{format_inr(profile['totalPortfolioValue'])}</div>
        <div style="color:rgba(255,255,255,0.4); font-size:11px; margin-top:2px;">Age {profile['age']} · {profile['currency']}</div>
    </div>

    <div style="margin-bottom:14px;">
        <div style="color:rgba(255,255,255,0.4); font-size:10px; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:10px;">Allocation</div>
        {alloc_html}
    </div>

    <div style="background:rgba(15,18,53,0.4); border-radius:12px; padding:14px; border:1px solid rgba(100,120,200,0.1);">
        <div style="color:rgba(255,255,255,0.4); font-size:10px; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:8px;">Goals</div>
        {''.join(f'<div style="color:rgba(255,255,255,0.7); font-size:12px; padding:4px 0; border-bottom:1px solid rgba(255,255,255,0.05);">▸ {g}</div>' for g in profile.get('goals', []))}
    </div>

    <div style="background:rgba(15,18,53,0.4); border-radius:12px; padding:14px; margin-top:14px; border:1px solid rgba(100,120,200,0.1);">
        <div style="color:rgba(255,255,255,0.4); font-size:10px; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:8px;">Key Metrics</div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
            <div>
                <div style="color:rgba(255,255,255,0.4); font-size:9px;">Exp. Return</div>
                <div style="color:#22c55e; font-size:14px; font-weight:700;">{metrics.get('expectedAnnualReturn', 'N/A')}</div>
            </div>
            <div>
                <div style="color:rgba(255,255,255,0.4); font-size:9px;">Volatility</div>
                <div style="color:#f59e0b; font-size:14px; font-weight:700;">{metrics.get('expectedVolatility', 'N/A')}</div>
            </div>
            <div>
                <div style="color:rgba(255,255,255,0.4); font-size:9px;">Sharpe Ratio</div>
                <div style="color:#3b82f6; font-size:14px; font-weight:700;">{metrics.get('sharpeRatio', 'N/A')}</div>
            </div>
            <div>
                <div style="color:rgba(255,255,255,0.4); font-size:9px;">5yr Projection</div>
                <div style="color:#f0d060; font-size:14px; font-weight:700;">₹{metrics.get('projectedValue_5yr', 0)/100000:.1f}L</div>
            </div>
        </div>
    </div>
    """
    return html


# ══════════════════════════════════════════════════════════════════════════
# CHAT HANDLER
# ══════════════════════════════════════════════════════════════════════════
def process_message(user_message: str, history: list):
    """
    Process a chat message through the RAG engine with streaming response.
    Uses Gradio's messages format: list of {"role": ..., "content": ...}
    """
    if not user_message.strip():
        yield history, "", "", ""
        return

    # Convert history to tuple format for RAG engine
    chat_pairs = []
    current_user = None
    for msg in history:
        if isinstance(msg, dict):
            if msg.get("role") == "user":
                current_user = msg.get("content")
            elif msg.get("role") == "assistant" and current_user:
                chat_pairs.append((current_user, msg.get("content")))
                current_user = None

    # Add user message immediately and initial placeholder assistant message
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": "Thinking..."})
    yield history, "📚 Retrieving relevant context...", "Retrieving...", "⏱️ In progress..."

    try:
        eng = get_engine()
        # Stream the response chunks from query_stream
        for update in eng.query_stream(user_message, chat_pairs):
            answer = update["answer"]
            chunks = update["retrieved_chunks"]
            trace = update["trace"]

            # Build trace info
            rag_info = f"📚 Retrieved {trace['chunks_retrieved']} chunks\n"
            rag_info += f"⏱️ Retrieval: {trace['retrieval_time_ms']}ms\n"
            rag_info += f"Sources:\n"
            for src in trace.get("sources_used", []):
                rag_info += f"  • {src}\n"

            # Build chunk details
            chunk_details = ""
            for i, chunk in enumerate(chunks, 1):
                chunk_details += f"[{i}] {chunk['fund_name']} (Score: {chunk['relevance_score']:.0%})\n"
                preview = chunk['text'][:200].replace('\n', ' ')
                chunk_details += f"    {preview}...\n\n"

            # Timing
            timing_info = (
                f"🤖 Model: {trace['model']}\n"
                f"⏱️ Generation: {trace['generation_time_ms']}ms\n"
                f"⏱️ Total: {trace['total_time_ms']}ms"
            )

            # Update last assistant message in history
            history[-1] = {"role": "assistant", "content": answer}
            yield history, rag_info, chunk_details, timing_info

    except Exception as e:
        answer = f"⚠️ Error: {str(e)}\n\nPlease ensure your `.env` file has a valid `GOOGLE_API_KEY`."
        history[-1] = {"role": "assistant", "content": answer}
        yield history, "❌ Error during retrieval", "", "❌ Error"


# ══════════════════════════════════════════════════════════════════════════
# GRADIO APP LAYOUT
# ══════════════════════════════════════════════════════════════════════════
def create_app():
    """Build and return the Gradio app."""

    profile_html = build_profile_html("Sushil")
    eng = get_engine()
    welcome_msg = eng.get_welcome_message()

    with gr.Blocks(
        title="Finassist — AI Finance Assistant",
    ) as app:

        logo_img_src = get_image_base64("static/images/finassist_logo.png")
        gr.HTML(f"""
        <div class="finassist-header">
            <div style="display:flex; align-items:center; justify-content:space-between;">
                <div style="display:flex; align-items:center; gap:12px;">
                    <img src="{logo_img_src}" style="width:48px; height:48px; border-radius:8px; object-fit:cover; border:1px solid rgba(212,175,55,0.4);">
                    <div>
                        <h1>Finassist</h1>
                        <p>AI-Powered Personal Finance Assistant · RAG-Grounded · Educational Only</p>
                    </div>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span class="status-dot status-online"></span>
                    <span style="color:rgba(255,255,255,0.6); font-size:12px;">Engine Online</span>
                </div>
            </div>
        </div>
        """)

        with gr.Row():

            # ═══ LEFT SIDEBAR — User Profile ═══
            with gr.Column(scale=2, min_width=260):
                gr.HTML(f"""
                <div style="color:rgba(255,255,255,0.4); font-size:10px; text-transform:uppercase;
                     letter-spacing:2px; margin-bottom:12px; padding-left:4px;">
                    👤 Investor Profile
                </div>
                """)
                gr.HTML(f'<div class="profile-card">{profile_html}</div>')

            # ═══ CENTER — Chat Interface ═══
            with gr.Column(scale=5, min_width=500):
                chatbot = gr.Chatbot(
                    value=[{"role": "assistant", "content": welcome_msg}],
                    height=620,
                    show_label=False,
                    avatar_images=(
                        get_image_absolute_path("static/images/sushil.jpeg"),
                        get_image_absolute_path("static/images/finassist_logo.png")
                    ),
                    elem_classes=["chatbot-container"],
                )

                with gr.Row():
                    msg_input = gr.Textbox(
                        placeholder="Ask about funds, portfolio, or investment concepts...",
                        show_label=False,
                        scale=8,
                        container=False,
                        elem_classes=["input-area"],
                        max_lines=3,
                    )
                    send_btn = gr.Button(
                        "Send ➤",
                        variant="primary",
                        scale=1,
                        min_width=100,
                        elem_classes=["send-btn"],
                    )

                # Quick action buttons
                with gr.Row():
                    gr.Button("💡 Low-cost index funds", size="sm", variant="secondary").click(
                        lambda: "What is a good low-cost index fund for my risk profile?",
                        outputs=msg_input,
                    )
                    gr.Button("📊 Portfolio overview", size="sm", variant="secondary").click(
                        lambda: "Give me an overview of my current portfolio allocation",
                        outputs=msg_input,
                    )
                    gr.Button("📈 Best performers", size="sm", variant="secondary").click(
                        lambda: "Which of my fund holdings have the best returns?",
                        outputs=msg_input,
                    )

            # ═══ RIGHT SIDEBAR — Observability Trace ═══
            with gr.Column(scale=3, min_width=280):
                gr.HTML("""
                <div style="color:rgba(255,255,255,0.4); font-size:10px; text-transform:uppercase;
                     letter-spacing:2px; margin-bottom:12px; padding-left:4px;">
                    🔍 Observability Trace
                </div>
                """)

                with gr.Group(elem_classes=["glass-card"]):
                    gr.HTML('<div style="color:#f0d060; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">📚 RAG Retrieval</div>')
                    rag_trace = gr.Textbox(
                        show_label=False,
                        value="Waiting for query...",
                        interactive=False,
                        container=False,
                        lines=5,
                        elem_classes=["trace-panel"],
                    )

                with gr.Group(elem_classes=["glass-card"]):
                    gr.HTML('<div style="color:#3b82f6; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">📄 Retrieved Chunks</div>')
                    chunk_trace = gr.Textbox(
                        show_label=False,
                        value="No chunks retrieved yet...",
                        interactive=False,
                        container=False,
                        lines=8,
                        elem_classes=["trace-panel"],
                    )

                with gr.Group(elem_classes=["glass-card"]):
                    gr.HTML('<div style="color:#22c55e; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">⚡ Performance</div>')
                    timing_trace = gr.Textbox(
                        show_label=False,
                        value="Waiting for query...",
                        interactive=False,
                        container=False,
                        lines=3,
                        elem_classes=["trace-panel"],
                    )

        # ── Footer ──
        gr.HTML("""
        <div style="text-align:center; padding:16px 0 8px; color:rgba(255,255,255,0.25); font-size:11px;">
            Finassist v2.0 · Built with Gemini + ChromaDB + Gradio · Educational Use Only
            <br>Data sourced from fund fact sheet PDFs · Not investment advice
        </div>
        """)

        # ═══ EVENT WIRING ═══
        submit_args = dict(
            fn=process_message,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, rag_trace, chunk_trace, timing_trace],
        )

        msg_input.submit(**submit_args).then(lambda: "", outputs=msg_input)
        send_btn.click(**submit_args).then(lambda: "", outputs=msg_input)

    return app


# ══════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = create_app()
    app.launch(
        share=True,
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        css=CUSTOM_CSS,
        allowed_paths=[str(Path(__file__).resolve().parent.parent / "static")],
        theme=gr.themes.Base(
            primary_hue=gr.themes.colors.amber,
            secondary_hue=gr.themes.colors.blue,
            neutral_hue=gr.themes.colors.slate,
            font=gr.themes.GoogleFont("Inter"),
        ),
    )
