# Model artifact

Place the trained paper checkpoint here as:

`certfusion.pt`

The backend accepts either a raw PyTorch `state_dict` or a dictionary containing `model_state_dict`.

The repository intentionally does **not** fabricate or ship trained weights. Without this file the application runs in clearly labelled `research-demo` mode, using an input-sensitive deterministic surrogate only to exercise the complete UI, rule, verification, uncertainty, reporting, and audit workflow.
