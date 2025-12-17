"""
Card Parser - Parse Markdown files into card objects
Follows Unix philosophy: do one thing well - parse text
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class CardType(Enum):
    """Card types supported by hashcards"""
    QA = "qa"  # Question-Answer
    CLOZE = "cloze"  # Cloze deletion


@dataclass
class Card:
    """Represents a single flashcard"""
    card_type: CardType
    content: Dict[str, str]
    deck_name: str
    line_number: int
    raw_text: str
    
    def get_hash(self) -> str:
        """Content-addressable: hash is based on content"""
        from .hasher import CardHasher
        return CardHasher.hash_card(self.raw_text)


class CardParser:
    """
    Parse Markdown files containing flashcards
    
    Format:
    Q: What is the atomic number of carbon?
    A: 6
    
    C: The atomic number of [carbon] is [6].
    """
    
    QA_PATTERN = re.compile(r'^Q:\s*(.+?)$\s*^A:\s*(.+?)$', re.MULTILINE | re.DOTALL)
    CLOZE_PATTERN = re.compile(r'^C:\s*(.+?)$', re.MULTILINE)
    CLOZE_DELETION = re.compile(r'\[([^\]]+)\]')
    
    @classmethod
    def parse_file(cls, filepath: str) -> List[Card]:
        """
        Parse a Markdown file and extract all cards
        
        Args:
            filepath: Path to the .md file
            
        Returns:
            List of Card objects
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        deck_name = cls._extract_deck_name(filepath)
        return cls.parse_content(content, deck_name)
    
    @classmethod
    def parse_content(cls, content: str, deck_name: str = "default") -> List[Card]:
        """
        Parse card content from string
        
        Args:
            content: Markdown text content
            deck_name: Name of the deck
            
        Returns:
            List of Card objects
        """
        cards = []
        
        # Parse Q&A cards
        for match in cls.QA_PATTERN.finditer(content):
            question = match.group(1).strip()
            answer = match.group(2).strip()
            line_num = content[:match.start()].count('\n') + 1
            
            card = Card(
                card_type=CardType.QA,
                content={"question": question, "answer": answer},
                deck_name=deck_name,
                line_number=line_num,
                raw_text=match.group(0)
            )
            cards.append(card)
        
        # Parse Cloze cards
        for match in cls.CLOZE_PATTERN.finditer(content):
            text = match.group(1).strip()
            line_num = content[:match.start()].count('\n') + 1
            
            # Find all cloze deletions
            deletions = cls.CLOZE_DELETION.findall(text)
            if deletions:
                card = Card(
                    card_type=CardType.CLOZE,
                    content={"text": text, "deletions": deletions},
                    deck_name=deck_name,
                    line_number=line_num,
                    raw_text=match.group(0)
                )
                cards.append(card)
        
        return cards
    
    @staticmethod
    def _extract_deck_name(filepath: str) -> str:
        """Extract deck name from file path"""
        import os
        return os.path.splitext(os.path.basename(filepath))[0]
    
    @staticmethod
    def format_cloze_for_display(text: str, reveal_index: Optional[int] = None) -> str:
        """
        Format cloze text for display
        
        Args:
            text: Original cloze text
            reveal_index: Which deletion to reveal (None = hide all)
            
        Returns:
            Formatted text with [...] or revealed content
        """
        deletions = CardParser.CLOZE_DELETION.findall(text)
        result = text
        
        for i, deletion in enumerate(deletions):
            if reveal_index is None or i != reveal_index:
                # Hide deletion
                result = result.replace(f"[{deletion}]", "[...]", 1)
            else:
                # Reveal deletion
                result = result.replace(f"[{deletion}]", f"**{deletion}**", 1)
        
        return result