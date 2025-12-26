from src.main import main


def test_main_example() -> None:
    assert main(example=True) == 0
