# SPDX-License-Identifier: Apache-2.0

from importlib.resources import files

from mncs_validator.schemas import SCHEMA_NAMES, load_schema


def test_runtime_schemas_are_package_resources() -> None:
    resources = files("mncs_validator.resources.schemas")
    for filename in SCHEMA_NAMES.values():
        assert resources.joinpath(filename).is_file()
    assert load_schema("manifest")["$id"].endswith("/0.1.1/mncs-manifest.schema.json")
