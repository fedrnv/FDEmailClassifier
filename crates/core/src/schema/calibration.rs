// Copyright 2026 FDEmailClassifier contributors
// SPDX-License-Identifier: Apache-2.0
//! Arithmetic for externally verified margin policies. No probability is inferred.
//! Callers must authenticate policy/model/language/score-kind and current authority.
use super::{
    Assessment, Classification, Priority, SchemaVersion, Security, Status, SuggestedAction,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Abstention {
    Unsupported,
    Unmeasured,
    OutsideValidationRange,
    UncertainBand,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Decision {
    Clear,
    Flagged,
    Abstained(Abstention),
}

pub fn decide(band: Option<&MarginBand>, score: Option<f64>) -> Decision {
    band.map_or(Decision::Abstained(Abstention::Unsupported), |band| {
        band.decide(score)
    })
}

/// An empirical, validation-only interval. Private fields prevent unchecked construction.
#[derive(Debug, Clone, Copy)]
pub struct MarginBand {
    minimum: f64,
    maximum: f64,
    negative_cut: Option<f64>,
    positive_cut: Option<f64>,
}

impl MarginBand {
    pub fn new(
        minimum: f64,
        maximum: f64,
        negative_cut: Option<f64>,
        positive_cut: Option<f64>,
    ) -> Result<Self, &'static str> {
        let finite = |value: f64| value.is_finite() && value.abs() <= 1_000_000.0;
        if !finite(minimum)
            || !finite(maximum)
            || minimum > maximum
            || (negative_cut.is_none() && positive_cut.is_none())
            || negative_cut
                .into_iter()
                .chain(positive_cut)
                .any(|value| !finite(value) || value < minimum || value > maximum)
            || matches!((negative_cut, positive_cut), (Some(low), Some(high)) if low >= high)
        {
            return Err("invalid calibration band");
        }
        Ok(Self {
            minimum,
            maximum,
            negative_cut,
            positive_cut,
        })
    }

    pub fn decide(&self, score: Option<f64>) -> Decision {
        let Some(score) = score.filter(|value| value.is_finite() && value.abs() <= 1_000_000.0)
        else {
            return Decision::Abstained(Abstention::Unmeasured);
        };
        if score < self.minimum || score > self.maximum {
            return Decision::Abstained(Abstention::OutsideValidationRange);
        }
        if self.negative_cut.is_some_and(|low| score <= low) {
            return Decision::Clear;
        }
        if self.positive_cut.is_some_and(|high| score >= high) {
            return Decision::Flagged;
        }
        Decision::Abstained(Abstention::UncertainBand)
    }
}

/// A hard-label JSON answer has no measured margin or calibrated probability.
pub fn unassessed_result() -> Classification {
    Classification {
        schema_version: SchemaVersion::V1,
        status: Status::Abstained,
        topics: vec![],
        priority: Priority::Unknown,
        security: Security {
            spam: Assessment::Unknown,
            phishing: Assessment::Unknown,
            malware: Assessment::Unknown,
        },
        suggested_action: SuggestedAction::Review,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn calibration_boundaries_and_missing_measurements_abstain() {
        assert_eq!(
            decide(None, Some(1.0)),
            Decision::Abstained(Abstention::Unsupported)
        );
        let band = MarginBand::new(-2.0, 3.0, Some(-1.0), Some(2.0)).unwrap();
        for (score, expected) in [
            (Some(-2.0), Decision::Clear),
            (Some(-1.0), Decision::Clear),
            (Some(-0.999), Decision::Abstained(Abstention::UncertainBand)),
            (Some(1.999), Decision::Abstained(Abstention::UncertainBand)),
            (Some(2.0), Decision::Flagged),
            (Some(3.0), Decision::Flagged),
            (
                Some(3.001),
                Decision::Abstained(Abstention::OutsideValidationRange),
            ),
            (None, Decision::Abstained(Abstention::Unmeasured)),
            (Some(f64::NAN), Decision::Abstained(Abstention::Unmeasured)),
        ] {
            assert_eq!(band.decide(score), expected);
        }
    }

    #[test]
    fn calibration_invalid_bands_and_wire_probability_are_rejected() {
        for (min, max, low, high) in [
            (3.0, -2.0, Some(-1.0), Some(2.0)),
            (-2.0, 3.0, Some(2.0), Some(2.0)),
            (-2.0, 3.0, None, None),
            (-2.0, 3.0, Some(f64::INFINITY), None),
            (-2.0, 3.0, None, Some(4.0)),
        ] {
            assert!(MarginBand::new(min, max, low, high).is_err());
        }
        let result = unassessed_result();
        assert!(result.validate().is_ok());
        assert_eq!(result.status, Status::Abstained);
        let mut wire = serde_json::to_value(&result).unwrap();
        wire["probability"] = serde_json::json!(0.99);
        assert!(serde_json::from_value::<Classification>(wire).is_err());
    }

    #[test]
    fn calibration_shared_python_fixture_vectors_match() {
        let vectors: serde_json::Value = serde_json::from_str(include_str!(
            "../../../../training/calibration/fixtures/boundaries-v1.json"
        ))
        .unwrap();
        let band = MarginBand::new(
            vectors["minimum"].as_f64().unwrap(),
            vectors["maximum"].as_f64().unwrap(),
            vectors["negative_cut"].as_f64(),
            vectors["positive_cut"].as_f64(),
        )
        .unwrap();
        for case in vectors["cases"].as_array().unwrap() {
            let actual = match band.decide(case["score"].as_f64()) {
                Decision::Clear => "clear",
                Decision::Flagged => "flagged",
                Decision::Abstained(Abstention::Unmeasured) => "abstained:unmeasured",
                Decision::Abstained(Abstention::OutsideValidationRange) => {
                    "abstained:outside_validation_range"
                }
                Decision::Abstained(Abstention::UncertainBand) => "abstained:uncertain_band",
                Decision::Abstained(Abstention::Unsupported) => "abstained:unsupported",
            };
            assert_eq!(actual, case["decision"].as_str().unwrap());
        }
    }
}
