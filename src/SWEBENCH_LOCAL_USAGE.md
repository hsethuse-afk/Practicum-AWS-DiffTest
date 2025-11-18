# SWE-bench Local Runner

## Basic Usage

```bash
python src/run_swebench_local.py --instance-id <INSTANCE_ID>
```

## Example

```bash
python src/run_swebench_local.py --instance-id astropy__astropy-12907 --keep-repo
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--instance-id` | SWE-bench instance ID (required) | - |
| `--dataset` | Dataset name | `princeton-nlp/SWE-bench_Verified` |
| `--max-examples` | Max test examples | 200 |
| `--seed` | Random seed for reproducibility | - |
| `--verbose` | Enable verbose output | false |
| `--keep-repo` | Keep cloned repos for debugging | false |
| `--work-dir` | Work directory | temp |

## Output

- HTML report: `reports/<instance-id>.html`
- Cloned repos (if `--keep-repo`): BEFORE and AFTER versions
