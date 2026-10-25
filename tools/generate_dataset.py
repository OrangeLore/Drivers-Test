#!/usr/bin/env python3
"""Generate an importable question set with the common grounded local pipeline."""
import argparse
import json
import os
from pathlib import Path
import generator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', required=True)
    parser.add_argument('--key', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--jurisdiction', default='')
    parser.add_argument('--testsize', type=int, default=30)
    parser.add_argument('--passmark', type=int, default=0)
    parser.add_argument('--n', type=int, default=120)
    parser.add_argument('--model', default=os.environ.get('AC7_MODEL', 'local-model'))
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    meta = {'key': args.key, 'name': args.name, 'jurisdiction': args.jurisdiction,
            'testSize': args.testsize, 'passMark': args.passmark or max(1, round(args.testsize * 0.8))}
    dataset = generator.run_full(pdf_bytes=Path(args.pdf).read_bytes(), meta=meta, model=args.model, target=args.n)
    if len(dataset['questions']) < args.testsize:
        raise SystemExit('Not enough grounded questions for requested test size; reduce --testsize or retry.')
    # Do not include workstation paths, PDF filenames or model IDs in portable metadata.
    Path(args.out).write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Question set generated. Review against the official handbook before use.')


if __name__ == '__main__':
    main()
