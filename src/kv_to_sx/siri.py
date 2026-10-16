"""SIRI-SX XML document generation and element construction."""

from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

from .xml_utils import strip_namespace

SIRI_NS = "http://www.siri.org.uk/siri"
XML_NS = "http://www.w3.org/XML/1998/namespace"

KNOWN_NAMESPACES: Dict[str, str] = {
    "": SIRI_NS,
    "kv17": "http://bison.connekt.nl/tmi8/kv17/msg",
    "kv15": "http://bison.connekt.nl/tmi8/kv15/msg",
    "kv8": "http://bison.connekt.nl/tmi8/kv8/msg",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

LOOKUP_NAMESPACES: Dict[str, str] = {
    "siri": SIRI_NS,
    **KNOWN_NAMESPACES,
}


# Standard sequence ordering of elements in PtSituationElementStructure
SIRI_ELEMENT_ORDER: List[str] = [
    "CreationTime",
    "CountryRef",
    "ParticipantRef",
    "SituationNumber",
    "UpdateStatus",
    "Version",
    "VersionedAtTime",
    "Source",
    "Progress",
    "QualityIndex",
    "ValidityPeriod",
    "Repetitions",
    "PublicationWindow",
    "AlertCause",
    "Priority",
    "Severity",
    "Summary",
    "Description",
    "Detail",
    "Advice",
    "Affects",
    "Consequences",
    "Extensions",
]


def resolve_qname(segment: str) -> str:
    """Resolve a path segment like 'kv17:PassageSequenceNumber' to an expanded QName."""
    if ":" in segment:
        prefix, local = segment.split(":", 1)
        uri = LOOKUP_NAMESPACES.get(prefix, f"http://bison.connekt.nl/tmi8/{prefix}/msg")
        return f"{{{uri}}}{local}"
    return f"{{{SIRI_NS}}}{segment}"



REPEATABLE_PARENT_TAGS = {"StopPoints", "Lines", "Operators", "StopPlaces"}
REPEATABLE_ITEM_TAGS = {"StopPoint", "Line", "Operator", "StopPlace"}


def set_target_path(
    parent: ET.Element,
    path: str,
    value: str,
    default_language: Optional[str] = None,
) -> None:
    """Set a value in parent element at the specified slash-separated path.

    Creates necessary intermediate container elements. Updates scalar leaf elements
    if already present, while creating new item elements for repeatable containers
    (such as StopPoints / StopPoint).
    """
    segments = [s.strip() for s in path.split("/") if s.strip()]
    if not segments:
        return

    current = parent
    for idx, seg in enumerate(segments[:-1]):
        qname = resolve_qname(seg)
        seg_clean = strip_namespace(qname)

        # For repeatable item containers like StopPoint under StopPoints
        if seg_clean in REPEATABLE_ITEM_TAGS:
            leaf_seg = segments[-1]
            leaf_qname = resolve_qname(leaf_seg)

            # Check if there is an existing item without this leaf
            chosen = None
            for child in current:
                if child.tag == qname and child.find(leaf_qname) is None:
                    chosen = child
                    break
            if chosen is None:
                chosen = ET.SubElement(current, qname)
            current = chosen
        else:
            # Container element: find existing or create new
            child = current.find(qname)
            if child is None:
                child = ET.SubElement(current, qname)
            current = child

    leaf_seg = segments[-1]
    leaf_qname = resolve_qname(leaf_seg)
    clean_leaf = strip_namespace(leaf_qname)
    parent_clean = strip_namespace(current.tag)

    # If leaf already exists under current non-repeatable container, update its text
    if parent_clean not in REPEATABLE_ITEM_TAGS and current.find(leaf_qname) is not None:
        leaf_elem = current.find(leaf_qname)
    else:
        leaf_elem = ET.SubElement(current, leaf_qname)

    leaf_elem.text = str(value)

    # Attach xml:lang to natural language text elements if configured
    if default_language and (clean_leaf in ("Description", "Summary", "Detail", "Advice") or parent_clean in ("Description", "Summary")):
        leaf_elem.set(f"{{{XML_NS}}}lang", default_language)



def _order_children(element: ET.Element, order: List[str]) -> None:
    """Sort children of an element according to schema sequence order."""
    order_map = {name.lower(): idx for idx, name in enumerate(order)}
    element[:] = sorted(
        element,
        key=lambda child: order_map.get(strip_namespace(child.tag).lower(), 999)
    )


def apply_defaults(situation: ET.Element, defaults: Dict[str, Any]) -> None:
    """Populate default situation fields from defaults configuration if not already set."""
    participant_ref = defaults.get("participant_ref")
    if participant_ref and situation.find(f"{{{SIRI_NS}}}ParticipantRef") is None:
        elem = ET.SubElement(situation, f"{{{SIRI_NS}}}ParticipantRef")
        elem.text = str(participant_ref)

    # Source / SourceType
    source_val = defaults.get("source")
    source_type = None
    if isinstance(source_val, dict):
        source_type = source_val.get("source_type")
    elif isinstance(source_val, str):
        source_type = source_val

    if source_type and situation.find(f"{{{SIRI_NS}}}Source") is None:
        source_elem = ET.SubElement(situation, f"{{{SIRI_NS}}}Source")
        st_elem = ET.SubElement(source_elem, f"{{{SIRI_NS}}}SourceType")
        st_elem.text = str(source_type)

    progress = defaults.get("progress")
    if progress and situation.find(f"{{{SIRI_NS}}}Progress") is None:
        elem = ET.SubElement(situation, f"{{{SIRI_NS}}}Progress")
        elem.text = str(progress)

    severity = defaults.get("severity")
    if severity and situation.find(f"{{{SIRI_NS}}}Severity") is None:
        elem = ET.SubElement(situation, f"{{{SIRI_NS}}}Severity")
        elem.text = str(severity)

    # Ensure CreationTime exists
    if situation.find(f"{{{SIRI_NS}}}CreationTime") is None:
        creation_time = ET.SubElement(situation, f"{{{SIRI_NS}}}CreationTime")
        creation_time.text = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def create_siri_document(
    situations: List[ET.Element],
    defaults: Dict[str, Any],
    timestamp: Optional[str] = None,
) -> ET.Element:
    """Wrap PtSituationElement list into a full SIRI-SX document with ServiceDelivery envelope."""
    for prefix, uri in KNOWN_NAMESPACES.items():
        ET.register_namespace(prefix, uri)

    now_iso = timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    siri = ET.Element(f"{{{SIRI_NS}}}Siri")
    siri.set("version", "2.0")

    service_delivery = ET.SubElement(siri, f"{{{SIRI_NS}}}ServiceDelivery")
    resp_time1 = ET.SubElement(service_delivery, f"{{{SIRI_NS}}}ResponseTimestamp")
    resp_time1.text = now_iso

    producer_ref = defaults.get("participant_ref")
    if producer_ref:
        prod_elem = ET.SubElement(service_delivery, f"{{{SIRI_NS}}}ProducerRef")
        prod_elem.text = str(producer_ref)

    status_elem = ET.SubElement(service_delivery, f"{{{SIRI_NS}}}Status")
    status_elem.text = "true"

    sx_delivery = ET.SubElement(service_delivery, f"{{{SIRI_NS}}}SituationExchangeDelivery")
    sx_delivery.set("version", "2.0")

    resp_time2 = ET.SubElement(sx_delivery, f"{{{SIRI_NS}}}ResponseTimestamp")
    resp_time2.text = now_iso

    situations_container = ET.SubElement(sx_delivery, f"{{{SIRI_NS}}}Situations")

    for sit in situations:
        apply_defaults(sit, defaults)
        _order_children(sit, SIRI_ELEMENT_ORDER)
        situations_container.append(sit)

    return siri


def serialize_siri_document(root: ET.Element) -> str:
    """Pretty-print and serialize SIRI XML document with XML declaration."""
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")
