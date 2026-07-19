"""
Finassist — UI Design Preview (Standalone)
No backend logic, no imports, no dependencies except gradio.
Just the premium design with static mock data.
"""
import gradio as gr

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

/* ─── Scrollbar ─── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: rgba(15,18,53,0.3); }
::-webkit-scrollbar-thumb {
    background: rgba(212,175,55,0.3);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(212,175,55,0.5); }

/* ─── Animations ─── */
@keyframes pulse-gold {
    0%, 100% { box-shadow: 0 0 0 0 rgba(212,175,55,0.3); }
    50% { box-shadow: 0 0 0 6px rgba(212,175,55,0); }
}
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

/* ─── Quick Action Buttons ─── */
.quick-btn {
    background: rgba(20,24,66,0.5) !important;
    border: 1px solid rgba(212,175,55,0.15) !important;
    color: rgba(255,255,255,0.7) !important;
    font-size: 12px !important;
    border-radius: 10px !important;
    transition: all 0.3s ease !important;
}
.quick-btn:hover {
    border-color: rgba(212,175,55,0.4) !important;
    color: #f0d060 !important;
    background: rgba(212,175,55,0.08) !important;
}
"""

# ══════════════════════════════════════════════════════════════════════════
# STATIC PROFILE HTML (Sushil)
# ══════════════════════════════════════════════════════════════════════════
PROFILE_HTML = """
<div style="text-align:center; margin-bottom:16px;">
    <div style="width:64px; height:64px; border-radius:50%; background:linear-gradient(135deg,#d4af37,#f0d060);
         margin:0 auto 10px; display:flex; align-items:center; justify-content:center;
         font-size:24px; font-weight:800; color:#0a0e27; box-shadow:0 4px 16px rgba(212,175,55,0.3);
         animation: pulse-gold 3s infinite;">
        S
    </div>
    <div style="color:white; font-size:18px; font-weight:700;">Sushil</div>
    <div style="color:rgba(255,255,255,0.5); font-size:12px; margin-top:2px;">Technology Professional</div>
    <div style="margin-top:8px;">
        <span style="background:linear-gradient(135deg,#dc2626,#ef4444); box-shadow:0 2px 8px rgba(220,38,38,0.4);
             color:white; padding:3px 14px; border-radius:20px; font-size:10px; font-weight:700;
             letter-spacing:0.5px; text-transform:uppercase;">
            High / Aggressive
        </span>
    </div>
</div>

<div style="background:rgba(15,18,53,0.4); border-radius:12px; padding:14px; margin-bottom:14px; border:1px solid rgba(212,175,55,0.1);">
    <div style="color:rgba(255,255,255,0.5); font-size:10px; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:4px;">Total Portfolio</div>
    <div style="color:#f0d060; font-size:22px; font-weight:800; letter-spacing:-0.5px;">₹25,00,000</div>
    <div style="color:rgba(255,255,255,0.4); font-size:11px; margin-top:2px;">Age 22 · INR</div>
</div>

<div style="margin-bottom:14px;">
    <div style="color:rgba(255,255,255,0.4); font-size:10px; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:10px;">Allocation</div>

    <div style="margin-bottom:10px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:3px;">
            <span style="color:rgba(255,255,255,0.7); font-size:11px;">House Escrow</span>
            <span style="color:#d4af37; font-size:11px; font-weight:600;">40%</span>
        </div>
        <div style="background:rgba(15,18,53,0.5); border-radius:6px; height:6px; overflow:hidden;">
            <div style="width:40%; height:100%; background:linear-gradient(90deg, #d4af37, #d4af3788); border-radius:6px;"></div>
        </div>
    </div>

    <div style="margin-bottom:10px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:3px;">
            <span style="color:rgba(255,255,255,0.7); font-size:11px;">Trip Fund</span>
            <span style="color:#3b82f6; font-size:11px; font-weight:600;">25%</span>
        </div>
        <div style="background:rgba(15,18,53,0.5); border-radius:6px; height:6px; overflow:hidden;">
            <div style="width:25%; height:100%; background:linear-gradient(90deg, #3b82f6, #3b82f688); border-radius:6px;"></div>
        </div>
    </div>

    <div style="margin-bottom:10px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:3px;">
            <span style="color:rgba(255,255,255,0.7); font-size:11px;">Long Term Equity</span>
            <span style="color:#22c55e; font-size:11px; font-weight:600;">30%</span>
        </div>
        <div style="background:rgba(15,18,53,0.5); border-radius:6px; height:6px; overflow:hidden;">
            <div style="width:30%; height:100%; background:linear-gradient(90deg, #22c55e, #22c55e88); border-radius:6px;"></div>
        </div>
    </div>

    <div style="margin-bottom:10px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:3px;">
            <span style="color:rgba(255,255,255,0.7); font-size:11px;">Cryptocurrency</span>
            <span style="color:#ef4444; font-size:11px; font-weight:600;">5%</span>
        </div>
        <div style="background:rgba(15,18,53,0.5); border-radius:6px; height:6px; overflow:hidden;">
            <div style="width:5%; height:100%; background:linear-gradient(90deg, #ef4444, #ef444488); border-radius:6px;"></div>
        </div>
    </div>
