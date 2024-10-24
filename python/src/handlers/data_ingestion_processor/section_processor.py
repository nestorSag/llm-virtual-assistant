"""
module usage:

from section_processor import SectionedDocumentParser

parser = SectionedDocumentParser(
    max_chunk_length=500, # maximum number of words allowed in a chunk
)
chunks = parser.split(text)
"""
import re
import warnings
from typing import List
from functools import total_ordering
from packaging.version import Version

import logging

class NoSectionsFound(Exception):
    pass

@total_ordering
class DottedSection:
    """
    This class handles document sections with formats like:

    1.2.3 Section Title
    * Note title has to be capitalised , with the exception of a few stopwords

    This class allow hierarchical and order comparison between sections, e.g.
    DottedSection("1.2.3 Title One") < DottedSection("1.2.4 Title Two") # True
    DottedSection("1.2.3 Title One").is_child_of(DottedSection("1.2 Title Two")) # True

    It also allows to build a traversable tree of sections through its parent, children and right_sibling attributes.

    In order to build parsers for different sectioning formats, subclass this class and override
    the regexes. Override the comparison methods (such as `is_child_of`) if necessary. Note all of the methods
    in this class are expected for it (overriden or not) in order to work.
    """

    numbering_regex = r"\d+(\.\d+)*"
    stopwords = ["the", "or", "and", "to", "in", "on", "at", "of", "for"]
    first_title_word_regex = r"\s[A-Z(][a-zA-Z0-9)/+-]*"
    following_title_words_regex = r'(\s([A-Z(][a-zA-Z0-9)/+-]*|' + "|".join(stopwords) + r'))*'
    section_regex = r'^\s+(' + numbering_regex + first_title_word_regex + following_title_words_regex + r')$'

    def __init__(
        self,
        title: str,
        content: str = None,
        parent: "DottedSection" = None,
    ):
    
        self.title = title
        self.content = content
        self.children = []
        self.right_sibling = None
        self.parent = parent

    def add_child(self, child: "DottedSection"):
        self.children.append(child)
        child.parent = self
        return self
    
    def set_right_sibling(self, right_sibling: "DottedSection"):
        if self.right_sibling is not None:
            warnings.warn("Setting right sibling when it already exists")
        self.right_sibling = right_sibling
        return self
    
    def set_parent(self, parent: "DottedSection"):
        if self.parent is not None:
            warnings.warn("Setting parent when it already exists")
        self.parent = parent
        return self
    
    def get_children(self):
        return self.children
    
    def get_right_sibling(self):
        return self.right_sibling
    
    def get_parent(self):
        return self.parent
    
    @property
    def number(self):
        return re.match(self.numbering_regex, self.title).group(0)
    
    def __eq__(self, other):
        return self.number == other.number
    
    def __lt__(self, other):
        return Version(self.number) < Version(other.number)
    
    def is_child_of(self, other: "DottedSection") -> bool:
        """Returns True if this section is a child of the other section
        """        
        self_numbering = list(map(int, self.number.split('.')))
        other_numbering = list(map(int, other.number.split('.')))
        # Check if the child starts with the parent parts
        return other_numbering == self_numbering[:len(other_numbering)] and self != other
    
    def is_parent_of(self, other: "DottedSection") -> bool:
        """Returns True if this section is a parent of the other section
        """        
        return other.is_child_of(self)
    
    def is_left_sibling_of(self, other: "DottedSection") -> bool:
        """Returns True if this section is a left sibling of the other section
        """        
        self_numbering = list(map(int, self.number.split('.')))
        other_numbering = list(map(int, other.number.split('.')))
        return other_numbering[:-1] == self_numbering[:-1] and other_numbering[-1] > self_numbering[-1]
    
    def is_right_sibling_of(self, other: "DottedSection") -> bool:
        """Returns True if this section is a right sibling of the other section
        """
        self_numbering = list(map(int, self.number.split('.')))
        other_numbering = list(map(int, other.number.split('.')))
        return other_numbering[:-1] == self_numbering[:-1] and other_numbering[-1] < self_numbering[-1]
    
    def search(self, title: str) -> "DottedSection":
        """Returns the section node with the given title, or None if it doesn't exist

        """        
        if self.title == title:
            return self
        for child in self.children:
            result = child.search(title)
            if result is not None:
                return result
        result = self.right_sibling.search(title) if self.right_sibling is not None else None
        if result is not None:
            return result
        return None
    
    def get_contextualised_content(self):
        """Augments a node's content with its section lineage with the format:
        In section 1 Section -> 1.1 Subsection -> 1.1.1 Subsubsection, part 1/1: 

        Returns
        -------
        _type_
            _description_
        """        
        parent_sections = []
        current = self
        while current is not None:
            parent_sections.append(current.title)
            current = current.parent
        return "In section: " + " -> ".join(list(reversed(parent_sections))) + ", part 1/1:\n" + self.content



