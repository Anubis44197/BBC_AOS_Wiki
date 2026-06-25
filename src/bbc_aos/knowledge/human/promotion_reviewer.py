from typing import Callable, Optional
from bbc_aos.knowledge.human.note_record import NoteRecord

class PromotionReviewer:
    """
    Evaluates note promotion requests, requiring manual/human approval callbacks.
    """
    def __init__(self, approval_callback: Optional[Callable[[NoteRecord], bool]] = None) -> None:
        """
        Args:
            approval_callback: Optional callable for approving the note.
        """
        self._approval_callback = approval_callback

    def review_promotion(self, note: NoteRecord) -> bool:
        """
        Invokes approval procedures to promote a note to Semantic Memory.
        
        Args:
            note: NoteRecord targeted for promotion.
            
        Returns:
            True if promotion is approved, False otherwise.
        """
        if self._approval_callback:
            return self._approval_callback(note)
        return False
