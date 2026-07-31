import logging
from typing import TypedDict, Dict, Any, Tuple
from datetime import datetime
from langgraph.graph import StateGraph, END
from pipeline.llm_manager import LLMManager
from pipeline.prompts import CONSOLIDATE_PROMPT, SEGMENT_PROMPT, GENERATE_NOTES_PROMPT, GENERATE_ANKI_PROMPT

logger = logging.getLogger(__name__)

class PipelineState(TypedDict):
    ocr_text: str
    transcription_text: str
    consolidated_text: str
    segmented_text: str
    final_notes: str
    anki_csv: str
    # Parameters for prompt formatting
    title: str
    date: str
    subject: str
    generate_anki: bool

class EIRNotesGraph:
    """Manages the LangGraph agent workflow for generating structured EIR nursing notes and Anki CSV cards."""
    
    def __init__(self):
        self.llm = LLMManager()
        self.workflow = StateGraph(PipelineState)
        self._build_graph()
        
    def _build_graph(self):
        # Add nodes
        self.workflow.add_node("consolidate", self.consolidate_node)
        self.workflow.add_node("segment", self.segment_node)
        self.workflow.add_node("generate_notes", self.generate_notes_node)
        self.workflow.add_node("generate_anki", self.generate_anki_node)
        
        # Set edges: consolidate -> segment -> generate_notes & generate_anki
        self.workflow.set_entry_point("consolidate")
        self.workflow.add_edge("consolidate", "segment")
        self.workflow.add_edge("segment", "generate_notes")
        self.workflow.add_edge("segment", "generate_anki")
        self.workflow.add_edge("generate_notes", END)
        self.workflow.add_edge("generate_anki", END)
        
        # Compile
        self.app = self.workflow.compile()
        
    def consolidate_node(self, state: PipelineState) -> Dict[str, Any]:
        logger.info("LangGraph: Running consolidation node...")
        user_content = (
            f"--- TEXTO DE DIAPOSITIVAS (OCR) ---\n{state['ocr_text']}\n\n"
            f"--- TRANSCRIPCIÓN DEL AUDIO ---\n{state['transcription_text']}"
        )
        consolidated = self.llm.process_node(CONSOLIDATE_PROMPT, user_content)
        return {"consolidated_text": consolidated}
        
    def segment_node(self, state: PipelineState) -> Dict[str, Any]:
        logger.info("LangGraph: Running segmentation node...")
        segmented = self.llm.process_node(SEGMENT_PROMPT, state["consolidated_text"])
        return {"segmented_text": segmented}
        
    def generate_notes_node(self, state: PipelineState) -> Dict[str, Any]:
        logger.info("LangGraph: Running notes generation node...")
        # Format the template with state parameters
        system_prompt = GENERATE_NOTES_PROMPT.format(
            title=state.get("title", "Apuntes de Clase"),
            date=state.get("date", datetime.now().strftime("%Y-%m-%d")),
            subject=state.get("subject", "Metodología")
        )
        notes = self.llm.process_node(system_prompt, state["segmented_text"])
        return {"final_notes": notes}
        
    def generate_anki_node(self, state: PipelineState) -> Dict[str, Any]:
        if not state.get("generate_anki", True):
            logger.info("LangGraph: Skipping Anki flashcards generation (disabled by configuration/user).")
            return {"anki_csv": ""}
        logger.info("LangGraph: Running Anki flashcards generation node...")
        anki_csv = self.llm.process_node(GENERATE_ANKI_PROMPT, state["segmented_text"])
        return {"anki_csv": anki_csv}
        
    def run(self, ocr_content: str, transcription_content: str, title: str = "Apuntes de Clase", date: str = "", subject: str = "Metodología", generate_anki: bool = True) -> Tuple[str, str]:
        """Executes the compiled graph and returns both study notes (Markdown) and Anki cards (CSV)."""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            
        initial_state = {
            "ocr_text": ocr_content,
            "transcription_text": transcription_content,
            "consolidated_text": "",
            "segmented_text": "",
            "final_notes": "",
            "anki_csv": "",
            "title": title,
            "date": date,
            "subject": subject,
            "generate_anki": generate_anki
        }
        
        logger.info("Starting LangGraph workflow execution...")
        result = self.app.invoke(initial_state)
        logger.info("LangGraph workflow completed.")
        return result["final_notes"], result["anki_csv"]
