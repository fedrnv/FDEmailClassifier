# FDEC-087 Mac staging for the original workstation

This report records the Mac preparation for the actual training return.
The exact producer source is `fd4d8fbf539862da2172ccf46509d3e9e19837c5`.
The public recording baseline is
`5609c692a75530c5633d19ce3beb19cdc12bdb6e`.

The authenticated local readback verified the actual training kit and
return receipt, all nine return-manifest members, the step-100 native
optimizer cursor and all 392 PEFT tensors. It also verified all 19
signed files of the existing local export candidate. This is the
actual Stage C handoff lineage. The later two-provider evaluated model
package remains a separate protected artifact.

| Prepared item | Observation |
| --- | --- |
| Owner-only staging archive | 33 payload files and an internal file manifest, 170,560,866 bytes |
| Archive readback | Exact file inventory, complete byte hashes and ZIP integrity passed |
| Contents | Exact source bundle, trained checkpoint and adapter, evaluation artifacts, signed compact input metadata and review bindings, and source receipt references |
| Excluded material | Handoff and consent authority keys, raw source runs, stock model and local GGUF binaries |
| External transfer and receiver verification | Pending |

| Identity | SHA-256 |
| --- | --- |
| Archive | `35a7f636c1ddc9a139c93a9c5bd29faffbafaff6ff9220b20edc3d5a1b4a5330` |
| Actual return manifest | `18d228b1b5c1e3ad42c310b85f3b20af808faf6752c1e55a329fba66f24a0bcb` |
| Verified local export manifest | `225918865d00ce06e3705f7bd87e7aee7d13208b0e70f0ca2faf102a2464b639` |

The archived producer's compact inventory reader requires POSIX private
storage. It rejects native Windows before reading the inventory. A local
negative fixture modeled that operating-system condition and confirmed
the rejection. The prior original Windows numerical fixture does not
exercise this actual compact corpus. Do not rewrite the signed inventory
or substitute a different source to make the receiver pass.

The original workstation still needs an approved private receiver
environment, secure artifact delivery, separately provisioned authority,
the exact approved source runs and stock snapshot, and a successful
actual-training verification receipt. The archive remains on the
FileVault-protected Mac in owner-only storage. No dataset or model
release has been approved by this preparation.
