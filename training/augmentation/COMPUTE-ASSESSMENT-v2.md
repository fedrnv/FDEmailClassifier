# Compute planning update: owner Mac M4 workflow

The owner's upstream plan at `0ea1e407e32eb2671226ab9f8430e54e4207d6b7` specifies a MacBook Air M4 with 32 GB unified memory as the preferred temporary Qwen3-0.6B MLX training host. This supersedes the earlier provisional recommendation to seek a Linux GPU machine. No GPU VPS is currently necessary or purchased.

Continue development and software-fixture tests on the current workstation. FDEC-087 and the upstream `docs/training/MACBOOK_M4_HANDOFF.md` define the device-dependent workflow. At the dependency-ready training step, prepare a clean pinned source checkpoint, admitted data/model/config manifests, runtime prerequisites and exact resume commands; notify the owner and obtain explicit confirmation before switching machines. Do not request that switch while independent workstation work is still ready.

After actual authorized training, verify private artifacts and their transfer, record a durable return checkpoint and only then tell the owner to return to the original development workstation. No Mac access, installed MLX stack, training performance or completed run has been verified. Linux/PyTorch remains an optional supported alternative when justified and authorized; the EUR 50 dataset-license allowance is not compute-rental authorization.

The earlier `COMPUTE-ASSESSMENT-v1.md` remains historical evidence of local hardware inspection, not the current host preference. Source and redistribution checks apply on every host. No weights, raw training data, credentials or private artifacts belong in Git.
