# Test Coverage Analysis

**Date**: 2026-01-15
**Overall Coverage**: 57%

## Executive Summary

This document analyzes the test coverage of the gesetze-aus-dem-internet codebase and proposes specific improvements. The current test suite has good coverage for XML parsing (96%) but significant gaps in download, ingestion, database, and frontend code.

## Current Coverage Status

| Module | Statements | Missing | Coverage |
|--------|-----------|---------|----------|
| `gadi/gesetze_im_internet/parsing.py` | 95 | 4 | **96%** ✓ |
| `gadi/api_schemas.py` | 125 | 31 | **75%** |
| `gadi/models.py` | 74 | 22 | **70%** |
| `gadi/db.py` | 39 | 21 | **46%** |
| `gadi/gesetze_im_internet/download.py` | 81 | 57 | **30%** |
| `gadi/gesetze_im_internet/__init__.py` | 117 | 94 | **20%** |
| **TOTAL** | **537** | **229** | **57%** |

## Current Test Suite

The project has 2 test files:
- `tests/test_parsing.py`: Tests XML parsing functionality (1 test, excellent coverage)
- `tests/test_json_generation_e2e.py`: End-to-end tests (5 parametrized tests, requires PostgreSQL)

## Recommendations by Priority

### 1. HIGH PRIORITY: Download Module (30% coverage)
**File**: `gadi/gesetze_im_internet/download.py`

**Missing coverage:**
- `fetch_toc()` - Fetches table of contents from gesetze-im-internet.de
- `has_update()` - Checks if remote files have been updated
- `_parse_last_modified_date_str()` - Parses HTTP Last-Modified headers
- `LocalPathLocation` class methods:
  - `create_or_replace_law()` - Downloads and extracts law archives
  - `list_slugs_with_timestamps()` - Lists local laws with their timestamps
  - `xml_file_for()` - Finds XML file for a law
  - `attachments()` - Extracts and base64-encodes attachments

**Why this is high priority:**
- Handles external HTTP requests (prone to failures)
- File system operations (edge cases with permissions, missing files)
- Critical for data pipeline reliability

**Recommended tests:**
```python
# tests/test_download.py
import pytest
from unittest.mock import Mock, patch, mock_open
from gadi.gesetze_im_internet.download import (
    fetch_toc, has_update, LocalPathLocation, _parse_last_modified_date_str
)

class TestFetchToc:
    def test_fetch_toc_success(self, mock_requests):
        """Test successful TOC fetch and parsing"""

    def test_fetch_toc_handles_network_errors(self, mock_requests):
        """Test graceful handling of network failures"""

    def test_fetch_toc_parses_xml_correctly(self, mock_requests):
        """Test XML parsing extracts correct slug and URL"""

class TestHasUpdate:
    def test_has_update_with_newer_remote_version(self):
        """Test returns True when remote is newer"""

    def test_has_update_with_same_version(self):
        """Test returns False when timestamps match"""

    def test_has_update_without_last_modified_header(self):
        """Test handles missing Last-Modified header gracefully"""

class TestParseLastModifiedDateStr:
    def test_parses_valid_http_date(self):
        """Test parsing of standard HTTP date format"""

    def test_handles_missing_last_modified_header(self):
        """Test defaults to current date when header missing"""

class TestLocalPathLocation:
    def test_create_or_replace_law_downloads_and_extracts(self, tmpdir):
        """Test downloads ZIP and extracts to correct location"""

    def test_create_or_replace_law_overwrites_existing(self, tmpdir):
        """Test replaces existing law directory"""

    def test_list_slugs_with_timestamps(self, tmpdir):
        """Test returns dict of slug -> timestamp"""

    def test_list_slugs_handles_missing_timestamp_file(self, tmpdir):
        """Test uses default timestamp when .timestamp file missing"""

    def test_xml_file_for_returns_single_xml(self, tmpdir):
        """Test finds and returns XML file path"""

    def test_xml_file_for_raises_when_multiple_xmls(self, tmpdir):
        """Test raises error when multiple XML files found"""

    def test_attachments_encodes_files_correctly(self, tmpdir):
        """Test base64 encodes non-XML files with correct MIME types"""

    def test_attachments_skips_xml_files(self, tmpdir):
        """Test does not include XML files in attachments"""
```

**Estimated effort**: Medium (2-3 days)

---

### 2. HIGH PRIORITY: Data Ingestion Module (20% coverage)
**File**: `gadi/gesetze_im_internet/__init__.py`

