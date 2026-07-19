import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core-kernel"))

from _lib.task_contracts import load_task_contract


def top_level_keys(text):
    keys = set()
    for line in text.splitlines():
        if line and not line[0].isspace() and ":" in line:
            keys.add(line.split(":", 1)[0])
    return keys


class TaskContractTests(unittest.TestCase):
    def test_all_contracts_resolve(self):
        contract_root = ROOT / "core-kernel/runtime/task_contracts"
        for path in sorted(contract_root.rglob("*.yaml")):
            relative = path.relative_to(contract_root).as_posix()
            with self.subTest(contract=relative):
                contract = load_task_contract(relative)
                self.assertTrue(contract["_canonical_ref"])
                self.assertTrue((ROOT / contract["workflow_ref"]).is_file())

    def test_alias_contracts_are_minimal(self):
        contract_root = ROOT / "core-kernel/runtime/task_contracts"
        aliases = 0
        for path in sorted(contract_root.rglob("*.yaml")):
            text = path.read_text(encoding="utf-8")
            if "kind: alias" not in text:
                continue
            aliases += 1
            self.assertEqual({"kind", "id", "canonical"}, top_level_keys(text), path)
        self.assertGreater(aliases, 0)

    def test_workflows_delegate_inputs_to_contracts(self):
        for path in sorted((ROOT / "core-kernel/workflows").rglob("*.md")):
            if path.name == "README.md":
                continue
            with self.subTest(workflow=path.relative_to(ROOT).as_posix()):
                self.assertNotIn("## Load", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
