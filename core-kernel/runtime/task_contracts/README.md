# Task Contracts

Task contracts are the stable executable units in Shiki. Each contract declares:

- `id`
- `stage`
- `kind`
- `goal`
- `inputs`
- `references`
- optional `artifact`
- `checks`
- `done_condition`
- optional `tech_contracts`
- `workflow_ref`

Runner logic routes from plan rows to these YAML files. Workflows are loaded only
after the contract is selected.