**Missing coverage:**
- `_calculate_diff()` - Calculates which laws are new/updated/removed
- `_loop_with_progress()` - Progress bar wrapper
- `_check_for_updates()` - Checks each law for updates
- `download_laws()` - Main function for downloading law data
- `ingest_data_from_location()` - Ingests parsed data into database
- `ingest_law()` - Parses and adds single law to database
- `_fixup_slug_duplicates()` - Handles duplicate law slugs
- `write_all_law_json_files()` - Generates JSON files for website
- `write_law_json_file()` - Writes single law JSON file
- `generate_static_assets()` - Creates tarball of all laws

**Why this is high priority:**
- Core business logic for data pipeline
- Complex state management (new/updated/removed laws)
- Safety check for accidental mass deletion (>250 laws)

**Recommended tests:**
```python
# tests/test_ingestion.py
import pytest
from unittest.mock import Mock, MagicMock
from gadi.gesetze_im_internet import (
    _calculate_diff, download_laws, ingest_data_from_location,
    ingest_law, _fixup_slug_duplicates, write_all_law_json_files
)

class TestCalculateDiff:
    def test_identifies_new_laws(self):
        """Test correctly identifies new laws"""
        previous = ["law1", "law2"]
        current = ["law1", "law2", "law3"]
        existing, new, removed = _calculate_diff(previous, current)
        assert new == {"law3"}
        assert existing == {"law1", "law2"}
        assert removed == set()

    def test_identifies_updated_laws(self):
        """Test identifies laws present in both sets"""

    def test_identifies_removed_laws(self):
        """Test correctly identifies removed laws"""

    def test_raises_error_on_suspicious_removals(self):
        """Test raises exception when >250 laws would be removed"""
        previous = [f"law{i}" for i in range(300)]
        current = []
        with pytest.raises(Exception, match="Dubious number"):
            _calculate_diff(previous, current)

class TestFixupSlugDuplicates:
    def test_applies_overrides_correctly(self, db_session):
        """Test applies hardcoded slug overrides"""

    def test_uses_gii_slug_as_default(self, db_session):
        """Test uses gii_slug when no override specified"""

class TestWriteLawJsonFiles:
    def test_write_law_json_file_creates_valid_json(self, tmpdir):
        """Test writes valid JSON file with correct schema"""

    def test_write_all_law_json_files_creates_index(self, tmpdir, db_session):
        """Test creates __index.json with sorted abbreviations"""

    def test_write_all_law_json_files_creates_gzipped_all_laws(self, tmpdir, db_session):
        """Test creates all_laws.json.gz with all laws"""

class TestGenerateStaticAssets:
    def test_creates_tarball(self, tmpdir, db_session):
        """Test creates tarball containing laws directory"""
```

**Estimated effort**: High (3-5 days)

---

### 3. MEDIUM PRIORITY: Database Module (46% coverage)
**File**: `gadi/db.py`

**Missing coverage:**
- `all_laws()` - Query all laws
- `find_law_by_doknr()` - Find law by document number
- `find_law_by_slug()` - Find law by slug
- `laws_with_duplicate_slugs()` - Find duplicate slugs
- `bulk_delete_laws_by_gii_slug()` - Delete multiple laws
- `session_scope()` - Context manager for transactions

**Why this is medium priority:**
- Relatively straightforward database queries
- Lower complexity but still important for data integrity

**Recommended tests:**
```python
# tests/test_db.py
import pytest
from gadi import db, models

class TestFinders:
    def test_find_law_by_doknr_returns_law(self, db_session, sample_law):
        """Test finds law by document number"""
        law = db.find_law_by_doknr(db_session, sample_law.doknr)
        assert law.id == sample_law.id

    def test_find_law_by_doknr_returns_none_when_not_found(self, db_session):
        """Test returns None for non-existent document number"""
        law = db.find_law_by_doknr(db_session, "NONEXISTENT")
        assert law is None

    def test_find_law_by_slug_returns_law(self, db_session, sample_law):
        """Test finds law by slug"""

    def test_laws_with_duplicate_slugs_identifies_duplicates(self, db_session):
        """Test finds laws with duplicate slugs"""

class TestBulkOperations:
    def test_bulk_delete_laws_by_gii_slug(self, db_session):
        """Test deletes multiple laws by gii_slug"""

    def test_all_laws_returns_all(self, db_session):
        """Test returns all laws"""

class TestSessionScope:
    def test_session_scope_commits_on_success(self):
        """Test commits transaction on successful completion"""

    def test_session_scope_rolls_back_on_error(self):
        """Test rolls back transaction on exception"""
```

**Estimated effort**: Low (1-2 days)

---

### 4. MEDIUM PRIORITY: Models (70% coverage)
**File**: `gadi/models.py`

