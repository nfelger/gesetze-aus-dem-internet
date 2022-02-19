from invoke import task, Collection
from sqlalchemy.exc import OperationalError
import sqlalchemy_utils

from gadi import db, gesetze_im_internet
from gadi.gesetze_im_internet.download import location_from_string

ns = Collection()


# Database tasks

@task
def db_init(c):
    """
    Set up database. (Set DB url with the DB_URI env variable.)
    """
    try:
        db._engine.connect().execute('select 1')
    except OperationalError:
        sqlalchemy_utils.create_database(db.db_uri)

    db_migrate(c)


@task
def db_migrate(c):
    """
    Bring database up to date with the latest schema.
    """
    c.run("alembic upgrade head")


ns.add_collection(Collection(
    'database',
    init=db_init,
    migrate=db_migrate
))


# Tests

@task
def run_tests(c):
    """Run project test suite."""
    c.run("pytest")


ns.add_task(run_tests, 'tests')


# Ingest tasks

@task(
    help={
        "data-location": "Where to store downloaded law data"
    }
)
def download_laws(c, data_location):
    """
    Download any updated law files from gesetze-im-internet.de.
    """
    gesetze_im_internet.download_laws(location_from_string(data_location))


@task(
    help={
       "data-location": "Where law data has been downloaded"
    }
)
def ingest_data_from_location(c, data_location):
    """
    Process downloaded laws and store/update them in the DB.
    """
    with db.session_scope() as session:
        gesetze_im_internet.ingest_data_from_location(session, location_from_string(data_location))


ns.add_collection(Collection(
    'ingest',
    download_laws=download_laws,
    ingest_data=ingest_data_from_location
))


# Example JSON tasks

@task(
    help={
        "law-abbr": "The abbreviation of the law you want to generate (slugified)"
    }
)
def json_generate(c, law_abbr):
    """
    Update JSON response for a single law in example_json/.
    """
    with db.session_scope() as session:
        law = db.find_law_by_slug(session, law_abbr)
        if not law:
            raise Exception(f'Could not find law by slug "{law_abbr}". Has it been ingested yet?')
        gesetze_im_internet.write_law_json_file(law, "example_json")


@task
def json_generate_all(c):
    """
    Update JSON response for a all laws in example_json/.
    """
    for law_abbr in [
        "a_kae", "aag", "aaueg_aendg", "abfaev", "abv", "abwv", "agg", "aktg", "alg", "amg", "ao", "arbgg", "arbschg",
        "arbzg", "asylg", "aufenthg", "aufenthv", "baeausbv_2004", "baederfangausbv", "bafoeg", "bahnvorschranwg",
        "bakredsitzbek", "bapostg", "bartschv", "baugb", "baunvo", "bbg", "bdsg", "beeg", "betrvg", "bgb", "bgbeg", "burlg",
        "erbstdv", "estg", "gastg", "gbo", "gg", "gkg", "gmbhg", "gvg", "gwb", "gwg", "haftpflg", "heizkostenv", "hgb", "hwo",
        "ifg", "ifsg", "inso", "irg", "jfdg", "juschg", "krwg", "kschg", "kunsturhg", "kwg", "luftsig", "mabv", "markeng",
        "muschg", "owig", "partg", "patg", "pferdewmeistprv", "prodhaftg", "puag", "rog", "rpflg", "scheckg", "sgb_1",
        "sgb_2", "sgb_3", "sgb_4", "sgb_5", "sgb_6", "skaufg", "stgb", "stpo", "stvo", "stvollzg", "tierschg", "tkg", "tmg",
        "tvg", "urhg", "uschadg", "ustdv", "uwg", "vag", "vereinsg", "vgv", "vvg_infov", "vwvfg", "waffg", "wistrg_1954",
        "wogg", "zpo", "zvg", "zwvwv"
    ]:
        json_generate(c, law_abbr)


ns.add_collection(Collection(
    'example_json',
    generate=json_generate,
    **{'generate-all': json_generate_all}
))


# Deployment-related tasks

@task
def generate_static_assets(c, output_dir):
    """
    Generate and upload bulk law files.
    """
    with db.session_scope() as session:
        gesetze_im_internet.generate_static_assets(session, output_dir)


ns.add_collection(Collection(
    'deploy',
    generate_static_assets=generate_static_assets,
))
