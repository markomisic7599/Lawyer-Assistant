# PyInstaller spec — build from repo root:
#   pyinstaller contract_reviewer/contract_reviewer.spec
#
# Optional: add assets\icon.ico under Windows shortcut / exe icon via icon= below.

import sys
from pathlib import Path

block_cipher = None
# SPECPATH is the folder containing this .spec file (the package directory).
cr = Path(SPECPATH).resolve()
root = cr.parent

a = Analysis(
    [str(cr / "desktop_main.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(cr / "assets"), "contract_reviewer/assets"),
    ]
    if (cr / "assets").exists()
    else [],
    hiddenimports=[
        "gradio",
        "docx",
        "docx.oxml",
        "openai",
        "rapidfuzz",
        "webview",
        "dotenv",
        "contract_reviewer",
        "contract_reviewer.app",
        "contract_reviewer.review_pipeline",
        "contract_reviewer.llm_client",
        "contract_reviewer.docx_reader",
        "contract_reviewer.docx_annotator",
        "contract_reviewer.span_mapper",
        "contract_reviewer.prompts",
        "contract_reviewer.settings",
        "contract_reviewer.file_utils",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ContractReviewer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ContractReviewer",
)
