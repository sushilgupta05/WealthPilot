# WealthPilot: Requirements

**Industry:** Finance

## 1. Objective
Build a personal finance and investment assistant that answers user questions using RAG over fund fact sheets and market reports, performs portfolio calculations and live-quote lookups via tools, and remembers a user's risk profile and goals across sessions; while never issuing definitive buy/sell advice.

## 2. User Persona
**Marcus Chen**, a 29-year-old software engineer, has $40,000 in savings and a 401(k) but feels overwhelmed by investment jargon and doesn't trust generic robo-advisors that don't explain their reasoning. He checks his portfolio a few times a week and wants a conversational assistant that can explain *why* a fund fits his moderate-risk, long-horizon profile, calculate how a rebalance would affect his allocation, and remind him of decisions he's already made (e.g., "you said you didn't want more than 10% in crypto"). His objective: make more informed decisions faster, without feeling like he's being sold something.

## 3. Sample Queries & Expected Answers

| # | Input / Query | Expected Agent Behavior |
|---|---|---|
| 1 | "What's a good low-cost index fund for a moderate-risk investor?" | Retrieves 2-3 candidate funds from the fund fact sheet RAG index with expense ratios and historical volatility, cited to source; frames as educational options, not a recommendation to buy. |
| 2 | "If I move $5,000 from bonds to equities, what's my new allocation?" | Calls the portfolio-calculation tool, returns the updated allocation percentages and a plain-language summary of the risk shift. |
| 3 | "What's the current price of VTI?" | Calls the live-quote tool, returns price with timestamp, notes data may be delayed. |
| 4 | "Remind me what my risk tolerance is." | Retrieves from memory the risk profile set in an earlier session and states it back accurately. |
| 5 | "Should I sell everything and buy Bitcoin?" | Declines to give directive advice; explains the volatility/risk considerations, references the user's stated risk profile from memory, and suggests consulting a licensed advisor for a decision of this size. |
| 6 | "What was the fund's return last year?" | Retrieves the historical return from the fact-sheet RAG index, cites the source document and date, and notes past performance doesn't guarantee future results. |

## 4. Constraints
- Market/fund data may come from a free/delayed API or a static sample dataset; real-time trading data is not required.
- RAG corpus limited to public fund fact sheets, prospectus summaries, and sample market reports (no proprietary research).
- No real brokerage integration; all trades/rebalances are simulated, never executed.
- Must support at least 2 return visits in the demo showing memory persistence of the user's stated risk profile.

## 5. Guardrail Requirements
- The agent must never issue a directive "buy/sell/invest now" instruction; all output must be framed as educational/informational with a disclaimer.
- Must never fabricate a fund's performance numbers; every quantitative claim must be traceable to a RAG citation or tool call output.
- Must flag and add extra caution language for high-risk requests (e.g., large lump-sum moves, speculative assets) and reference the user's own stated risk tolerance from memory.
- Must not store or request sensitive PII (SSNs, account numbers, passwords); only preference/profile data needed for personalization.
- Observability must log which retrieved documents and tool outputs informed each response, enabling a full explainability trace for any answer given.
