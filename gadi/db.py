from contextlib import contextmanager
import os
import re

from sqlalchemy import create_engine
from sqlalchemy.orm import load_only, sessionmaker, aliased

from .models import Base, Law

# There's big variety in how paragraph names are formatted. This rule captures 88% of them as of 2020-10-01.
ARTICLE_NUM_REGEX = re.compile(
    # Optional article identifier, optionally followed by a space,
    r'((§|art|artikel|nr) ?)?'
    # and:
    # 1) bare numbers ("13"),
    # 2) roman numerals below 50 ("XIV"),
    # 3) 1/2 may be followed by 1 or 2 letters ("224b", "13mb")
    # 4) 1/2/3 may be followed by a single dot ("3.", "IX.", "7c.")
    # 5) two groups of 1/2/3 may be joined by a single dot in the middle ("12.31", "4a.03")
    r'(?P<article_num>([\dIVX]+\w{0,2}\.?){1,2})',
    re.IGNORECASE
)

db_uri = os.environ.get("DB_URI") or "postgresql://localhost:5432/gadi"
_engine = create_engine(db_uri)
Session = sessionmaker(bind=_engine)


def init_db():
    Base.metadata.create_all(_engine)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:  # noqa
        session.rollback()
        raise
    finally:
        session.close()


def all_laws(session):
    return session.query(Law).all()


def all_laws_load_only_gii_slug_and_source_timestamp(session):
    return session.query(Law).options(load_only("gii_slug", "source_timestamp")).all()


def laws_with_duplicate_slugs(session):
    law2 = aliased(Law)
    law_pairs_query = (
        session.query(Law, law2).
        join(law2, Law.slug == law2.slug).filter(Law.id != law2.id)
    )

    dupes = {}
    # Transform pairs to list per slug. (Needed in case more than 2 laws share a slug.)
    for law1, law2 in law_pairs_query:
        laws = dupes.setdefault(law1.slug, set())
        laws.add(law1)
        laws.add(law2)

    return [list(laws) for laws in dupes.values()]


def find_law_by_doknr(session, doknr):
    return session.query(Law).filter_by(doknr=doknr).first()


def find_law_by_slug(session, slug):
    return session.query(Law).filter_by(slug=slug).first()


def bulk_delete_laws_by_gii_slug(session, gii_slugs):
    Law.__table__.delete().where(Law.gii_slug.in_(gii_slugs))