**Missing coverage:**
- `slugify()` - Converts strings to URL-safe slugs
- `Law.from_dict()` - Creates Law instances from dictionaries
- `ContentItem.from_dict()` - Creates ContentItem from dictionaries
- Relationship handling

**Why this is medium priority:**
- Core data models with business logic
- Slug generation is critical for URL generation

**Recommended tests:**
```python
# tests/test_models.py
import pytest
from gadi.models import slugify, Law, ContentItem

class TestSlugify:
    def test_handles_umlauts(self):
        """Test converts German umlauts correctly"""
        assert slugify("Müller") == "mueller"
        assert slugify("Größe") == "groesse"
        assert slugify("Käse") == "kaese"
        assert slugify("Übung") == "uebung"

    def test_handles_special_characters(self):
        """Test replaces special characters with underscores"""
        assert slugify("Test & Co.") == "test___co_"

    def test_collapses_underscores(self):
        """Test collapses consecutive underscores"""
        assert slugify("Test   Co") == "test_co"

    def test_lowercase_conversion(self):
        """Test converts to lowercase"""
        assert slugify("AbCdEf") == "abcdef"

class TestLawFromDict:
    def test_creates_law_with_basic_fields(self):
        """Test creates Law with basic fields from dict"""

    def test_creates_law_with_contents(self):
        """Test creates Law with content items"""

    def test_creates_law_with_attachments(self):
        """Test creates Law with attachments"""

    def test_sets_relationships_correctly(self):
        """Test sets parent-child relationships for content items"""

class TestContentItemFromDict:
    def test_handles_parent_relationships(self):
        """Test correctly links to parent content items"""
```

**Estimated effort**: Low (1-2 days)

---

### 5. MEDIUM PRIORITY: API Schemas (75% coverage)
**File**: `gadi/api_schemas.py`

**Missing coverage:**
- Various `from_orm_model()` class methods
- Pydantic validators
- Model transformations for different content item types

**Why this is medium priority:**
- API contract validation is important
- Pydantic provides some built-in validation
- Missing coverage in edge cases

**Recommended tests:**
```python
# tests/test_api_schemas.py
import pytest
from gadi import api_schemas

class TestContentItemSchemas:
    def test_content_item_basic_fields_from_orm_model(self, sample_content_item):
        """Test converts ORM model to basic fields schema"""

    def test_article_all_fields_includes_body(self, sample_article):
        """Test article schema includes body field"""

    def test_heading_all_fields_excludes_body(self, sample_heading):
        """Test heading schema excludes body field"""

class TestLawSchemas:
    def test_law_basic_fields_from_orm_model(self, sample_law):
        """Test converts ORM law to basic fields"""

    def test_law_all_fields_from_orm_model_with_contents(self, sample_law):
        """Test includes contents when requested"""

    def test_law_all_fields_from_orm_model_without_contents(self, sample_law):
        """Test excludes contents when not requested"""

class TestValidators:
    def test_type_validator_rejects_mismatched_types(self):
        """Test validator rejects incorrect type strings"""

class TestSerialization:
    def test_serialization_to_json(self, sample_law):
        """Test schemas serialize to valid JSON"""
```

**Estimated effort**: Medium (2-3 days)

---

### 6. LOW PRIORITY: Website Tests (0% coverage)
**File**: `website/src/pages/index.tsx`

The Gatsby website currently has no tests. While the component is simple, adding tests would improve confidence.

**Recommended tests:**
```typescript
// website/src/pages/__tests__/index.test.tsx
import React from 'react'
import { render, screen } from '@testing-library/react'
import IndexPage from '../index'

describe('IndexPage', () => {
  it('renders page heading', () => {
    render(<IndexPage />)
    expect(screen.getByRole('heading', { name: /Gesetze aus dem Internet/i }))
      .toBeInTheDocument()
  })

  it('displays last modified date', () => {
    render(<IndexPage />)
    expect(screen.getByText(/Zuletzt aktualisiert:/i)).toBeInTheDocument()
  })

  it('renders download links', () => {
    render(<IndexPage />)
    expect(screen.getByRole('link', { name: /all_laws.json.gz/i }))
      .toBeInTheDocument()
    expect(screen.getByRole('link', { name: /all_laws.tar.gz/i }))
      .toBeInTheDocument()
  })

  it('renders law list from index', () => {
    render(<IndexPage />)
    // Verify at least one law is rendered
    const links = screen.getAllByRole('link')
    expect(links.length).toBeGreaterThan(2) // More than just the 2 download links
  })

  it('law links have correct href', () => {
    render(<IndexPage />)
    const lawLinks = screen.getAllByRole('link')
      .filter(link => link.getAttribute('href')?.startsWith('laws/'))
    expect(lawLinks.length).toBeGreaterThan(0)
  })
})
```

