# Raw evidence storage

The epoch-1 mixed-record CSV is stored as the deterministic text artifact
the ordered `../../artifacts/epoch-1-reactivity.csv.zlib.b85.part*` files.

Run `python3 tools/materialize.py` to restore the byte-identical CSV into `.materialized/`, or
run `make check` to analyze the compressed artifact directly without creating working files.
