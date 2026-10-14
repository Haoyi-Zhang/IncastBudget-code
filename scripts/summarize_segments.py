"""Recompute the unfiltered current segment-path comparison and paper table."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('records', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.records.read_bytes()
    record = json.loads(raw)
    if not record['all_outputs_equal'] or not record['source_unchanged'] or record['rounds'] != 3 or record['samples_retained'] != 48:
        raise ValueError('Incomplete current comparison')
    names = [('pilot.json', 'Window pilot', 96), ('bounded.jsonl', 'Window domain', 20736)]
    names += [('sparse-' + str(n), 'Sparse ' + str(n), 1) for n in (8, 16, 32, 64, 128, 256)]
    seen = {}
    for row in record['samples']:
        key = row['group'], row['round'], row['route']
        if key in seen or row['wall_seconds'] <= 0 or row['process_cpu_seconds'] < 0:
            raise ValueError('Duplicate or invalid observation')
        seen[key] = row
    required = {(name, i, route) for name, _, _ in names for i in range(3) for route in ('transparent', 'segments')}
    if set(seen) != required:
        raise ValueError('Missing or additional observations')
    summary = []
    for name, label, count in names:
        ratios = []
        for i in range(3):
            a, b = seen[name, i, 'segments'], seen[name, i, 'transparent']
            if any(a[k] != b[k] for k in ('instances', 'input_sha256', 'output_sha256', 'output_bytes')) or a['instances'] != count:
                raise ValueError('Mismatched complete-path result')
            ratios.append(a['wall_seconds'] / b['wall_seconds'])
        summary.append(dict(group=name, label=label, instances=count, matched_rounds=3,
                            median_segment_over_transparent_wall=statistics.median(ratios),
                            all_ratios=ratios))
    args.output.mkdir(parents=True, exist_ok=True)
    result = dict(record_sha256=hashlib.sha256(raw).hexdigest(), groups=summary,
                  interpretation='Median of three unfiltered same-output complete-group wall ratios; repeated authored controls, not independent deployed workloads')
    (args.output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    lines = [r'\begin{tabular}{@{}lrr@{}}', r'\toprule', r'Existing input & Count & Segment/transparent\\', r'\midrule']
    for row in summary:
        lines.append(f"{row['label']} & {row['instances']:,} & {row['median_segment_over_transparent_wall']:.3f}" + r'\\')
    lines += [r'\bottomrule', r'\end{tabular}']
    (args.output / 'summary.tex').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'groups': len(summary), 'samples': len(seen), 'output': str(args.output)}))

if __name__ == '__main__':
    main()
