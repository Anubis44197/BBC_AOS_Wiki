from typing import Dict, Any, Tuple
from bbc_aos.knowledge.human.note_record import NoteRecord

class NoteParser:
    """
    Parses frontmatter tags and serializes NoteRecords to standard formats.
    """
    def parse_markdown(self, content: str) -> Tuple[Dict[str, Any], str]:
        """
        Extracts YAML frontmatter dictionary and raw markdown text body.
        
        Args:
            content: Raw string content of the note file.
            
        Returns:
            Tuple of (frontmatter dictionary, body content string).
        """
        return {}, content

    def serialize_note(self, record: NoteRecord) -> str:
        """
        Converts a NoteRecord instance into a markdown string containing YAML frontmatter.
        
        Args:
            record: NoteRecord instance.
            
        Returns:
            Formated markdown file content string.
        """
        return ""
