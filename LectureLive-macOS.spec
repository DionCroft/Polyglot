# Native Apple Silicon build; never cross-compiled from Windows.
import os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

identity = os.environ.get("LECTURELIVE_CODESIGN_IDENTITY") or None
datas = [('assets', 'assets'), ('glossaries', 'glossaries'), ('docs', 'docs'),
         ('build/macos-assets/models', 'models'), ('build/macos-licenses', 'docs/licenses/macos-wheels')]
datas += collect_data_files('opencc')
a = Analysis(
    ['LectureLive.pyw'], pathex=[], datas=datas,
    binaries=collect_dynamic_libs('onnxruntime'),
    hiddenimports=['AppKit', 'Foundation', 'objc', 'PySide6.QtMultimedia'],
    excludes=['onnxruntime_qnn', 'winui3', 'winrt', 'pytest', 'ruff', 'onnx'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='LectureLive',
          console=False, argv_emulation=False, target_arch='arm64', upx=False,
          codesign_identity=identity, entitlements_file='assets/macos-entitlements.plist')
coll = COLLECT(exe, a.binaries, a.datas, name='LectureLive-macOS', upx=False)
app = BUNDLE(coll, name='LectureLive.app', icon='build/LectureLive.icns',
             bundle_identifier='io.github.dioncroft.lecturelive',
             version='0.5.0', info_plist={
                 'CFBundleDisplayName': 'LectureLive',
                 'CFBundleShortVersionString': '0.5.0',
                 'CFBundleVersion': '0.5.0',
                 'LSMinimumSystemVersion': '14.0',
                 'NSHighResolutionCapable': True,
                 'NSMicrophoneUsageDescription': 'LectureLive uses your microphone to create live lecture captions and translations entirely on this Mac. Audio is not uploaded.',
             })
