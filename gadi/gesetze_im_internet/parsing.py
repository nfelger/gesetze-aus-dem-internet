import itertools
import xml.etree.ElementTree as ET

import declxml as xml
from declxml import _PrimitiveValue, _string_parser, _hooks_apply_after_parse
from lxml import etree

from .utils import chunk_string


class _XmlPreservingStringValue(_PrimitiveValue):
    """
    Hack to get at the element so we can serialize its content & children
    (instead of just getting the element text).
    Scaffolding copied from https://github.com/gatkin/declxml/blob/8cc2ff2fa813aa9d4c27d1964fe7d865029a1298/declxml.py
    """
    def parse_at_element(
        self,
        element,  # type: ET.Element
        state  # type: _ProcessorState
    ):
        # type: (...) -> Any
        """Parse the primitive value at the XML element."""
        if self._attribute:
            parsed_value = self._parse_attribute(element, self._attribute, state)
        else:
            serialised_element_content = "".join(
                itertools.chain([element.text or ""], (ET.tostring(child, encoding="unicode") for child in element))
            )
            parsed_value = self._parser_func(serialised_element_content, state)

        return _hooks_apply_after_parse(self._hooks, state, parsed_value)


def node_as_string(
    element_name,  # type: Text
    attribute=None,  # type: Optional[Text]
    required=True,  # type: bool
    alias=None,  # type: Optional[Text]
    default='',  # type: Optional[Text]
    omit_empty=False,  # type: bool
    strip_whitespace=True,  # type: bool
    hooks=None  # type: Optional[Hooks]
):
    # type: (...) -> Processor
    """
    Custom processor for extractingXml nodes as strings. Used because some
    fields contain embedded tags.
    :param strip_whitespace: Indicates whether leading and trailing whitespace should be stripped
        from parsed string values.
    """

    value_parser = _string_parser(strip_whitespace)
    return _XmlPreservingStringValue(
        element_name,
        value_parser,
        attribute,
        required,
        alias,
        default,
        omit_empty,
        hooks
    )


EMPTY_CONTENT_PATTERNS = ["<P/>", "<P />", "<P>-</P>"]
def _content_string_hooks_after_parse(_, text):
    if text == '' or any(text == pat for pat in EMPTY_CONTENT_PATTERNS):
        return None
    return text

content_string_hooks = xml.Hooks(after_parse=_content_string_hooks_after_parse)

text_processor = xml.dictionary("textdaten/text", [
        node_as_string("Content", required=False, hooks=content_string_hooks),
        node_as_string("TOC", required=False, default=None),
        node_as_string("Footnotes", required=False, default=None),
    ], required=False, alias="text")

header_norm_processor = xml.dictionary("norm", [
    xml.array(xml.string("metadaten/jurabk", alias="jurabk")),
    xml.array(xml.string("metadaten/amtabk", alias="amtabk", required=False)),
    xml.string("metadaten/ausfertigung-datum", alias="first_published"),
    xml.string(".", attribute="doknr"),
    xml.string(".", attribute="builddate", alias="source_timestamp"),
    node_as_string("metadaten/langue", alias="title_long"),
    node_as_string("metadaten/kurzue", alias="title_short", required=False, default=None),
    text_processor,
    xml.array(xml.dictionary("metadaten/fundstelle", [
        xml.string("periodikum", alias="periodical"),
        xml.string("zitstelle", alias="reference")
    ], required=False), alias="publication_info"),
    xml.array(xml.dictionary("metadaten/standangabe", [
        xml.string("standtyp", alias="category"),
        node_as_string("standkommentar", alias="comment")
    ], required=False), alias="status_info"),
    node_as_string("textdaten/fussnoten/Content", required=False, default=None, alias="notes_documentary_footnotes", hooks=content_string_hooks),
])

body_norm_processor = xml.dictionary("norm", [
    xml.string(".", attribute="doknr"),
    text_processor,
    node_as_string("textdaten/fussnoten/Content", required=False, default=None, alias="documentary_footnotes", hooks=content_string_hooks),
    xml.string("metadaten/enbez", alias="name", required=False, default=None),
    node_as_string("metadaten/titel", alias="title", required=False, default=None, hooks=content_string_hooks),
    xml.dictionary("metadaten/gliederungseinheit", [
        xml.string("gliederungskennzahl", alias="code"),
        xml.string("gliederungsbez", alias="name"),
        node_as_string("gliederungstitel", alias="title", required=False, default=None, hooks=content_string_hooks),
    ], required=False, alias="section_info")
])


