"""
Finassist — RAG Engine
Orchestrates the full RAG pipeline: retrieval → prompt construction → LLM call.
Uses Google Gemini 2.0 Flash as the primary LLM.
"""
import time
import traceback
from google import genai
from google.genai import types
from src.config import (
    GOOGLE_API_KEY, GEMINI_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS,
    LLM_PROVIDER, GROQ_API_KEY, GROQ_MODEL, HF_TOKEN, HF_MODEL
)
from src.retriever import FundRetriever
from src.system_prompt import generate_system_prompt


class RAGEngine:
    """
    Full RAG pipeline engine supporting multiple LLM backends:
    - Groq (Finance/Reasoning dedicated models)
    - Hugging Face (Fine-tuned finance models)
    - Google Gemini
    """

    def __init__(self, user_name: str = "Sushil"):
        self.user_name = user_name
        self.retriever = FundRetriever()
        self.system_prompt = generate_system_prompt(user_name)
        self.provider = LLM_PROVIDER

        if self.provider == "groq" and GROQ_API_KEY:
            from groq import Groq
            self.groq_client = Groq(api_key=GROQ_API_KEY)
            self.model_name = GROQ_MODEL
            print(f"[RAGEngine] Initialized for user '{user_name}' with Groq Finance Model '{self.model_name}'")
        elif self.provider == "huggingface" and HF_TOKEN:
            from huggingface_hub import InferenceClient
            self.hf_client = InferenceClient(token=HF_TOKEN)
            self.model_name = HF_MODEL
            print(f"[RAGEngine] Initialized for user '{user_name}' with HuggingFace Model '{self.model_name}'")
        else:
            self.provider = "gemini"
            if not GOOGLE_API_KEY:
                raise ValueError(
                    "No API Key found! Please set GROQ_API_KEY, HF_TOKEN, or GOOGLE_API_KEY in your .env file."
                )
            self.client = genai.Client(api_key=GOOGLE_API_KEY)
            self.model_name = GEMINI_MODEL
            self.gen_config = types.GenerateContentConfig(
                temperature=LLM_TEMPERATURE,
                max_output_tokens=LLM_MAX_TOKENS,
                system_instruction=self.system_prompt,
            )
            print(f"[RAGEngine] Initialized for user '{user_name}' with Gemini Model '{self.model_name}'")

    @staticmethod
    def _extract_text(msg) -> str:
        """Extract plain text from Gradio's various message formats."""
        if msg is None:
            return ""
        if isinstance(msg, str):
            return msg
        if isinstance(msg, dict):
            return msg.get("text", str(msg))
        if isinstance(msg, list):
            # Gradio sometimes passes [{'text': '...', 'type': 'text'}]
            parts = []
            for item in msg:
                if isinstance(item, dict):
                    parts.append(item.get("text", str(item)))
                elif isinstance(item, str):
                    parts.append(item)
            return " ".join(parts) if parts else str(msg)
        return str(msg)

    def _get_messages_for_openai_style(self, chat_history: list, augmented_prompt: str) -> list[dict]:
        """Build messages format for Groq/HuggingFace chat completion API."""
        messages = [{"role": "system", "content": self.system_prompt}]
        if chat_history:
            for msg_user, msg_bot in chat_history[-5:]:
                u_text = self._extract_text(msg_user)
                b_text = self._extract_text(msg_bot)
                if u_text:
                    messages.append({"role": "user", "content": u_text})
                if b_text:
                    messages.append({"role": "assistant", "content": b_text})
        messages.append({"role": "user", "content": augmented_prompt})
        return messages

    def query(self, user_message: str, chat_history: list = None) -> dict:
        """
        Process a user query through the full RAG pipeline.

        Returns dict:
        {
            "answer": str,
            "retrieved_chunks": list[dict],
            "context": str,
            "trace": dict,
        }
        """
        start_time = time.time()
        trace = {
            "user_query": user_message,
            "retrieval_time_ms": 0,
            "generation_time_ms": 0,
            "total_time_ms": 0,
            "chunks_retrieved": 0,
            "sources_used": [],
            "model": self.model_name,
        }

        # ── Step 1: Retrieve relevant chunks ────────────────────────────
        retrieval_start = time.time()
        retrieved_chunks = self.retriever.retrieve(user_message)
        context = self.retriever.format_context(retrieved_chunks)
        trace["retrieval_time_ms"] = round((time.time() - retrieval_start) * 1000)
        trace["chunks_retrieved"] = len(retrieved_chunks)
        trace["sources_used"] = list(set(r["source"] for r in retrieved_chunks))

        # ── Step 2: Construct the augmented prompt ──────────────────────
        augmented_prompt = f"""
{context}

═══════════════════════════════════════════
USER QUESTION
═══════════════════════════════════════════
{user_message}

Instructions: Answer the question using ONLY the retrieved context above. 
Cite the source document for any quantitative claims. If the context doesn't 
contain relevant information, clearly state that you don't have that data.
"""

        # ── Step 3: Generate response with Selected Provider ───────────
        generation_start = time.time()
        try:
            if self.provider == "groq":
                messages = self._get_messages_for_openai_style(chat_history, augmented_prompt)
                response = self.groq_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=LLM_TEMPERATURE,
                    max_tokens=2500,  # Caps requested output tokens to stay well within Groq's 8000 TPM On-Demand limit
                )
                answer = response.choices[0].message.content
            elif self.provider == "huggingface":
                messages = self._get_messages_for_openai_style(chat_history, augmented_prompt)
                response = self.hf_client.chat_completion(
                    model=self.model_name,
                    messages=messages,
                    temperature=LLM_TEMPERATURE,
                    max_tokens=LLM_MAX_TOKENS,
                )
                answer = response.choices[0].message.content
            else:
                # Build conversation contents with history for Gemini
                contents = []
                if chat_history:
                    for msg_user, msg_bot in chat_history[-5:]:  # Last 5 exchanges
                        user_text = self._extract_text(msg_user)
                        bot_text = self._extract_text(msg_bot)
                        if user_text:
                            contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_text)]))
                        if bot_text:
                            contents.append(types.Content(role="model", parts=[types.Part.from_text(text=bot_text)]))

                # Add the current augmented prompt
                contents.append(types.Content(role="user", parts=[types.Part.from_text(text=augmented_prompt)]))

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=self.gen_config,
                )
                answer = response.text

        except Exception as e:
            traceback.print_exc()
            answer = (
                f"I encountered an error while generating a response: {str(e)}\n\n"
                "Please check that your GOOGLE_API_KEY is valid and try again.\n\n"
                "📋 *Disclaimer: This is a technical error, not investment advice.*"
            )

        trace["generation_time_ms"] = round((time.time() - generation_start) * 1000)
        trace["total_time_ms"] = round((time.time() - start_time) * 1000)

        return {
            "answer": answer,
            "retrieved_chunks": retrieved_chunks,
            "context": context,
            "trace": trace,
        }

    def query_stream(self, user_message: str, chat_history: list = None):
        """
        Process a user query through the full RAG pipeline and yield chunks.
        Yields dict:
        {
            "answer": str,
            "retrieved_chunks": list[dict],
            "context": str,
            "trace": dict,
            "done": bool
        }
        """
        start_time = time.time()
        trace = {
            "user_query": user_message,
            "retrieval_time_ms": 0,
            "generation_time_ms": 0,
            "total_time_ms": 0,
            "chunks_retrieved": 0,
            "sources_used": [],
            "model": self.model_name,
        }

        # ── Step 1: Retrieve relevant chunks ────────────────────────────
        retrieval_start = time.time()
        retrieved_chunks = self.retriever.retrieve(user_message)
        context = self.retriever.format_context(retrieved_chunks)
        trace["retrieval_time_ms"] = round((time.time() - retrieval_start) * 1000)
        trace["chunks_retrieved"] = len(retrieved_chunks)
        trace["sources_used"] = list(set(r["source"] for r in retrieved_chunks))

        # ── Step 2: Construct the augmented prompt ──────────────────────
        augmented_prompt = f"""
{context}

═══════════════════════════════════════════
USER QUESTION
═══════════════════════════════════════════
{user_message}

Instructions: Answer the question using ONLY the retrieved context above. 
Cite the source document for any quantitative claims. If the context doesn't 
contain relevant information, clearly state that you don't have that data.
"""

        # Build conversation contents with history
        contents = []
        if chat_history:
            for msg_user, msg_bot in chat_history[-5:]:  # Last 5 exchanges
                user_text = self._extract_text(msg_user)
                bot_text = self._extract_text(msg_bot)
                if user_text:
                    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_text)]))
                if bot_text:
                    contents.append(types.Content(role="model", parts=[types.Part.from_text(text=bot_text)]))

        # Add the current augmented prompt
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=augmented_prompt)]))

        # ── Step 3: Stream response with Selected Provider ────────────
        generation_start = time.time()
        try:
            if self.provider == "groq":
                messages = self._get_messages_for_openai_style(chat_history, augmented_prompt)
                response_stream = self.groq_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=LLM_TEMPERATURE,
                    max_tokens=2500,  # Caps requested output tokens to stay well within Groq's 8000 TPM On-Demand limit
                    stream=True,
                )
                answer = ""
                for chunk in response_stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        answer += chunk.choices[0].delta.content
                        current_trace = trace.copy()
                        current_trace["generation_time_ms"] = round((time.time() - generation_start) * 1000)
                        current_trace["total_time_ms"] = round((time.time() - start_time) * 1000)
                        yield {
                            "answer": answer,
                            "retrieved_chunks": retrieved_chunks,
                            "context": context,
                            "trace": current_trace,
                            "done": False,
                        }
            elif self.provider == "huggingface":
                messages = self._get_messages_for_openai_style(chat_history, augmented_prompt)
                response_stream = self.hf_client.chat_completion(
                    model=self.model_name,
                    messages=messages,
                    temperature=LLM_TEMPERATURE,
                    max_tokens=LLM_MAX_TOKENS,
                    stream=True,
                )
                answer = ""
                for chunk in response_stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        answer += chunk.choices[0].delta.content
                        current_trace = trace.copy()
                        current_trace["generation_time_ms"] = round((time.time() - generation_start) * 1000)
                        current_trace["total_time_ms"] = round((time.time() - start_time) * 1000)
                        yield {
                            "answer": answer,
                            "retrieved_chunks": retrieved_chunks,
                            "context": context,
                            "trace": current_trace,
                            "done": False,
                        }
            else:
                response_stream = self.client.models.generate_content_stream(
                    model=self.model_name,
                    contents=contents,
                    config=self.gen_config,
                )
                
                answer = ""
                for chunk in response_stream:
                    if chunk.text:
                        answer += chunk.text
                        current_trace = trace.copy()
                        current_trace["generation_time_ms"] = round((time.time() - generation_start) * 1000)
                        current_trace["total_time_ms"] = round((time.time() - start_time) * 1000)
                        yield {
                            "answer": answer,
                            "retrieved_chunks": retrieved_chunks,
                            "context": context,
                            "trace": current_trace,
                            "done": False
                        }

            trace["generation_time_ms"] = round((time.time() - generation_start) * 1000)
            trace["total_time_ms"] = round((time.time() - start_time) * 1000)
            yield {
                "answer": answer,
                "retrieved_chunks": retrieved_chunks,
                "context": context,
                "trace": trace,
                "done": True
            }

        except Exception as e:
            traceback.print_exc()
            answer = (
                f"I encountered an error while generating a response: {str(e)}\n\n"
                "Please check that your GOOGLE_API_KEY is valid and try again.\n\n"
                "📋 *Disclaimer: This is a technical error, not investment advice.*"
            )
            trace["generation_time_ms"] = round((time.time() - generation_start) * 1000)
            trace["total_time_ms"] = round((time.time() - start_time) * 1000)
            yield {
                "answer": answer,
                "retrieved_chunks": retrieved_chunks,
                "context": context,
                "trace": trace,
                "done": True
            }

    def get_welcome_message(self) -> str:
        """Generate a personalized welcome message for the user."""
        from src.user_profile_loader import get_user_profile
        profile = get_user_profile(self.user_name)
        if not profile:
            return "Welcome to Finassist! Ask me anything about mutual funds and investing."

        from src.config import format_inr
        return (
            f"👋 Welcome back, **{profile['name']}**! I'm Finassist, your personal finance assistant.\n\n"
            f"Here's a quick snapshot of your profile:\n"
            f"- **Risk Profile:** {profile['riskProfile']}\n"
            f"- **Portfolio Value:** ₹{format_inr(profile['totalPortfolioValue'])}\n"
            f"- **Goals:** {', '.join(profile.get('goals', []))}\n\n"
            f"I can help you explore your holdings, understand fund performance, "
            f"and learn about investment options — all grounded in real data.\n\n"
            f"Try asking:\n"
            f'- *"What is a good low-cost index fund?"*\n'
            f'- *"Tell me about my SBI Bluechip Fund performance"*\n'
            f'- *"What are the best liquid funds for short-term parking?"*\n\n'
            f"📋 *Disclaimer: I provide educational information only. "
            f"Please consult a licensed advisor for investment decisions.*"
        )


if __name__ == "__main__":
    engine = RAGEngine("Sushil")
    print(engine.get_welcome_message())
    print("\n" + "=" * 60)

    # Test query
    result = engine.query("What is a good low-cost index fund for a moderate-risk investor?")
    print(f"\nAnswer:\n{result['answer']}")
    print(f"\nTrace: {result['trace']}")
