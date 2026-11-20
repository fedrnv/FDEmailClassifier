"""Actual MSVC build after the older MinGW SDK lacked thread-power types."""
import json
from pathlib import Path
import secrets
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/"training/export"))
import exporter
import runtime_load
from common import private_output,write_json
checkout,profile=exporter.converter_checkout(ROOT/"training/data/export-llama-cpp-29b52d3")
output=private_output(ROOT/"training/outputs/fdec019-build-probe-v3",ROOT)
output.mkdir(parents=True)
(output/".owner").write_text(secrets.token_hex(32),encoding="ascii")
original=runtime_load.subprocess.run
counter=0
def captured(command,**kwargs):
    global counter
    counter+=1
    print(json.dumps(dict(stage="configure" if counter==1 else "compile",state="running")),flush=True)
    result=original(command,**kwargs)
    (output/f"stage-{counter}.log").write_bytes(result.stdout+b"\n"+result.stderr)
    print(json.dumps(dict(stage=counter,exit_code=result.returncode)),flush=True)
    return result
runtime_load.subprocess.run=captured
try:executable,record=runtime_load.build(checkout,output/"build",profile["llama_cpp_revision"])
finally:runtime_load.subprocess.run=original
exporter.converter_checkout(checkout)
write_json(output/"build-record.json",dict(**record,executable_relative=executable.relative_to(output).as_posix()))
print(json.dumps(dict(build_completed=True,**record)),flush=True)
