// SPDX-License-Identifier: Apache-2.0

use mncs_rc_consumer::{default_corpus_from_manifest, run_corpus};
use serde_json::json;
use std::env;
use std::path::PathBuf;
use std::process::ExitCode;

fn main() -> ExitCode {
    let path = env::args_os()
        .nth(1)
        .map_or_else(default_corpus_from_manifest, PathBuf::from);
    match run_corpus(&path) {
        Ok(result) => {
            let failed =
                result.summary.disagreement > 0 || result.summary.implementation_errors > 0;
            println!(
                "{}",
                serde_json::to_string_pretty(&result).expect("serializing a result cannot fail")
            );
            if failed {
                ExitCode::FAILURE
            } else {
                ExitCode::SUCCESS
            }
        }
        Err(error) => {
            println!(
                "{}",
                serde_json::to_string_pretty(&json!({
                    "category": "IMPLEMENTATION_ERROR",
                    "error": error
                }))
                .expect("serializing an error cannot fail")
            );
            ExitCode::from(2)
        }
    }
}
