import pandas as pd
from src.load import clean_runtime, clean_box_office


def test_clean_runtime():
    assert clean_runtime("81 min") == 81


def test_clean_box_office():
    assert clean_box_office("$229,947,062") == 229947062


def test_na_values_become_null():
    assert clean_runtime("N/A") is None or pd.isna(clean_runtime("N/A"))
    assert clean_box_office("N/A") is None or pd.isna(clean_box_office("N/A"))