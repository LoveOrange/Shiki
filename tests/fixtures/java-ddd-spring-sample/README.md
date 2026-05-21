# Java DDD Spring Sample

This is the smallest local verification fixture for Shiki. It validates init,
path conventions, entry discovery, and module inference. It is not part of the
runtime context created in consumer projects.

## Shape

```text
src/main/java/com/example/shop/
  adapter/order/web/OrderController.java
  application/order/...
  domain/order/...
  infrastructure/order/...
```

## Local Verification

From the Shiki repository root:

```bash
python3 tools-skills/scripts/verify.py
```

`scan.py` calls a `devagent` command for deep entry analysis. The verification
script injects a deterministic shim so this fixture can run without a real agent.
