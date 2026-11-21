"""Prepare/inspect private transfer; never approve owners, transfer or publish."""
import argparse
import json
from pathlib import Path
import secrets
import sys
from trainer_config import ROOT,TrainerError
from ingest_dataset import private_output,remove_owned
import mlx_handoff as handoff
import private_paths


def main(argv=None):
    from train import Parser
    parser=Parser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True,parser_class=Parser)
    store=commands.add_parser('private-store');store.add_argument('--opt-in',action='store_true');store.add_argument('--output-dir',required=True)
    prepare=commands.add_parser('prepare');prepare.add_argument('--opt-in',action='store_true');prepare.add_argument('--purpose',choices=('numeric-smoke','actual-training'),required=True);prepare.add_argument('--config',required=True);prepare.add_argument('--output-dir',required=True)
    for name in ('inventory','consent','split-dir','annotations','prompt'):prepare.add_argument('--'+name)
    prepare.add_argument('--source-run',action='append')
    inspect=commands.add_parser('inspect');inspect.add_argument('--handoff-dir',required=True)
    receive=commands.add_parser('verify-return');receive.add_argument('--handoff-dir',required=True);receive.add_argument('--received-dir',required=True)
    for name in ('export-dir','llama-cpp-dir','config','inventory','consent','split-dir','training-annotations','training-prompt','annotations','model-dir'):receive.add_argument('--'+name)
    receive.add_argument('--source-run',action='append')
    args=parser.parse_args(argv)
    try:
        if args.command=='private-store':
            if not args.opt_in:raise TrainerError('explicit_opt_in_required')
            path=private_output(args.output_dir,ROOT);token=secrets.token_hex(32);owned=False
            try:
                path.parent.mkdir(parents=True,exist_ok=True);path.mkdir(mode=0o700);owned=True;(path/'.owner').write_text(token,encoding='ascii');private_paths.verify(path,owner_token=token)
            except Exception:
                if owned:remove_owned(path,token)
                raise
            result=dict(private_store_created=True,owner_confirmation_created=False,actual_apple_execution=False)
        elif args.command=='prepare':
            if not args.opt_in:raise TrainerError('explicit_opt_in_required')
            inputs=None
            if args.purpose=='actual-training':
                required=(args.inventory,args.consent,args.split_dir,args.annotations,args.prompt,args.source_run)
                if not all(required):raise TrainerError('insufficient_approved_data')
                inputs=dict(inventory_path=args.inventory,consent_path=args.consent,split_dir=args.split_dir,annotations_path=args.annotations,prompt_path=args.prompt,source_runs=args.source_run)
            result=handoff.prepare(args.output_dir,purpose=args.purpose,config_path=args.config,inputs=inputs)
        elif args.command=='inspect':
            state=handoff.Handoff(args.handoff_dir)
            import portable_source
            portable_source.verify(state.manifest['source'])
            result=dict(handoff_sha256=state.sha256,source=state.manifest['source'],purpose=state.manifest['purpose'],source_license_state=state.manifest['source_license_state'],owner_confirmation_required=True,actual_apple_execution=False,resources=state.manifest['resources'])
        else:result=handoff.verify_return(args.received_dir,handoff=handoff.Handoff(args.handoff_dir),actual_arguments=args)
        print(json.dumps(result,sort_keys=True));return 0
    except Exception as error:
        print(handoff.diagnostic(error),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