**Required setup:**
- Install testing libraries: `@testing-library/react`, `@testing-library/jest-dom`
- Configure Jest for Gatsby
- Mock GraphQL queries

**Estimated effort**: Medium (2-3 days including setup)

---

## Testing Infrastructure Improvements

### 1. Mock External Dependencies

**Recommendation**: Add fixtures and mocks for:
- HTTP requests to gesetze-im-internet.de (use `responses` or `requests-mock`)
- File system operations (use `tmpdir` fixture or `pyfakefs`)
- Database connections (use test database or SQLite in-memory)

**Example**:
```python
# tests/conftest.py
import pytest
import responses

@pytest.fixture
def mock_gii_toc():
    """Mock the gesetze-im-internet.de TOC endpoint"""
    responses.add(
        responses.GET,
        "http://www.gesetze-im-internet.de/gii-toc.xml",
        body="""<?xml version="1.0"?>
        <items>
            <item><link>http://example.com/alg/</link></item>
        </items>""",
        status=200
    )
```

### 2. Test Database Setup

**Current issue**: Tests require a running PostgreSQL instance, which is not portable.

**Recommendations**:
1. **Option A**: Use SQLite in-memory database for tests
   - Pros: Fast, no setup required
   - Cons: Different SQL dialect might hide PostgreSQL-specific issues

2. **Option B**: Use Docker container with PostgreSQL
   - Pros: Tests against actual PostgreSQL
   - Cons: Requires Docker setup

3. **Option C**: Use pytest-postgresql plugin
   - Pros: Automatic PostgreSQL setup/teardown
   - Cons: Additional dependency

**Preferred**: Option C with fallback to Option A

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from gadi.models import Base

@pytest.fixture(scope="session")
def test_db_engine(postgresql):
    """Create test database engine"""
    engine = create_engine(postgresql.url())
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def db_session(test_db_engine):
    """Create test database session"""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
```

### 3. CI Configuration

**Recommendation**: Add GitHub Actions workflow to run tests automatically.

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_DB: gadi_test
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install pipenv
          pipenv install --dev

      - name: Run tests
        run: pipenv run pytest --cov --cov-report=xml
        env:
          DB_URI: postgresql://postgres:postgres@localhost:5432/gadi_test

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### 4. Coverage Reporting

**Current setup**: Coverage is generated but not enforced.

**Recommendations**:
1. Add `--cov-fail-under=80` to pytest.ini to fail builds below 80% coverage
2. Configure pytest-cov to show missing lines in output
3. Integrate with Codecov or Coveralls for PR comments

```ini
# pytest.ini
[pytest]
addopts = -ra --cov=gadi --cov-report=term-missing --cov-report=html --cov-fail-under=80 --durations=10
testpaths =
    tests
```

---

## Summary Priority Matrix

| Priority | Module | File | Current | Target | Effort | Impact |
|----------|--------|------|---------|--------|--------|--------|
| 🔴 **High** | Download | `download.py` | 30% | 85%+ | Medium | High |
| 🔴 **High** | Ingestion | `__init__.py` | 20% | 80%+ | High | High |
| 🟡 **Medium** | Database | `db.py` | 46% | 90%+ | Low | Medium |
| 🟡 **Medium** | Models | `models.py` | 70% | 90%+ | Low | Medium |
| 🟡 **Medium** | Schemas | `api_schemas.py` | 75% | 90%+ | Medium | Medium |
| 🟢 **Low** | Website | `index.tsx` | 0% | 70%+ | Medium | Low |

---

## Recommended Implementation Order

1. **Week 1-2**: Infrastructure improvements (test database, fixtures, CI)
2. **Week 3**: High priority - Download module tests
3. **Week 4-5**: High priority - Ingestion module tests
4. **Week 6**: Medium priority - Database and Models tests
5. **Week 7**: Medium priority - API Schemas tests
6. **Week 8**: Low priority - Website tests (if time permits)

---

## Expected Outcomes

After implementing these recommendations:
- **Overall coverage**: 57% → 85%+
- **Reduced bugs**: Better test coverage catches edge cases
- **Safer refactoring**: Tests provide safety net for code changes
- **Better documentation**: Tests serve as usage examples
- **CI confidence**: Automated testing prevents regressions

---

## Notes

- The most critical gaps are in the **download and ingestion modules**, which handle external data sources and are prone to edge cases and errors
- Current tests only cover the "happy path" - need more edge case and error handling tests
- Website testing requires setup but is lower priority due to component simplicity
- Consider adding integration tests that test the full pipeline end-to-end
