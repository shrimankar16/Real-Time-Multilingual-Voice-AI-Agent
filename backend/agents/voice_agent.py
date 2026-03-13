"""LangChain tool-calling voice agent for clinical appointment booking."""
import logging
import re
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq

from app.config import GROQ_API_KEY, LLM_MODEL
from tools.appointment_tools import (
    book_appointment,
    cancel_appointment,
    get_available_slots,
    get_patient_history,
    reschedule_appointment,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Wrap raw functions as LangChain tools
# ---------------------------------------------------------------------------

@tool
def tool_get_available_slots(doctor_name: str, date: str = "") -> str:
    """Get available appointment slots for a doctor. Use date format YYYY-MM-DD if specified."""
    return get_available_slots(doctor_name, date)


@tool
def tool_book_appointment(
    patient_name: str,
    patient_phone: str,
    doctor_name: str,
    slot_time: str,
    language: str = "en",
) -> str:
    """Book a doctor appointment. slot_time must be in 'YYYY-MM-DD HH:MM' 24-hour format."""
    return book_appointment(patient_name, patient_phone, doctor_name, slot_time, language)


@tool
def tool_cancel_appointment(appointment_id: str) -> str:
    """Cancel an existing appointment by its ID."""
    return cancel_appointment(int(appointment_id))


@tool
def tool_reschedule_appointment(appointment_id: str, new_slot_time: str) -> str:
    """Reschedule an appointment to a new time. new_slot_time in 'YYYY-MM-DD HH:MM' format."""
    return reschedule_appointment(int(appointment_id), new_slot_time)


@tool
def tool_get_patient_history(patient_phone: str) -> str:
    """Get appointment history for a patient by their phone number."""
    return get_patient_history(patient_phone)


TOOLS = [
    tool_get_available_slots,
    tool_book_appointment,
    tool_cancel_appointment,
    tool_reschedule_appointment,
    tool_get_patient_history,
]

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a friendly and professional clinical receptionist AI for a multi-specialty clinic.

Your responsibilities:
1. Help patients book, reschedule, or cancel doctor appointments.
2. Check doctor availability and suggest alternative slots when there are conflicts.
3. Retrieve patient appointment history when asked.

Available doctors:
- Dr. Sharma — Cardiology
- Dr. Priya — Dermatology
- Dr. Ravi — Orthopedics

Appointment slots are every 30 minutes from 9 AM to 5 PM.

IMPORTANT RULES:
- Always ask for the patient's name and phone number before booking.
- If a slot is taken, suggest alternatives from the available slots.
- Never book in the past.
- Be concise and conversational.
- Respond in the SAME LANGUAGE the patient is speaking (English, Hindi, or Tamil).
- If the patient speaks Hindi, respond in Hindi. If Tamil, respond in Tamil.
- Use the tools provided to check availability and manage appointments.
- Always confirm details before finalizing a booking.

Current date/time context will be provided with each message."""

# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------

class VoiceAgent:
    """Stateful conversational agent with tool-calling capabilities."""

    def __init__(self) -> None:
        self.llm = ChatGroq(
            model=LLM_MODEL,
            api_key=GROQ_API_KEY,
            temperature=0.3,
        )
        self.llm_with_tools = self.llm.bind_tools(TOOLS)
        # Per-session conversation histories
        self._histories: dict[str, list] = {}

    def _get_history(self, session_id: str) -> list:
        if session_id not in self._histories:
            self._histories[session_id] = [SystemMessage(content=SYSTEM_PROMPT)]
        return self._histories[session_id]

    def process(self, session_id: str, user_text: str, language: str = "en") -> dict[str, Any]:
        """
        Process user input and return agent response with reasoning trace.

        Returns:
            {
                "response": str,
                "tool_calls": [{"tool": str, "args": dict, "result": str}, ...],
                "language": str,
            }
        """
        from datetime import datetime

        history = self._get_history(session_id)
        # Add context about current time
        time_context = f"[Current time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] [Patient language: {language}]"
        history.append(HumanMessage(content=f"{time_context}\n{user_text}"))

        tool_call_log: list[dict] = []
        max_iterations = 5  # safety limit

        for _ in range(max_iterations):
            response = self.llm_with_tools.invoke(history)
            history.append(response)

            # If no tool calls, we have the final answer
            if not response.tool_calls:
                break

            # Execute tool calls
            from langchain_core.messages import ToolMessage
            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                logger.info("🔧 Tool call: %s(%s)", tool_name, tool_args)

                # Find and execute the matching tool
                tool_fn = next((t for t in TOOLS if t.name == tool_name), None)
                if tool_fn:
                    result = tool_fn.invoke(tool_args)
                else:
                    result = f"Unknown tool: {tool_name}"

                tool_call_log.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "result": result,
                })
                logger.info("🔧 Tool result: %s", result[:200])

                history.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

        final_response = history[-1].content if isinstance(history[-1], AIMessage) else str(history[-1])

        # Clean up Groq/Llama 3 raw function call artifacts from text response
        final_response = re.sub(r"<function=.*?>.*?</function>", "", final_response, flags=re.DOTALL).strip()

        return {
            "response": final_response,
            "tool_calls": tool_call_log,
            "language": language,
        }


# Singleton agent instance
_agent: VoiceAgent | None = None


def get_agent() -> VoiceAgent:
    """Get or create the singleton VoiceAgent instance."""
    global _agent
    if _agent is None:
        _agent = VoiceAgent()
    return _agent