</div>

<div style="background:rgba(15,18,53,0.4); border-radius:12px; padding:14px; border:1px solid rgba(100,120,200,0.1);">
    <div style="color:rgba(255,255,255,0.4); font-size:10px; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:8px;">Goals</div>
    <div style="color:rgba(255,255,255,0.7); font-size:12px; padding:4px 0; border-bottom:1px solid rgba(255,255,255,0.05);">▸ Build own house (5-7 years)</div>
    <div style="color:rgba(255,255,255,0.7); font-size:12px; padding:4px 0; border-bottom:1px solid rgba(255,255,255,0.05);">▸ Fund foreign trips (Annual)</div>
    <div style="color:rgba(255,255,255,0.7); font-size:12px; padding:4px 0;">▸ Long-term retirement wealth</div>
</div>

<div style="background:rgba(15,18,53,0.4); border-radius:12px; padding:14px; margin-top:14px; border:1px solid rgba(100,120,200,0.1);">
    <div style="color:rgba(255,255,255,0.4); font-size:10px; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:8px;">Key Metrics</div>
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
        <div>
            <div style="color:rgba(255,255,255,0.4); font-size:9px;">Exp. Return</div>
            <div style="color:#22c55e; font-size:14px; font-weight:700;">10.5%</div>
        </div>
        <div>
            <div style="color:rgba(255,255,255,0.4); font-size:9px;">Volatility</div>
            <div style="color:#f59e0b; font-size:14px; font-weight:700;">18-22%</div>
        </div>
        <div>
            <div style="color:rgba(255,255,255,0.4); font-size:9px;">Sharpe Ratio</div>
            <div style="color:#3b82f6; font-size:14px; font-weight:700;">0.52</div>
        </div>
        <div>
            <div style="color:rgba(255,255,255,0.4); font-size:9px;">5yr Projection</div>
            <div style="color:#f0d060; font-size:14px; font-weight:700;">₹41.0L</div>
        </div>
    </div>
