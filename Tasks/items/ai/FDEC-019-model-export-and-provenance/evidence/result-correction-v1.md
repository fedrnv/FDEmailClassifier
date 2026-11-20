# Export result identity correction

The first result authoring command passed an unquoted `HEAD^{tree}` through
PowerShell, which parsed the braces as script syntax. Git rejected the resulting
argument, but the outer script continued and wrote result-v1.json with an invalid
source-tree value. No acceptance test or source changed, no closure was recorded,
and no version request was submitted from that result.

The original file is retained unchanged. result-v2.json is the successor with the
source tree obtained using quoted `git rev-parse 'HEAD^{tree}'`, checked for exit
zero and a 40-character Git identity before writing. All other result fields are
unchanged. Closing readiness and the first version request must bind result-v2,
not the rejected result-v1. No test rerun is warranted for this metadata-only
correction; both final tests ran at the unchanged verified source state.
