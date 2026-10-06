"""Separate evaluation-only entry point. No fitting and no sealed-input writes."""
import json
import hashlib
import io
import zipfile
from pathlib import Path
from datetime import datetime,timezone
from stage16r_seal import unprotect


def load_authorized(authorization_path,seal_root):
    auth=json.loads(Path(authorization_path).read_text(encoding='utf-8'))
    required={'user_authorization','requester','scope','model_sha256','preprocessor_sha256','feature_sha256','threshold_sha256','commitment_id','operation'}
    if not required.issubset(auth) or auth['user_authorization'] is not True or auth['operation']!='frozen_evaluation' or auth['scope'] not in ('final_test','independent_evaluation'):
        raise PermissionError('Recorded user authorization and frozen artifacts required')
    for field in ('model_sha256','preprocessor_sha256','feature_sha256','threshold_sha256'):
        if len(auth[field])!=64 or any(c not in '0123456789abcdef' for c in auth[field]): raise PermissionError('Invalid frozen artifact hash')
        artifact=Path(auth.get('frozen_artifact_paths',{}).get(field,''))
        if not artifact.is_file() or hashlib.sha256(artifact.read_bytes()).hexdigest()!=auth[field]: raise PermissionError('Frozen artifact missing or changed')
    root=Path(seal_root)
    public=json.loads((root/'public_commitment.json').read_text())
    if auth['commitment_id']!=public['commitment_id']: raise PermissionError('Mismatched evaluation commitment')
    if public['disposition']!='SEALED': raise PermissionError('Quarantined holdout cannot be evaluated')
    blob=(root/'evaluation.dpapi').read_bytes()
    if hashlib.sha256(blob).hexdigest()!=public['encrypted_envelope_sha256']: raise PermissionError('Envelope hash mismatch')
    log={'utc':datetime.now(timezone.utc).isoformat(),**auth}
    with (root/'authorized_access.jsonl').open('a',encoding='utf-8') as stream: stream.write(json.dumps(log,sort_keys=True)+'\n')
    # Scope-filter after authentication; never release the other partition or private salt.
    output=io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(unprotect(blob))) as incoming, zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as selected:
        for name in incoming.namelist():
            if name.startswith(auth['scope']+'/'):
                selected.writestr(name,incoming.read(name))
    return output.getvalue()