class SectionedDocumentParser:
    """
    This class splits a document mimicking its (possibly nested) section structure, where each section is mapped to
    one or more chunks (depending on the maximum allowed chunk size). The chunks are enriched with the full lineage
    of the section they belong to in the top line, the top line has the format:
    In section: 1 Section -> 1.1 Subsection -> 1.1.1 Subsubsection, part 1/1

    The parsing of different sectioning formats is handled by the passed `section_parser` argument.
    For different sectioning formats, you will have to subclass `DottedSection` and pass the new class as the `section_parser` argument.
    """
    numbering_regex = r"\d+(\.\d+)*"
    
    def __init__(
        self,
        section_parser: DottedSection = None,
        max_chunk_length: int = 500,
    ):
        """

        Parameters
        ----------
        section_parser : DottedSection, optional
            Class that splits the document based on specific sectioning formats, by default `DottedSection`
        max_chunk_length : int, optional
            Maximum number of words allowed in a chunk, by default 1000
        """        
        self.sectioner = section_parser or DottedSection
        self.max_chunk_length = max_chunk_length

    def validate_extracted_sections(self, sections: List[str]) -> list[str]:
        # no all caps titles
        valid_sections = [section for section in sections if not section.isupper()]
        # no sections numbered higher than 99
        def numbers_are_valid(section):
            numbers = re.match(self.numbering_regex, section).group(0).split(".")
            return all([len(_) <= 2 for _ in numbers])
        valid_sections = [section for section in valid_sections if numbers_are_valid(section)]
        if len(valid_sections) == 0:
            raise NoSectionsFound("No valid sections found in text")
        return valid_sections
    
    def extract_sections(self, text: str) -> List[str]:
        sections = [groups[0] for groups in re.findall(self.sectioner.section_regex, text, re.MULTILINE)]
        if len(sections) == 0:
            raise NoSectionsFound("No sections found in text")
        return sections
    
    def build_section_tree(self, titles: str) -> DottedSection:
        root = self.sectioner(title=titles[0])
        current_section = root
        for title in titles[1:]:
            new_section = self.sectioner(title)
            if new_section.is_child_of(current_section):
                current_section.children.append(new_section)
                new_section.parent = current_section
            elif new_section.is_right_sibling_of(current_section):
                current_section.right_sibling = new_section
                new_section.parent = current_section.parent
            else:
                # backtrack to find the parent.
                while not (new_section.is_child_of(current_section) or current_section.parent is None):
                    current_section = current_section.parent
                if new_section.is_child_of(current_section):
                    current_section.children.append(new_section)
                    new_section.parent = current_section
                else:
                    # current_section is at root level
                    if new_section.is_right_sibling_of(current_section):
                        current_section.right_sibling = new_section
                        new_section.parent = current_section.parent
                    # if not, discard the section as there can't be a left sibling at this point
                    else:
                        logging.info(f"Discarding section {new_section.title}")
                        continue
            parent_title = new_section.parent.title if new_section.parent is not None else "(no parent section)"
            logging.info(f"{parent_title} -> {new_section.title}")
            current_section = new_section
        return root
    
    def enrich_section_chunks(self, text: str, get_tree: bool = False) -> List[str]:
        """Adds the section lineage to each chunk

        Parameters
        ----------
        text : str
            Document's text
        get_tree : bool, optional
            Whether to return the section tree, by default False

        Returns
        -------
        List[str]
            List of enriched chunks
        """        
        section_titles = self.extract_sections(text)
        valid_titles = self.validate_extracted_sections(section_titles)
        sorted_titles = sorted(valid_titles, key=lambda x: DottedSection(x))

        root = self.build_section_tree(sorted_titles)
        for current_section, next_section in zip(sorted_titles, sorted_titles[1:]):
            # find first occurrence of current_section in text
            current_section_start = text.find(current_section)
            next_section_start = text.find(next_section)
            chunk = text[current_section_start:next_section_start]
            chunk_node = root.search(current_section)
            chunk_node.content = chunk

        chunks = []
        for section in sorted_titles:
            node = root.search(section)
            if node.content is not None:
                chunks.append(node.get_contextualised_content())
            else:  
                warnings.warn(f"Section {section} has no content")
        
        if not get_tree:
            return chunks
        else:
            return chunks, root
    
    def word_count(self, text: str):
        return len(text.split())
    
    def split(self, text: str) -> List[str]:
        """Split a document by sections, ensuring that each chunk has at most `max_chunk_length` words.
        For sections that are longer than `max_chunk_length`, the section is split into smaller chunks, preserving entire lines
        to avoid splitting paragraphs. The first line of each chunk is the updated section lineage where part 1/1 is replaced by part k/n.
        If a single line in a section is longer than `max_chunk_length`, a ValueError is raised.

        Parameters
        ----------
        text : str
            Document's text

        Returns
        -------
        List[str]
            List of chunks
        """        
        valid_chunks = []
        chunks = self.enrich_section_chunks(text)
        for chunk in chunks:
            if self.word_count(chunk) <= self.max_chunk_length:
                valid_chunks.append(chunk)
            else:
                # create sub chunks by stringing together lines until the max_chunk_length is reached
                # this is to avoid splitting paragraphs as much as possible
                # as well as to preserve the original document as much as possible
                # the first line of the chunk is the updated section lineage where part 1/1 is replaced by part k/n
                lines = chunk.split("\n")
                section_lineage = lines[0] # first line is the section lineage
                lineage_length = self.word_count(section_lineage)
                adjusted_max_length = self.max_chunk_length - lineage_length
                lines = lines[1:] # content lines (not lineage)
                if any([self.word_count(line) > adjusted_max_length for line in lines]):
                    raise ValueError(f"Single line in section {section_lineage} is longer than {adjusted_max_length=}")
                sub_chunks = []
                while len(lines) > 0:
                    current_chunk = ""
                    current_len = 0
                    while len(lines) > 0 and current_len + self.word_count(lines[0]) <= adjusted_max_length:
                        new_line = lines.pop(0)
                        current_chunk += new_line + "\n"
                        current_len += self.word_count(new_line)
                    sub_chunks.append(current_chunk)
                for k, sub_chunk in enumerate(sub_chunks):
                    updated_section_lineage = section_lineage.replace("part 1/1", f"part {k + 1}/{len(sub_chunks)}")
                    valid_chunks.append(updated_section_lineage + "\n" + sub_chunk)
        return valid_chunks
                
                # split into smaller chunks
                

# if __name__ == "__main__":
#     with open("/Users/nestorsanchez/Downloads/Centura 200mm Maintenance and Calibration Manual - extracted.txt", "r") as file:
#         text = file.read()
    
#     from pathlib import Path
#     parser = SectionedDocumentParser()
#     chunks = parser.split(text)
#     output_dir = Path("/Users/nestorsanchez/Downloads/Centura 200mm Maintenance and Calibration Manual - chunks")
#     Path(output_dir).mkdir(exist_ok=True)
#     for k, chunk in enumerate(chunks):
#         with open(output_dir / f"chunk-{k}.txt", "w") as file:
#             file.write(chunk)

