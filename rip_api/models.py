import re

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


def _slugify(string):
    string = string.lower()
    # Transcribe umlauts etc.
    for orig, repl in [("ß", "ss"), ("ä", "ae"), ("ö", "oe"), ("ü", "ue")]:
        string = string.replace(orig, repl)
    # Replace other characters with underscore
    string = re.sub("[^a-z0-9]", "_", string)
    # Collapse consecutive underscores
    string = re.sub("_+", "_", string)
    return string


class Law(Base):
    __tablename__ = "laws"

    id = Column(Integer, primary_key=True)
    doknr = Column(String, nullable=False, unique=True)
    slug = Column(String, nullable=False, index=True)
    gii_slug = Column(String, nullable=False, index=True)
    abbreviation = Column(String, nullable=False)
    extra_abbreviations = Column(postgresql.ARRAY(String), nullable=False)
    first_published = Column(String, nullable=False)
    source_timestamp = Column(String, nullable=False)
    heading_long = Column(String, nullable=False)
    heading_short = Column(String)
    publication_info = Column(postgresql.JSONB, nullable=False)
    status_info = Column(postgresql.JSONB, nullable=False)
    notes = Column(postgresql.JSONB)
    attachment_names = Column(postgresql.ARRAY(String), nullable=False)

    contents = relationship(
        "ContentItem",
        back_populates="law",
        order_by="ContentItem.order",
        cascade="all, delete, delete-orphan",
        passive_deletes=True
    )

    @staticmethod
    def from_dict(law_dict, gii_slug):
        law = Law(
            slug=_slugify(law_dict["abbreviation"]),
            gii_slug=gii_slug,
            **{k: v for k, v in law_dict.items() if k != "contents"}
        )

        content_item_dicts = law_dict["contents"]
        content_items_by_doknr = {}
        for idx, content_item_dict in enumerate(content_item_dicts):
            parent_dict = content_item_dict["parent"]
            parent = parent_dict and content_items_by_doknr[parent_dict["doknr"]]

            content_item_attrs = {k: v for k, v in content_item_dict.items() if k != "parent"}
            content_item = ContentItem(parent=parent, order=idx, **content_item_attrs)
            law.contents.append(content_item)
            content_items_by_doknr[content_item.doknr] = content_item

        return law


class ContentItem(Base):
    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True)
    doknr = Column(String, nullable=False, unique=True)
    item_type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    title = Column(String)
    body = Column(postgresql.JSONB)
    documentary_footnotes = Column(String)
    content_level = Column(Integer, nullable=False)
    law_id = Column(Integer, ForeignKey("laws.id", ondelete="CASCADE"), index=True)
    parent_id = Column(Integer, ForeignKey("content_items.id"))
    order = Column(Integer, nullable=False)

    law = relationship("Law", back_populates="contents")
    parent = relationship("ContentItem", remote_side=[id], uselist=False)
