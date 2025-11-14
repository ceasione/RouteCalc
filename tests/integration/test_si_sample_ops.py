
import pytest
from app.lib.utils.QueryLogger import QueryLogger

TABLE_NAME = 'si_sample'

@pytest.fixture(scope='session')
def db():
    ql = QueryLogger(':memory:')
    with ql:
        yield ql

samples_for_insert = [
    (0, 1, 2, 3.14),
    (1, 2, 3, 3.14),
    (2, 3, 4, 3.14)
]

samples_for_update = [
    (0, 1, 2, 7.68),
    (2, 3, 4, 7.68)
]

samples_to_assert = [
    (0, 1, 2, 7.68),
    (1, 2, 3, 3.14),
    (2, 3, 4, 7.68)
]

@pytest.mark.order(1)
def test_table_creation_successful(db):
    # This will return a list of tables with the name specified; that is,
    # the cursor will have a count of 0 (does not exist) or a count of 1 (does exist)
    db.cursor.execute(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{TABLE_NAME}';"
    )
    assert len(db.cursor.fetchall()) == 1

@pytest.mark.order(2)
@pytest.mark.parametrize('samples', [samples_for_insert, samples_for_update])
def test_upsert(db, samples):
    for smp in samples:
        db.sample_upsert(smp[0], smp[1], smp[2], smp[3])
    db.conn.commit()

@pytest.mark.order(3)
def test_select_samples(db):
    samples_generator = db.select_samples()
    retrieved_samples = [sample for sample in samples_generator]
    assert retrieved_samples == samples_to_assert
