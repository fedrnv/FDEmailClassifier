// Copyright 2026 FDEmailClassifier contributors
// SPDX-License-Identifier: Apache-2.0
use std::process::ExitCode;

fn main() -> ExitCode {
    let mut args = std::env::args_os().skip(1);
    let arg = args.next();
    if args.next().is_some() {
        eprintln!("Invalid arguments. Use --help.");
        return ExitCode::from(2);
    }
    match arg.as_deref().and_then(|value| value.to_str()) {
        Some("--help" | "-h") => {
            println!(
                "FDEmailClassifier server scaffold\nUsage: fdemailclassifier-server --help | --version\nThe service is not implemented yet; no network listener is started."
            );
            ExitCode::SUCCESS
        }
        Some("--version" | "-V") => {
            println!(
                "fdemailclassifier-server {} (development scaffold)",
                env!("CARGO_PKG_VERSION")
            );
            ExitCode::SUCCESS
        }
        _ => {
            eprintln!("The service is not implemented. Use --help.");
            ExitCode::from(2)
        }
    }
}
