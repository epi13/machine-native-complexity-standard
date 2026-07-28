from mncs_validator.composition import aggregate


def result(status: str, required: bool = True, evidence_ref: str = "evidence") -> dict[str, object]:
    return {"status": status, "required": required, "evidence_ref": evidence_ref}


def test_precedence() -> None:
    assert aggregate([result("PASS"), result("UNKNOWN")]) == "UNKNOWN"
    assert aggregate([result("UNKNOWN"), result("FAIL")]) == "FAIL"
    assert aggregate([result("PASS"), result("PASS")]) == "PASS"


def test_review_and_missing() -> None:
    assert aggregate([result("UNKNOWN")], allow_review=True) == "REVIEW_REQUIRED"
    assert aggregate([result("PASS", evidence_ref="")]) == "UNKNOWN"
