"""XML utility functions for parsing, searching, and namespace handling."""

import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple

from .exceptions import XmlParseError


def strip_namespace(tag: str) -> str:
    """Strip XML namespace prefix from a tag, e.g. '{http://...}tag' -> 'tag'."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def parse_xml(content: str) -> ET.Element:
    """Parse XML string into an ElementTree Element, raising XmlParseError on failure."""
    try:
        return ET.fromstring(content)
    except Exception as e:
        raise XmlParseError(f"Failed to parse input XML: {e}") from e


def _match_children(parent: ET.Element, segment: str) -> List[ET.Element]:
    """Find all direct children of parent whose tag (without namespace) matches segment."""
    return [
        child for child in parent
        if strip_namespace(child.tag).lower() == segment.lower()
    ]


def find_elements_by_path(root: ET.Element, path: str) -> List[ET.Element]:
    """Find all elements in an XML tree matching a slash-separated path.

    Path matching is namespace-agnostic and resilient to wrappers:
    - If the first segment matches the root element itself, search continues with children.
    - If the root element does not match the first segment, search looks for the first segment
      among direct children or descendants.
    - If the path starts with parent wrappers not present in the tree, but the root matches
      an intermediate segment, search proceeds from the root.
    """
    segments = [s.strip() for s in path.split("/") if s.strip()]
    if not segments:
        return [root]

    root_tag = strip_namespace(root.tag).lower()

    # Case 1: Root tag matches an intermediate segment in the path
    # e.g. path is TimingPoint/KV8generalmessages/GENERALMESSAGEUPDATE
    # and root is KV8generalmessages
    for idx, seg in enumerate(segments):
        if seg.lower() == root_tag:
            remaining = segments[idx + 1:]
            if not remaining:
                return [root]
            current_nodes = [root]
            for next_seg in remaining:
                next_nodes = []
                for node in current_nodes:
                    next_nodes.extend(_match_children(node, next_seg))
                current_nodes = next_nodes
                if not current_nodes:
                    break
            if current_nodes:
                return current_nodes

    # Case 2: Root tag matches first segment
    if root_tag == segments[0].lower():
        start_nodes = [root]
        remaining = segments[1:]
    else:
        # Search direct children first
        start_nodes = _match_children(root, segments[0])
        # If not found in direct children, search all descendants for first segment
        if not start_nodes:
            start_nodes = [
                desc for desc in root.iter()
                if strip_namespace(desc.tag).lower() == segments[0].lower()
            ]
        remaining = segments[1:]

    current_nodes = start_nodes
    for seg in remaining:
        next_nodes = []
        for node in current_nodes:
            next_nodes.extend(_match_children(node, seg))
        current_nodes = next_nodes
        if not current_nodes:
            break

    return current_nodes


def find_first_element_by_path(root: ET.Element, path: str) -> Optional[ET.Element]:
    """Find the first element matching path, or None if not found."""
    matches = find_elements_by_path(root, path)
    return matches[0] if matches else None


def get_element_text(element: Optional[ET.Element]) -> Optional[str]:
    """Get the stripped text of an element, or None if missing or empty."""
    if element is None:
        return None
    if element.text is None:
        return ""
    return element.text.strip()


def extract_element_context(element: ET.Element) -> Dict[str, str]:
    """Extract a dictionary of child tag values and attributes for template substitution."""
    context: Dict[str, str] = {}
    for attr, val in element.attrib.items():
        clean_attr = strip_namespace(attr)
        context[clean_attr] = str(val)

    for child in element:
        tag = strip_namespace(child.tag)
        text = child.text.strip() if child.text else ""
        context[tag] = text

    return context


def detect_message_type(root: ET.Element, candidate_messages: List[str]) -> Optional[str]:
    """Detect which candidate source message type matches the given XML element tree."""
    root_tag = strip_namespace(root.tag).lower()

    # Exact or substring match on root tag
    for cand in candidate_messages:
        cand_lower = cand.lower()
        if root_tag == cand_lower or cand_lower.startswith(root_tag) or root_tag.startswith(cand_lower):
            return cand

    # Search for candidate tag among all elements in the document
    all_tags = {strip_namespace(el.tag).lower() for el in root.iter()}
    for cand in candidate_messages:
        cand_lower = cand.lower()
        for tag in all_tags:
            if tag == cand_lower or (cand_lower == "kv15" and "kv15" in tag):
                return cand

    # Fallback: check which candidate message has elements in the tree
    for cand in candidate_messages:
        if cand.lower() in ("kv17", "kv17cvlinfo"):
            if any("kv17" in t for t in all_tags):
                return cand
        elif cand.lower() in ("kv8", "kv8generalmessages", "kv78"):
            if any("kv8" in t or "generalmessage" in t for t in all_tags):
                return cand
        elif cand.lower() in ("kv15", "kv15messages"):
            if any("kv15" in t or "stopmessage" in t for t in all_tags):
                return cand

    # If there is only one message type defined in config, default to it
    if len(candidate_messages) == 1:
        return candidate_messages[0]

    return None

