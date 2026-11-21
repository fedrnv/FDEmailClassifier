"""Numerical/protocol fixtures only; no actual MLX execution or owner approval."""
from copy import deepcopy
from datetime import datetime,timezone
import json
from pathlib import Path
import os
import secrets
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'training/finetune'))
from trainer_config import TrainerError,TARGET_MODULES
import checkpoints,mlx_codec,mlx_handoff as handoff,mlx_export_adapter,portable_source,private_paths
import mlx_engine
import numpy as np


def adapter():
    result={}
    for name in TARGET_MODULES:
        prefix='model.layers.0.'+('self_attn' if name in TARGET_MODULES[:4] else 'mlp')+'.'+name+'.lora_'
        result[prefix+'a']=np.arange(8,dtype=np.float32).reshape(4,2)/16
        result[prefix+'b']=np.arange(8,dtype=np.float32).reshape(2,4)/32
    return result


class Fixtures(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='fdec-mlx-protocol-')
        self.base=Path(self.temporary.name).resolve();self.repo=self.base/'repo';self.repo.mkdir()
        self.store=self.base/'private';self.store.mkdir();token=secrets.token_hex(32);(self.store/'.owner').write_text(token);private_paths.verify(self.store,owner_token=token)
        self.git('init','--quiet');self.git('config','core.autocrlf','true');self.git('config','user.name','Fixture');self.git('config','user.email','fixture@example.invalid')
        for name in ('mlx-runtime-v1.json','mlx-trainer-v1.json'):
            path=self.repo/'training/config'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/'training/config'/name).read_bytes())
        (self.repo/'.gitignore').write_text('ignored/\n')
        (self.repo/'source.py').write_text('value = 1\n')
        self.git('add','.');self.git('commit','--quiet','-m','technical fixture')
        self.config=self.repo/'training/config/mlx-trainer-v1.json'
        self.owner=self.store/'counterfactual-owner.json'
        self.environment=patch.dict(os.environ,{'FDEC_OWNER_CONFIRMATION_FILE':str(self.owner)})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        absolute=self.base.resolve()
        if not absolute.is_relative_to(Path(tempfile.gettempdir()).resolve()) or not absolute.name.startswith('fdec-mlx-protocol-'):raise AssertionError('Unsafe fixture cleanup')
        self.temporary.cleanup()

    def git(self,*args):return subprocess.run(['git','-C',str(self.repo),*args],capture_output=True,text=True,check=True).stdout.strip()
    def prepare(self):
        handoff.prepare(self.store/'handoff',purpose='numeric-smoke',config_path=self.config,root=self.repo)
        return handoff.Handoff(self.store/'handoff',root=self.repo)
    def approve_fixture(self,state):
        # Counterfactual isolated authority; not an actual owner conversation.
        value=dict(schema='fdec-owner-transition/v1',source_sha=state.manifest['source']['source_sha'],handoff_sha256=state.sha256,scope='numeric-smoke',confirmation='explicit-project-owner-device-transition',confirmed_at=datetime.now(timezone.utc).isoformat())
        self.owner.write_text(handoff.canonical(value));return value
    def state(self):return dict(schema='fdec-mlx-state/v1',parameter_order=sorted(adapter()),adapter=adapter(),optimizer={'step':np.array(4,dtype=np.uint64),'momentum':np.arange(4,dtype=np.float32)},rng=np.array([17,29],dtype=np.uint32))
    def bundle(self,state):
        self.approve_fixture(state)
        config=dict(state.manifest['config'],max_steps=4,rank=2,alpha=4)
        context=dict(schema='fdec-mlx-smoke-context/v1',config=config,handoff_sha256=state.sha256)
        checkpoint=self.store/'checkpoint'
        checkpoints.save(checkpoint,state=self.state(),context=context,step=4,key=state.key,writer=lambda value,path:mlx_codec.encode(value,path,to_numpy=np.array),current_check=lambda:None)
        export=self.store/'adapter'
        mlx_export_adapter.write(export,adapter=adapter(),config=config,model_id='fdec-technical-random-qwen3',revision='numeric-only-no-publisher-tensors')
        artifacts={name:checkpoint/name.split('/')[-1] for name in ('checkpoint/.owner','checkpoint/state.safetensors','checkpoint/metadata.json','checkpoint/receipt.json')}
        artifacts.update({name:export/name.split('/')[-1] for name in ('adapter/adapter_model.safetensors','adapter/adapter_config.json')})
        report=dict(schema='fdec-mlx-numeric-smoke/v1',result='PASS',checkpoint_resume_exact=True,actual_apple_execution=False,simulation=True)
        handoff.create_return(self.store/'return',handoff=state,report=report,artifacts=artifacts)
        return self.store/'return'

    def test_portable_source_reads_actual_worktree_index_and_ignores_git_env(self):
        expected=portable_source.verify(root=self.repo)
        with patch.dict(os.environ,{'GIT_DIR':str(self.base/'missing'),'GIT_INDEX_FILE':str(self.base/'missing-index')}):self.assertEqual(portable_source.verify(expected,root=self.repo),expected)
        (self.repo/'source.py').write_bytes(b'value = 1\r\n')
        self.assertEqual(portable_source.verify(expected,root=self.repo),expected)
        (self.repo/'source.py').write_text('value = 2\n')
        with self.assertRaisesRegex(TrainerError,'working_source_drift'):portable_source.verify(expected,root=self.repo)
        self.git('add','source.py')
        with self.assertRaisesRegex(TrainerError,'staged_source_drift'):portable_source.verify(expected,root=self.repo)

    def test_portable_source_hidden_flags_new_source_and_committed_drift_reject(self):
        expected=portable_source.verify(root=self.repo)
        self.git('update-index','--assume-unchanged','source.py')
        with self.assertRaisesRegex(TrainerError,'hidden_index_flag'):portable_source.verify(expected,root=self.repo)
        self.git('update-index','--no-assume-unchanged','source.py')
        (self.repo/'other.py').write_text('untrusted = 1\n')
        with self.assertRaisesRegex(TrainerError,'untracked_source'):portable_source.verify(expected,root=self.repo)
        self.git('add','.');self.git('commit','--quiet','-m','source drift')
        with self.assertRaisesRegex(TrainerError,'committed_drift'):portable_source.verify(expected,root=self.repo)

    def test_prepare_retains_exact_git_bundle_and_requires_external_owner(self):
        state=self.prepare()
        refs=subprocess.run(['git','bundle','list-heads',str(state.directory/'source.bundle')],capture_output=True,text=True,check=True).stdout
        self.assertIn(state.manifest['source']['source_sha'],refs)
        with patch.object(mlx_engine,'hardware') as hardware:
            with self.assertRaisesRegex(TrainerError,'explicit_owner_transition_missing'):mlx_engine.runtime(state,'numeric-smoke')
            hardware.assert_not_called()
        self.approve_fixture(state);state.authorize('numeric-smoke')
        with self.assertRaisesRegex(TrainerError,'apple_silicon_host_required'):mlx_engine.runtime(state,'numeric-smoke')
        self.assertFalse(any(name=='mlx.core' for name in sys.modules))

    def test_scope_change_owner_revocation_and_source_bundle_mutation_reject(self):
        state=self.prepare();value=self.approve_fixture(state);state.authorize('numeric-smoke')
        with self.assertRaisesRegex(TrainerError,'scope_mismatch'):state.authorize('actual-training')
        value['confirmed_at']='2020-01-01T00:00:00+00:00';self.owner.write_text(handoff.canonical(value))
        with self.assertRaisesRegex(TrainerError,'transition_changed'):state.authorize('numeric-smoke')
        (state.directory/'source.bundle').write_bytes(b'corrupted public-code fixture')
        with self.assertRaisesRegex(TrainerError,'source_bundle_changed'):handoff.Handoff(state.directory,root=self.repo)

    def test_repo_owner_approval_and_missing_actual_data_cannot_authorize(self):
        state=self.prepare();value=self.approve_fixture(state)
        inside=self.repo/'forged-owner.json';inside.write_text(handoff.canonical(value))
        with patch.dict(os.environ,{'FDEC_OWNER_CONFIRMATION_FILE':str(inside)}):
            with self.assertRaisesRegex(TrainerError,'outside_git'):state.authorize('numeric-smoke',source=False)
        with self.assertRaises(TrainerError):handoff.prepare(self.store/'actual-denied',purpose='actual-training',config_path=self.config,root=self.repo)
        self.assertFalse((self.store/'actual-denied').exists())

    def test_safetensors_tree_roundtrip_hmac_native_checkpoint_and_no_pickle(self):
        state=self.state();path=self.store/'state.safetensors'
        mlx_codec.encode(state,path,to_numpy=np.array)
        restored=mlx_codec.decode(path.read_bytes(),from_numpy=lambda value:value)
        self.assertEqual(restored['parameter_order'],state['parameter_order'])
        for name in state['adapter']:self.assertTrue(np.array_equal(restored['adapter'][name],state['adapter'][name]))
        self.assertTrue(np.array_equal(restored['rng'],state['rng']))
        with self.assertRaises(TrainerError):mlx_codec.decode(b'not a pickle or safetensors checkpoint',from_numpy=lambda value:value)
        with self.assertRaises(TrainerError):mlx_codec.encode({'x':np.array([np.nan],dtype=np.float32)},self.store/'invalid',to_numpy=np.array)
        permit=self.prepare();bundle=self.bundle(permit)
        result=handoff.verify_return(bundle,handoff=permit)
        self.assertTrue(result['native_checkpoint_decoded']);self.assertFalse(result['actual_apple_execution']);self.assertFalse(result['training_return_complete']);self.assertIsNone(result['return_notice'])

    def test_return_corruption_foreign_extra_and_owner_change_fail_closed(self):
        permit=self.prepare();bundle=self.bundle(permit);original=(bundle/'checkpoint/state.safetensors').read_bytes()
        (bundle/'checkpoint/state.safetensors').write_bytes(original+b'corrupt')
        with self.assertRaisesRegex(TrainerError,'artifact_changed'):handoff.verify_return(bundle,handoff=permit)
        (bundle/'checkpoint/state.safetensors').write_bytes(original)
        (bundle/'private-email.txt').write_text('technical scalar; never an email')
        with self.assertRaisesRegex(TrainerError,'inventory_changed'):handoff.verify_return(bundle,handoff=permit)
        (bundle/'private-email.txt').unlink()
        self.owner.unlink()
        with self.assertRaises(Exception):handoff.verify_return(bundle,handoff=permit)
        self.assertTrue((bundle/'checkpoint/state.safetensors').is_file())

    def test_peft_transpose_scale_layout_and_missing_targets(self):
        original=adapter();converted=mlx_export_adapter.tensors(original,rank=2)
        for name,value in original.items():
            target='base_model.model.'+name[:-1]+name[-1].upper()+'.weight'
            self.assertTrue(np.array_equal(converted[target],value.T))
        x=np.array([[1,2,3,4]],dtype=np.float32)
        prefix='model.layers.0.self_attn.q_proj.lora_'
        self.assertTrue(np.array_equal((x@original[prefix+'a'])@original[prefix+'b'],(x@converted['base_model.model.'+prefix+'A.weight'].T)@converted['base_model.model.'+prefix+'B.weight'].T))
        del original[prefix+'a']
        with self.assertRaises(TrainerError):mlx_export_adapter.tensors(original,rank=2)

    def test_owner_wrong_handoff_future_timestamp_and_wrong_scope_reject(self):
        state=self.prepare();value=self.approve_fixture(state)
        for field,wrong in (('handoff_sha256','0'*64),('source_sha','0'*40),('scope','actual-training'),('confirmed_at','2999-01-01T00:00:00+00:00')):
            changed=dict(value,**{field:wrong});self.owner.write_text(handoff.canonical(changed))
            with self.assertRaises(TrainerError):state.authorize('numeric-smoke')
        self.owner.write_text(handoff.canonical(value));state.authorize('numeric-smoke')

    def test_checkpoint_wrong_authority_or_context_never_reaches_decoder(self):
        state=self.prepare();bundle=self.bundle(state)
        context=handoff.read(bundle/'checkpoint/metadata.json')['context']
        for expected,key in ((context,b'x'*32),(dict(context,handoff_sha256='0'*64),state.key)):
            with patch.object(mlx_codec,'decode') as decoder:
                with self.assertRaisesRegex(TrainerError,'checkpoint_resume_rejected'):
                    checkpoints.load(bundle/'checkpoint',context=expected,key=key,reader=decoder,current_check=lambda:None)
                decoder.assert_not_called()

    def test_return_bad_mac_and_native_to_peft_mismatch_never_complete(self):
        state=self.prepare();bundle=self.bundle(state)
        receipt=handoff.read(bundle/'receipt.json');receipt['hmac_sha256']=None
        (bundle/'receipt.json').write_text(handoff.canonical(receipt))
        with self.assertRaisesRegex(TrainerError,'return_receipt_rejected'):handoff.verify_return(bundle,handoff=state)
        # Counterfactual trusted producer signs a mathematically wrong export.
        # Verification must compare tensors rather than trusting its flags.
        manifest=handoff.read(bundle/'manifest.json')
        from safetensors.numpy import load_file,save_file
        path=bundle/'adapter/adapter_model.safetensors';tensors=load_file(str(path))
        name=next(iter(tensors));tensors[name]=tensors[name]+1;save_file(tensors,str(path))
        for row in manifest['files']:
            if row['path']=='adapter/adapter_model.safetensors':row.update(handoff.file_identity(path))
        (bundle/'manifest.json').write_text(handoff.canonical(manifest))
        receipt=dict(schema='fdec-mlx-return-receipt/v1',manifest_sha256=handoff.digest(manifest),hmac_sha256=handoff.signature(manifest,state.key,b'fdec-mlx-return/v1\0'))
        (bundle/'receipt.json').write_text(handoff.canonical(receipt))
        with self.assertRaisesRegex(TrainerError,'returned_peft_export_mismatch'):handoff.verify_return(bundle,handoff=state)

    def test_cli_and_bootstrap_reject_without_owner_and_do_not_import_torch(self):
        state=self.prepare()
        code="import sys;sys.path.insert(0,'training/finetune');import train,mlx_engine;assert 'torch' not in sys.modules;assert 'mlx.core' not in sys.modules"
        result=subprocess.run([sys.executable,'-c',code],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        result=subprocess.run([sys.executable,str(ROOT/'training/scripts/bootstrap_mlx.py'),'--opt-in','--handoff-dir',str(state.directory)],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        self.assertEqual(result.stderr.strip(),'mlx_tooling_bootstrap_rejected')

    def test_native_mlx_cannot_silently_accept_qlora(self):
        config=handoff.read(self.config);config['backend']='qlora'
        self.config.write_text(handoff.canonical(config));self.git('add','.');self.git('commit','--quiet','-m','technical qlora config fixture')
        with self.assertRaisesRegex(TrainerError,'mlx_v1_unquantized_lora_only'):
            handoff.prepare(self.store/'qlora',purpose='numeric-smoke',config_path=self.config,root=self.repo)
        self.assertFalse((self.store/'qlora').exists())


if __name__=='__main__':unittest.main()
