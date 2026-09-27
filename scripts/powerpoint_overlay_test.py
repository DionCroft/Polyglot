import os,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
os.environ['LECTURELIVE_DATA']=str(root/'tests/powerpoint-data')
from app.system.offline import enforce_offline
enforce_offline()
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.captions.state import Caption
from app.system.windows import user32
app=QApplication([]);w=MainWindow();w.showMinimized()
w.overlay.set_caption(Caption(1,0,5,'The interrupt service routine should execute as quickly as possible.','中断服务程序应尽快执行。',True));w.overlay.show();w.overlay.lock(True)
def report():
 (root/'docs/evidence/powerpoint-overlay-state.json').write_text(json.dumps({'hwnd':int(w.overlay.winId()),'rect':[w.overlay.x(),w.overlay.y(),w.overlay.width(),w.overlay.height()],'locked':w.cfg.locked,'visible':w.overlay.isVisible(),'style':hex(user32.GetWindowLongPtrW(int(w.overlay.winId()),-20))},indent=2))
timer=QTimer();timer.timeout.connect(report);timer.start(500)
QTimer.singleShot(240000,w.close)
app.exec()
