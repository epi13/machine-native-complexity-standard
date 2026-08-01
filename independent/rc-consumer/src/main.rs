// SPDX-License-Identifier: Apache-2.0

use mncs_rc_consumer::{
    default_corpus_from_manifest, run_corpus, validate_mncds_value, validate_record_value,
};
use serde_json::{Value, json};
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::ExitCode;

const MAX_INPUT_BYTES: u64 = 4 * 1024 * 1024;

fn bounded_json(path: &Path) -> Result<Value, String> {
    let metadata = fs::symlink_metadata(path).map_err(|error| error.to_string())?;
    if metadata.file_type().is_symlink() || !metadata.is_file() {
        return Err("input must be a regular non-symlink file".to_owned());
    }
    if metadata.len() > MAX_INPUT_BYTES {
        return Err(format!("input exceeds {MAX_INPUT_BYTES} bytes"));
    }
    let bytes = fs::read(path).map_err(|error| error.to_string())?;
    if u64::try_from(bytes.len()).unwrap_or(u64::MAX) > MAX_INPUT_BYTES {
        return Err(format!("input exceeds {MAX_INPUT_BYTES} bytes"));
    }
    serde_json::from_slice(&bytes).map_err(|error| error.to_string())
}

fn flag(args: &[String], name: &str) -> Option<String> {
    args.windows(2)
        .find(|pair| pair[0] == name)
        .map(|pair| pair[1].clone())
}

fn emit(value: &Value, status: u8) -> ExitCode {
    println!(
        "{}",
        serde_json::to_string_pretty(value).expect("serializing a result cannot fail")
    );
    ExitCode::from(status)
}

fn conformance(path: &Path) -> ExitCode {
    match run_corpus(path) {
        Ok(result) => {
            let failed =
                result.summary.disagreement > 0 || result.summary.implementation_errors > 0;
            let payload = json!({
                "command": "conformance",
                "category": if failed { "FAIL" } else { "PASS" },
                "implementation": {
                    "name": "mncs-rc-consumer",
                    "language": "Rust",
                    "package_identity": format!("mncs-rc-consumer@{}", env!("CARGO_PKG_VERSION")),
                    "implementation_independence": "separate source and executable",
                    "independent_operation": "UNKNOWN",
                    "organizational_independence": "UNKNOWN"
                },
                "supported_schemas": [
                    "mncs-contract-profile-0.3 / 0.3-rc.1",
                    "mncs-assurance-case-0.3 / 0.3-rc.1",
                    "mncs-threat-record-0.3 / 0.3-rc.1",
                    "mncs-measurement-profile-0.3 / 0.3-rc.1",
                    "mncds-development-record-0.1 / 0.1-rc.1"
                ],
                "supported_rules": [
                    "exact schema/version dispatch",
                    "contract adequacy subset",
                    "FAIL > UNKNOWN > PASS",
                    "claim identity and reference integrity",
                    "cycle rejection",
                    "required and optional dependency handling",
                    "correlated-group propagation",
                    "RFC 3339 timestamps with UTC or numeric offsets",
                    "freshness",
                    "required transitive material-change graph impact",
                    "partial and full revalidation coverage",
                    "release-candidate lifecycle subset",
                    "MNCDS authority, protected-evidence, lineage, selection, and result rules"
                ],
                "unsupported_rules": [
                    "general MNCS 0.2 package archive validation",
                    "general DSSE/Ed25519 trust-policy validation",
                    "network-fetched or executable evidence",
                    "schemas or record families not listed above"
                ],
                "corpus": result.summary,
                "disagreements": result.results.iter()
                    .filter(|item| item.classification == "DISAGREEMENT")
                    .collect::<Vec<_>>(),
                "limitations": [
                    "bounded implementation-conformance subset, not a normative implementation",
                    "unsupported behavior is never silently accepted",
                    "separate implementation code does not establish independent operation or organizational independence",
                    "no result establishes protected custody, governance approval, certification, or promotion"
                ]
            });
            emit(&payload, u8::from(failed))
        }
        Err(error) => emit(
            &json!({"category": "IMPLEMENTATION_ERROR", "error": error}),
            2,
        ),
    }
}

fn validate_record(args: &[String]) -> ExitCode {
    let Some(kind) = flag(args, "--kind") else {
        return emit(
            &json!({"category": "IMPLEMENTATION_ERROR", "error": "--kind is required"}),
            2,
        );
    };
    let Some(input) = flag(args, "--input") else {
        return emit(
            &json!({"category": "IMPLEMENTATION_ERROR", "error": "--input is required"}),
            2,
        );
    };
    let at = flag(args, "--at").unwrap_or_default();
    match bounded_json(Path::new(&input)) {
        Ok(value) => {
            let outcome = validate_record_value(&kind, &value, &at);
            let category = outcome.category.clone();
            emit(
                &json!({
                    "command": "validate-record",
                    "kind": kind,
                    "input": input,
                    "category": category,
                    "issue_codes": outcome.issue_codes,
                    "evaluation_time": if at.is_empty() { Value::Null } else { Value::String(at) },
                    "limitations": [
                        "validation is limited to the declared Rust subset",
                        "assurance and measurement freshness without --at remains UNKNOWN",
                        "the input is inspected offline and no evidence is executed"
                    ]
                }),
                u8::from(matches!(category.as_str(), "INVALID" | "UNSUPPORTED")),
            )
        }
        Err(error) => emit(
            &json!({
                "command": "validate-record",
                "category": "INVALID",
                "issue_codes": ["INPUT-INVALID"],
                "error": error
            }),
            1,
        ),
    }
}

fn validate_mncds(args: &[String]) -> ExitCode {
    let Some(input) = flag(args, "--input") else {
        return emit(
            &json!({"category": "IMPLEMENTATION_ERROR", "error": "--input is required"}),
            2,
        );
    };
    match bounded_json(Path::new(&input)) {
        Ok(value) => {
            let outcome = validate_mncds_value(&value);
            let category = outcome.category.clone();
            emit(
                &json!({
                    "command": "validate-mncds",
                    "input": input,
                    "category": category,
                    "issue_codes": outcome.issue_codes,
                    "limitations": [
                        "MNCDS and MNCS results remain separate",
                        "local validation cannot create protected custody or independent operation"
                    ]
                }),
                u8::from(matches!(category.as_str(), "INVALID" | "UNSUPPORTED")),
            )
        }
        Err(error) => emit(
            &json!({
                "command": "validate-mncds",
                "category": "INVALID",
                "issue_codes": ["INPUT-INVALID"],
                "error": error
            }),
            1,
        ),
    }
}

fn legacy_corpus(path: &Path) -> ExitCode {
    match run_corpus(path) {
        Ok(result) => {
            let failed =
                result.summary.disagreement > 0 || result.summary.implementation_errors > 0;
            emit(
                &serde_json::to_value(result).expect("serializing a result cannot fail"),
                u8::from(failed),
            )
        }
        Err(error) => emit(
            &json!({"category": "IMPLEMENTATION_ERROR", "error": error}),
            2,
        ),
    }
}

fn main() -> ExitCode {
    let args: Vec<String> = env::args().skip(1).collect();
    match args.first().map(String::as_str) {
        Some("validate-record") => validate_record(&args[1..]),
        Some("validate-mncds") => validate_mncds(&args[1..]),
        Some("conformance") => {
            let path = flag(&args[1..], "--corpus")
                .map_or_else(default_corpus_from_manifest, PathBuf::from);
            conformance(&path)
        }
        Some(path) => legacy_corpus(Path::new(path)),
        None => conformance(&default_corpus_from_manifest()),
    }
}
