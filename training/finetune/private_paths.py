"""Check/private-lock only newly owned handoff directories, never source trees."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
from trainer_config import ROOT,TrainerError
from ingest_dataset import reject_links


def verify(directory,*,owner_token=None):
    directory=reject_links(directory)
    if not directory.is_dir():raise TrainerError('private_handoff_directory_required')
    if os.name=='nt':
        shell=shutil.which('powershell.exe') or shutil.which('pwsh')
        if not shell:raise TrainerError('private_acl_verifier_missing')
        command=[shell,'-NoProfile','-NonInteractive','-File',str(ROOT/'training/scripts/private-handoff-path.ps1'),'-Path',str(directory),'-Action','Protect' if owner_token else 'Assert']
        if owner_token:command+=['-OwnerToken',owner_token]
        result=subprocess.run(command,capture_output=True,timeout=30)
        if result.returncode:raise TrainerError('private_handoff_acl_rejected')
    else:
        if owner_token:
            if (reject_links(directory/'.owner')).read_text()!=owner_token or {p.name for p in directory.iterdir()}!={'.owner'}:raise TrainerError('private_handoff_owner_mismatch')
            if sys.platform=='darwin':
                result=subprocess.run(['chmod','-N',str(directory)],capture_output=True,timeout=10)
                if result.returncode:raise TrainerError('private_handoff_acl_clear_failed')
            os.chmod(directory,0o700)
        if directory.stat().st_mode&0o077:raise TrainerError('private_handoff_permissions_rejected')
        for path in [directory,*directory.rglob('*')]:
            reject_links(path)
            if path.stat().st_uid!=os.geteuid():raise TrainerError('private_handoff_foreign_owner')
            if sys.platform=='darwin':
                # POSIX mode alone does not exclude an inherited macOS ACL.
                # Capture metadata privately; never emit user or machine names.
                result=subprocess.run(['ls','-lde',str(path)],capture_output=True,text=True,timeout=10)
                if result.returncode or not result.stdout.split() or '+' in result.stdout.split()[0]:raise TrainerError('private_handoff_acl_rejected')
    return True
