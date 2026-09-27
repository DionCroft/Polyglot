import os,time,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
os.environ['LECTURELIVE_DATA']=str(root/'tests/visual-data')
from app.system.offline import enforce_offline
enforce_offline()
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from app.ui.main_window import MainWindow
from app.captions.state import Caption
from app.system.windows import user32
app=QApplication([]);w=MainWindow();w.show();QTest.qWait(500)
def pump(ms):
 end=time.monotonic()+ms/1000
 while time.monotonic()<end:app.processEvents();time.sleep(.01)
w.bridge.event.connect(lambda k,v:print(k, str(v)[:200],flush=True) if k in {"state","warning","backend"} else None)
limit=time.monotonic()+15
while not w.start_button.isEnabled() and time.monotonic()<limit:pump(50)
assert w.start_button.isEnabled()
# Capture using Qt itself for reproducible artifact comparison.
w.grab().save(str(root/'docs/evidence/control-panel.png'))
w.overlay.set_caption(Caption(1,0,5,'The interrupt service routine should execute as quickly as possible.','中断服务程序应尽快执行。',True));w.overlay.show();w.overlay.lock(True);QTest.qWait(300)
w.overlay.grab().save(str(root/'docs/evidence/overlay.png'))
style=user32.GetWindowLongPtrW(int(w.overlay.winId()),-20)
assert style&0x20 and style&0x08000000
w.overlay.lock(False);assert not user32.GetWindowLongPtrW(int(w.overlay.winId()),-20)&0x20
w.wav=str(root/'tests/fixtures/technical.wav');w.start_stop();limit=time.monotonic()+30
while time.monotonic()<limit and not (w.last_caption and w.last_caption.chinese):pump(50)
if not (w.last_caption and w.last_caption.chinese):
 w.pipeline.close();raise AssertionError('UI did not receive translated caption: '+w.warning.text())
w.pause();pump(50);assert not w.overlay.isVisible();epoch=w.pipeline.epoch
pump(600);assert w.pipeline.epoch==epoch
w.pause();pump(50);w.stop();limit=time.monotonic()+15
while w.pipeline and time.monotonic()<limit:pump(50)
assert w.pipeline is None,'UI shutdown did not finish'
w.close();app.processEvents()
(root/'docs/evidence/ui-verification.json').write_text(json.dumps({'caption_delivery':True,'pause_hides_overlay':True,'native_clickthrough_flag':True,'native_noactivate_flag':True,'shutdown_joined':True,'screens':[s.name() for s in app.screens()]},indent=2))
print('UI checks passed')
