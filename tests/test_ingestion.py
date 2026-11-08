
import pandas as pd

from src.etl.ingestion import ingest_csv


def test_ingestion_with_valid_data():

    df = pd.DataFrame({
        "encounter_id": ["1001", "1002"],
        "patient_nbr": ["2001", "2002"],
        "gender": ["Female", "Male"]
    })

    result = ingest_csv(
        __import__("io").StringIO(df.to_csv(index=False))
    )

    assert result.status == "PARTIAL"
    assert result.total_records == 2
    assert result.valid_records == 2
    assert result.rejected_records == 0


def test_ingestion_rejects_missing_identifiers():

    df = pd.DataFrame({
        "encounter_id": ["1001", None],
        "patient_nbr": ["2001", "2002"]
    })

    result = ingest_csv(
        __import__("io").StringIO(df.to_csv(index=False))
    )

    assert result.rejected_records == 1
    assert result.valid_records == 1


def test_ingestion_fails_without_identifiers():

    df = pd.DataFrame({
        "gender": ["Female", "Male"]
    })

    result = ingest_csv(
        __import__("io").StringIO(df.to_csv(index=False))
    )

    assert result.status == "FAILED"
