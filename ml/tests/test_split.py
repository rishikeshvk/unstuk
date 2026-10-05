from records import make

from unstuk_ml.grid import plan_batches
from unstuk_ml.record import Record
from unstuk_ml.split import split


def pool() -> list[Record]:
    records: list[Record] = []
    for kind, count in (("train", 40), ("oos", 10), ("contrast", 6)):
        for i, cell in enumerate(plan_batches(count, seed=1), 1):
            batch = f"{kind}-{i:02d}"
            records += [
                make(f"{batch}-{n}", f"line {n}", batch=batch, persona=cell) for n in range(3)
            ]
    records.append(make("seed-1", "seed line", batch="seed-01", source="seed"))
    return records


def test_a_batch_is_never_on_both_sides() -> None:
    train, dev = split(pool(), seed=3)

    assert {r.batch for r in train}.isdisjoint({r.batch for r in dev})


def test_dev_covers_every_grid_value_and_seeds_stay_in_train() -> None:
    train, dev = split(pool(), seed=3)

    assert {r.persona["style"] for r in dev if r.persona} == {
        "plain",
        "question",
        "story",
        "frustrated",
        "dictated",
        "terse",
    }
    assert any(r.source == "seed" for r in train)
    assert not any(r.source == "seed" for r in dev)


def test_the_split_is_the_same_every_run() -> None:
    assert split(pool(), seed=3) == split(pool(), seed=3)