def load_norms_from_file(file_or_filepath):
    if hasattr(file_or_filepath, "read"):
        doc = etree.parse(file_or_filepath)
    else:
        with open(file_or_filepath) as f:
            doc = etree.parse(f)

    return doc.xpath("/dokumente/norm")


def apply_transformer(dict, transform_func, replace=None, read=None):
    args = [dict.pop(key) for key in replace or []] + [dict[key] for key in read or []]
    new_entries = transform_func(*args)
    dict.update(new_entries)


def transform_notes_text(text_dict):
    return {
        "notes_body": text_dict.get("Content") or text_dict.get("TOC"),
        "notes_footnotes": text_dict.get("Footnotes")
    }


def transform_text(text_dict):
    return {
        "body": text_dict.get("Content") or text_dict.get("TOC"),
        "footnotes": text_dict.get("Footnotes")
    }


def transform_abbreviations(amtabk, jurabk):
    primary, *rest = list(dict.fromkeys(amtabk + jurabk))
    return {
        "abbreviation": primary,
        "extra_abbreviations": rest,
    }


def transform_item_type(doknr, body):
    if "NE" in doknr:
        return { "item_type": "article" }
    elif "NG" in doknr:
        if body:
            return { "item_type": "heading_article" }
        else:
            return { "item_type": "heading" }
    else:
        raise Exception(f"Unknown norm structure encountered: {doknr}")


def transform_name_and_title(section_info, name, title, item_type):
    if item_type == "article":
        return {
            "name": name,
            "title": title,
        }
    else:
        return {
            "name": section_info["name"],
            "title": section_info["title"],
        }


def _find_parent(sections_by_code, code):
    """
    Search by iteratively removing 3 digits from the end of the code to find a
    match among already-added sections.
    """
    chunks = chunk_string(code, 3)
    for i in reversed(range(len(chunks) + 1)):
        substring = "".join(chunks[:i])
        if sections_by_code.get(substring):
            return sections_by_code[substring]
    return None


def _set_parent(item, parser_state):
    code = item["section_info"] and item["section_info"]["code"]

    if item["item_type"] == "article":
        if code:
            item["parent"] = _find_parent(parser_state["sections_by_code"], code)
        else:
            item["parent"] = parser_state["current_parent"]

    else:
        item["parent"] = _find_parent(parser_state["sections_by_code"], code)
        parser_state["sections_by_code"][code] = parser_state["current_parent"] = item

    if item["parent"]:
        parser_state["items_with_children"].add(item["parent"]["doknr"])


def extract_law_attrs(header_norm):
    law_dict = xml.parse_from_string(header_norm_processor, etree.tostring(header_norm, encoding="unicode"))
    apply_transformer(
        law_dict, transform_notes_text, replace=["text"]
    )
    apply_transformer(
        law_dict, transform_abbreviations, replace=["amtabk", "jurabk"]
    )

    return law_dict


def extract_contents(body_norms):
    parser_state = {
        "current_parent": None,
        "sections_by_code": {"": None},
        "items_with_children": set(),
    }

    content_items = []
    for norm in body_norms:
        item = xml.parse_from_string(body_norm_processor, etree.tostring(norm, encoding="unicode"))
        apply_transformer(
            item, transform_text, replace=["text"],
        )
        apply_transformer(
            item, transform_item_type, read=["doknr", "body"]
        )
        _set_parent(item, parser_state)
        apply_transformer(
            item, transform_name_and_title, replace=["section_info", "name", "title"], read=["item_type"]
        )
        content_items.append(item)

    # Convert empty heading articles to articles
    for item in content_items:
        if item["item_type"] == "heading_article" and item["doknr"] not in parser_state["items_with_children"]:
            item["item_type"] = "article"

    return content_items


def parse_law(file_or_filepath):
    header_norm, *body_norms = load_norms_from_file(file_or_filepath)

    law_attrs = extract_law_attrs(header_norm)
    law_attrs["contents"] = extract_contents(body_norms)

    return law_attrs
