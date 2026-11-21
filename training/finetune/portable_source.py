"""Exact clean source with Git-normalized blobs, portable across CRLF/LF hosts."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from trainer_config import ROOT,TrainerError


def command(root,args,*,content=None,check=True):
    environment={key:value for key,value in os.environ.items() if not key.upper().startswith('GIT_')}
    result=subprocess.run(['git','-C',str(root),*args],input=content,capture_output=True,timeout=60,env=environment)
    if check and result.returncode:raise TrainerError('handoff_git_inspection_failed')
    return result


def bookkeeping(path):
    return bool(re.fullmatch(r'Tasks/items/ai/FDEC-087-[^/]+/(?:events|evidence)/.+|Tasks/version-requests/FDEC-087.json',path))


def tree(root,revision):
    rows=[]
    for raw in command(root,['ls-tree','-rz',revision]).stdout.split(b'\0'):
        if not raw:continue
        front,name=raw.split(b'\t',1);mode,kind,digest=front.decode().split();name=name.decode('utf-8')
        if bookkeeping(name):continue
        if kind!='blob' or mode not in ('100644','100755') or not re.fullmatch(r'[A-Za-z0-9_./-]+',name):raise TrainerError('handoff_source_path_unsupported')
        rows.append([name,mode,digest])
    return sorted(rows)


def verify(expected=None,*,root=ROOT):
    root=Path(root).resolve()
    head=command(root,['rev-parse','HEAD']).stdout.decode().strip()
    source=head if expected is None else expected['source_sha']
    if not re.fullmatch('[a-f0-9]{40}',source) or command(root,['merge-base','--is-ancestor',source,head],check=False).returncode:raise TrainerError('handoff_source_not_ancestor')
    rows=tree(root,source)
    if tree(root,head)!=rows:raise TrainerError('handoff_source_committed_drift')
    index=[]
    for entry in command(root,['ls-files','--stage','-z']).stdout.split(b'\0'):
        if not entry:continue
        front,name=entry.split(b'\t',1);mode,digest,stage=front.decode().split();name=name.decode('utf-8')
        if stage!='0':raise TrainerError('handoff_unmerged_source')
        if not bookkeeping(name):index.append([name,mode,digest])
    if sorted(index)!=rows:raise TrainerError('handoff_staged_source_drift')
    if any(row and row[:1]!=b'H' for row in command(root,['ls-files','-v','-z']).stdout.split(b'\0')):raise TrainerError('handoff_hidden_index_flag')
    names=[row[0] for row in rows]
    from ingest_dataset import reject_links
    for name in names:reject_links(root/name)
    actual=command(root,['hash-object','--stdin-paths'],content=('\n'.join(names)+'\n').encode()).stdout.decode().splitlines()
    if actual!=[row[2] for row in rows]:raise TrainerError('handoff_working_source_drift')
    extras=command(root,['ls-files','--others','--exclude-standard','-z']).stdout.split(b'\0')
    allowed_ide=r'\.idea/(?:workspace.xml|vcs.xml|modules.xml|misc.xml|\.gitignore|[^/]+\.iml|inspectionProfiles/[^/]+\.xml)'
    if any(raw and not bookkeeping(raw.decode()) and not re.fullmatch(allowed_ide,raw.decode()) for raw in extras):raise TrainerError('handoff_untracked_source')
    digest=hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()
    result=dict(algorithm='fdec-portable-source/v1',source_sha=source,source_tree=command(root,['rev-parse',source+'^{tree}']).stdout.decode().strip(),portable_tree_sha256=digest,source_files=len(rows))
    if expected is not None and result!=expected:raise TrainerError('handoff_source_identity_changed')
    return result
