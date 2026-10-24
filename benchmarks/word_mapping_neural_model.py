"""Explicit, revision-pinned download; inference elsewhere is strictly offline."""
import argparse
import hashlib
from pathlib import Path

from voynich_smt.data.corpus import digest, write_json

MODEL_ID = 'pstroe/roberta-base-latin-cased'
REVISION = '0f5e1a95f76fafac3002f8349fa5c6e41129ed6f'
DEFAULT_MODEL = Path('data/models/latin-roberta')


def file_hashes(root):
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_file() and '.cache' not in path.parts and path.name != 'manifest.json':
            with path.open('rb') as handle:
                result[str(path.relative_to(root))] = hashlib.file_digest(handle, 'sha256').hexdigest()
    return result


def download(out=DEFAULT_MODEL):
    from huggingface_hub import snapshot_download
    from transformers import AutoModelForMaskedLM, RobertaTokenizerFast
    out = Path(out)
    if (out / 'manifest.json').exists():
        raise ValueError('Model already installed; use the existing local snapshot')
    snapshot_download(MODEL_ID, revision=REVISION, local_dir=out / 'original', token=False,
        allow_patterns=['README.md', 'config.json', 'merges.txt', 'vocab.json',
                        'tokenizer_config.json', 'pytorch_model.bin'])
    # Standard architecture only, no remote Python. Transformers uses the
    # restricted weights-only torch loader; save a safetensors inference copy.
    model = AutoModelForMaskedLM.from_pretrained(out / 'original', local_files_only=True,
        trust_remote_code=False, use_safetensors=False)
    # Published tokenizer_config.json is actually a tokenizers backend dump.
    # Reconstruct the standard fast RoBERTa tokenizer from the published BPE
    # vocabulary/merges instead of interpreting backend objects as config kwargs.
    tokenizer = RobertaTokenizerFast(vocab_file=str(out / 'original/vocab.json'),
        merges_file=str(out / 'original/merges.txt'), add_prefix_space=True,
        model_max_length=model.config.max_position_embeddings - 2)
    model.save_pretrained(out / 'inference', safe_serialization=True)
    tokenizer.save_pretrained(out / 'inference')
    protocol = {'model_id': MODEL_ID, 'revision': REVISION,
        'files_sha256': file_hashes(out), 'remote_code': False,
        'tokenizer_adapter': 'standard RobertaTokenizerFast from published vocab/merges; prefix space; BOS/EOS',
        'source': f'https://huggingface.co/{MODEL_ID}/tree/{REVISION}',
        'pretraining_overlap': 'unknown; Caesar exposure possible; scorer probe only'}
    write_json(out / 'manifest.json', {'protocol': protocol, 'sha256': digest(protocol)})
    print(f'Installed {MODEL_ID}@{REVISION} at {out}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=DEFAULT_MODEL)
    download(parser.parse_args().out)