</div>
"""

# ══════════════════════════════════════════════════════════════════════════
# MOCK CHAT DATA
# ══════════════════════════════════════════════════════════════════════════
WELCOME_MSG = (
    "👋 Welcome back, **Sushil**! I'm Finassist, your personal finance assistant.\n\n"
    "Here's a quick snapshot of your profile:\n"
    "- **Risk Profile:** High/Aggressive\n"
    "- **Portfolio Value:** ₹25,00,000\n"
    "- **Goals:** Build own house, Fund foreign trips, Long-term retirement wealth\n\n"
    "I can help you explore your holdings, understand fund performance, "
    "and learn about investment options — all grounded in real data.\n\n"
    "Try asking:\n"
    '- *"What is a good low-cost index fund?"*\n'
    '- *"Tell me about my SBI Bluechip Fund performance"*\n'
    '- *"What are the best liquid funds for short-term parking?"*\n\n'
    "📋 *Disclaimer: I provide educational information only. "
    "Please consult a licensed advisor for investment decisions.*"
)

SAMPLE_ANSWER = (
    "Great question, Sushil! Based on your **High/Aggressive** risk profile and long-term goals, "
    "here are some low-cost index fund options from the knowledge base:\n\n"
    "### 1. HDFC Sensex Index Fund\n"
    "- **Expense Ratio:** 0.13% [LOW-COST] ✅\n"
    "- **Category:** Index Fund (Sensex)\n"
    "- **1-Year Return:** 12.4%\n"
    "- **Expected Return:** 10-11%\n"
    "- *Source: HDFC_Sensex_Index_Fund.txt*\n\n"
    "### 2. UTI Nifty 50 Index Fund\n"
    "- **Expense Ratio:** 0.18% [LOW-COST] ✅\n"
    "- **Category:** Index Fund (Nifty 50)\n"
    "- **1-Year Return:** 11.8%\n"
    "- **Expected Return:** 10-12%\n"
    "- *Source: UTI_Nifty_50_Index_Fund.txt*\n\n"
    "**Why these fit your profile:** Both funds track major indices with minimal cost drag. "
    "Given your 30+ year retirement horizon, the compounding benefit of low expense ratios "
    "is significant — saving ~1% annually could mean ₹5-8L more over 20 years.\n\n"
    "You already hold ₹2,00,000 in HDFC Sensex Index Fund (8% allocation), "
    "which aligns well with your long-term equity bucket.\n\n"
    "📋 *Disclaimer: This information is for educational purposes only and does not "
    "constitute investment advice. Past performance does not guarantee future results. "
    "Please consult a licensed financial advisor before making investment decisions.*"
)

MOCK_CHAT = [
    {"role": "assistant", "content": WELCOME_MSG},
    {"role": "user", "content": "What is a good low-cost index fund for my risk profile?"},
    {"role": "assistant", "content": SAMPLE_ANSWER},
]

# ══════════════════════════════════════════════════════════════════════════
# GRADIO APP
# ══════════════════════════════════════════════════════════════════════════
with gr.Blocks(
    title="Finassist — AI Finance Assistant",
) as demo:

    # ── Header ──
    gr.HTML("""
    <div class="finassist-header">
        <div style="display:flex; align-items:center; justify-content:space-between;">
            <div>
                <h1>🧭 Finassist</h1>
                <p>AI-Powered Personal Finance Assistant · RAG-Grounded · Educational Only</p>
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
            gr.HTML("""
            <div style="color:rgba(255,255,255,0.4); font-size:10px; text-transform:uppercase;
                 letter-spacing:2px; margin-bottom:12px; padding-left:4px;">
                👤 Investor Profile
            </div>
            """)
            gr.HTML(f'<div class="profile-card">{PROFILE_HTML}</div>')

        # ═══ CENTER — Chat Interface ═══
        with gr.Column(scale=5, min_width=500):
            chatbot = gr.Chatbot(
                value=MOCK_CHAT,
                height=620,
                show_label=False,
                avatar_images=(
                    "static/images/sushil.jpeg",
                    "static/images/finassist_logo.png"
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
                gr.Button("💡 Low-cost index funds", size="sm", variant="secondary", elem_classes=["quick-btn"])
                gr.Button("📊 Portfolio overview", size="sm", variant="secondary", elem_classes=["quick-btn"])
                gr.Button("📈 Best performers", size="sm", variant="secondary", elem_classes=["quick-btn"])

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
                gr.Textbox(
                    show_label=False,
                    value="📚 Retrieved 5 chunks\n⏱️ Retrieval: 42ms\nSources:\n  • HDFC_Sensex_Index_Fund.txt\n  • UTI_Nifty_50_Index_Fund.txt\n  • PORTFOLIO_SUSHIL.txt",
                    interactive=False,
                    container=False,
                    lines=5,
                    elem_classes=["trace-panel"],
                )

            with gr.Group(elem_classes=["glass-card"]):
                gr.HTML('<div style="color:#3b82f6; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">📄 Retrieved Chunks</div>')
                gr.Textbox(
                    show_label=False,
                    value="[1] HDFC Sensex Index Fund (Score: 94%)\n    Fund Name: HDFC Sensex Index Fund\n    Expense Ratio: 0.13% [LOW-COST]\n\n[2] UTI Nifty 50 Index Fund (Score: 89%)\n    Fund Name: UTI Nifty 50 Index Fund\n    Category: Index Fund - Nifty 50\n\n[3] Portfolio Sushil (Score: 82%)\n    Risk Profile: High/Aggressive\n    Total Portfolio: INR 25,00,000",
                    interactive=False,
                    container=False,
                    lines=10,
                    elem_classes=["trace-panel"],
                )

            with gr.Group(elem_classes=["glass-card"]):
                gr.HTML('<div style="color:#22c55e; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;">⚡ Performance</div>')
                gr.Textbox(
                    show_label=False,
                    value="🤖 Model: gemini-2.0-flash\n⏱️ Generation: 1240ms\n⏱️ Total: 1282ms",
                    interactive=False,
                    container=False,
                    lines=3,
                    elem_classes=["trace-panel"],
                )

    # ── Footer ──
    gr.HTML("""
    <div style="text-align:center; padding:16px 0 8px; color:rgba(255,255,255,0.25); font-size:11px;">
        Finassist v1.0 · Built with Gemini + ChromaDB + Gradio · Educational Use Only
        <br>Data sourced from MFapi.in (AMFI) · Not investment advice
    </div>
    """)


if __name__ == "__main__":
    demo.launch(
        share=False,
        inbrowser=True,
        css=CUSTOM_CSS,
        theme=gr.themes.Base(
            primary_hue=gr.themes.colors.amber,
            secondary_hue=gr.themes.colors.blue,
            neutral_hue=gr.themes.colors.slate,
            font=gr.themes.GoogleFont("Inter"),
        ),
    )
