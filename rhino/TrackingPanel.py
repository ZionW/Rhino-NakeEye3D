#! python 3
"""Modeless Rhino Eto panel; controls the loaded .rhp and local webcam worker."""
import json
import os
import subprocess
import time
import urllib.request
import System
import Rhino
import Eto.Forms as forms
import Eto.Drawing as drawing
import scriptcontext
import sys

from urllib.parse import urlparse, unquote
script_path=unquote(urlparse(__file__).path) if __file__.startswith('file:') else __file__
if os.name=='nt' and script_path.startswith('/') and len(script_path)>2 and script_path[2]==':':script_path=script_path[1:]
ROOT=os.environ.get('NAKEDEYE3D_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(script_path)))
KEY='NakedEye3D.Panel'
if ROOT+'/rhino' not in sys.path: sys.path.insert(0,ROOT+'/rhino')
import importlib
import ViewportTracking as viewport_module
importlib.reload(viewport_module)
ViewportTracking=viewport_module.ViewportTracking

def ui(cls, **props):
    obj=cls()
    for key,value in props.items(): setattr(obj,key,value)
    return obj

def row(*controls):
    stack=ui(forms.StackLayout,Orientation=forms.Orientation.Horizontal,Spacing=8)
    for control in controls: stack.Items.Add(forms.StackLayoutItem(control))
    return stack
def inset(control):
    stack=ui(forms.StackLayout,Orientation=forms.Orientation.Horizontal,Spacing=4,Padding=drawing.Padding(13,0,12,0))
    stack.Items.Add(forms.StackLayoutItem(control))
    return stack

existing=scriptcontext.sticky.get(KEY)
if existing:
    existing.Topmost=False
    existing.BringToFront()
else:
    demo=scriptcontext.sticky.pop('NakedEye3D.Demo',None)
    if demo:
        demo[0].Stop(); demo[1].close()
    Rhino.RhinoApp.RunScript('_NakedEye3DStop',False)
    result,_=Rhino.PlugIns.PlugIn.LoadPlugIn(ROOT+'/rhino/bin/Debug/net7.0/NakedEye3D.rhp')
    if str(result)!='Success': raise RuntimeError(str(result))
    os.makedirs(ROOT+'/runtime',exist_ok=True)

    class TrackingPanel(forms.Form):
        def __init__(self):
            super().__init__()
            self.Title='裸視3D · Webcam 追蹤'
            self.Topmost=False
            self.Owner=Rhino.UI.RhinoEtoApp.MainWindowForDocument(Rhino.RhinoDoc.ActiveDoc)
            self.ClientSize=drawing.Size(229,715)
            self.Resizable=False
            self.worker=None; self.log=None; self.running=False
            self.fullscreen_state=None
            Rhino.RhinoApp.EscapeKeyPressed+=self.escape_fullscreen
            self.tracking=ViewportTracking()
            self.settings=dict(paused=True,stop=False,camera=0,calibration=0,mode='space',wave_enabled=False,sensitivity=1.)
            self.language=ui(forms.DropDown)
            for name in ['中文','English','日本語']: self.language.Items.Add(name)
            self.language.SelectedIndex=0
            self.language.SelectedIndexChanged+=self.translate
            self.space=ui(forms.Button)
            self.object=ui(forms.Button)
            self.space.Click+=lambda s,e:self.change_mode('space',e)
            self.object.Click+=lambda s,e:self.change_mode('object',e)
            self.label=ui(forms.Label,Text='準備就緒，按「開始追蹤」開啟 webcam')
            self.label.Wrap=forms.WrapMode.Word
            self.label.TextAlignment=forms.TextAlignment.Left
            self.label.Width=199
            self.preview=ui(forms.ImageView,Size=drawing.Size(224,168))
            self.preview_bitmap=None
            self.camera=ui(forms.NumericStepper,MinValue=0,MaxValue=8,Value=0)
            self.camera.Width=46
            self.language.Width=88
            self.start=ui(forms.Button,Text='開始／繼續追蹤')
            self.pause_button=ui(forms.Button,Text='暫停追蹤')
            self.start.Width=199
            self.pause_button.Width=199
            self.calibrate_button=ui(forms.Button,Text='校正目前頭部位置')
            self.stop_button=ui(forms.Button,Text='停止並還原視角')
            self.collapse_button=ui(forms.Button,Text='收回爆炸圖（原位置）')
            self.collapse_button.Click+=self.collapse
            self.start.Click+=self.begin
            self.pause_button.Click+=self.pause
            self.calibrate_button.Click+=self.calibrate
            self.stop_button.Click+=self.stop
            self.camera_label=ui(forms.Label,Width=66,TextAlignment=forms.TextAlignment.Left)
            self.strength_label=ui(forms.Label,Width=199,TextAlignment=forms.TextAlignment.Left)
            self.sensitivity_label=ui(forms.Label,Width=199,TextAlignment=forms.TextAlignment.Left)
            self.strength=ui(forms.Slider,MinValue=0,MaxValue=300,Value=100)
            self.sensitivity=ui(forms.Slider,MinValue=20,MaxValue=300,Value=100)
            self.strength.ValueChanged+=self.tune
            self.sensitivity.ValueChanged+=self.tune
            self.fullscreen_button=ui(forms.Button,Width=199)
            self.fullscreen_button.Click+=self.toggle_fullscreen
            self.KeyDown+=self.panel_keydown
            self.help_button=ui(forms.Button,Width=199)
            self.help_button.ToolTip='中文 / English / 日本語'
            for button in [self.space,self.object]: button.Width=97
            for control in [self.calibrate_button,self.stop_button,self.collapse_button,self.strength,self.sensitivity]: control.Width=199
            self.help_button.Click+=self.show_help
            layout=ui(forms.DynamicLayout,Padding=drawing.Padding(2,8,3,8),Spacing=drawing.Size(4,6))
            layout.AddRow(row(self.camera_label,self.camera,self.language))
            layout.AddRow(inset(row(self.space,self.object)))
            layout.AddRow(inset(self.start))
            layout.AddRow(inset(self.pause_button))
            layout.AddRow(inset(self.calibrate_button))
            layout.AddRow(inset(self.stop_button))
            layout.AddRow(inset(self.collapse_button))
            layout.AddRow(inset(self.label))
            layout.AddRow(self.preview)
            layout.AddRow(inset(self.strength_label))
            layout.AddRow(inset(self.strength))
            layout.AddRow(inset(self.sensitivity_label))
            layout.AddRow(inset(self.sensitivity))
            layout.AddRow(inset(self.fullscreen_button))
            layout.AddRow(inset(self.help_button))
            self.translate(None,None)
            self.Content=layout
            self.timer=ui(forms.UITimer,Interval=.033)
            self.timer.Elapsed+=self.update
            self.timer.Start()
            self.Closed+=self.close_panel

        def write(self):
            self.settings['heartbeat']=time.time()
            path=ROOT+'/runtime/control.json'
            with open(path+'.tmp','w') as f: json.dump(self.settings,f)
            os.replace(path+'.tmp',path)

        def tr(self,zh,en,ja):
            return (zh,en,ja)[self.language.SelectedIndex]

        def translate(self,s,e):
            self.Title=self.tr('裸視3D · Webcam 追蹤','NakedEye3D · Webcam tracking','裸眼3D · Webcam トラッキング')
            for control,text in [(self.camera_label,('📷 相機','📷 Cam','📷 カメラ')),
                (self.space,('🌌 空間模式','🌌 Space','🌌 空間')),
                (self.object,('🧸 物體模式','🧸 Object','🧸 物体')),
                (self.start,('▶️ 開始／繼續追蹤','▶️ Start / resume','▶️ 開始／再開')),
                (self.pause_button,('⏸️ 暫停追蹤','⏸️ Pause','⏸️ 一時停止')),
                (self.calibrate_button,('🎯 校正目前頭部位置','🎯 Calibrate head','🎯 頭の位置を調整')),
                (self.stop_button,('🏠 停止並還原視角','🏠 Stop / restore view','🏠 停止・視点を復元')),
                (self.collapse_button,('🧩 收回爆炸圖（原位置）','🧩 Restore parts','🧩 分解表示を戻す')),
                (self.fullscreen_button,('🖥️ 全螢幕（Esc 返回）','🖥️ Full screen / Esc','🖥️ 全画面・Escで戻る')),
                (self.help_button,('💡 使用說明','💡 Help','💡 使い方'))]:
                control.Text=self.tr(*text)
            self.space.Enabled=self.settings['mode']!='space'
            self.object.Enabled=self.settings['mode']!='object'
            self.tune(None,None)
            self.label.Text=self.tr('準備就緒','Ready','準備完了')

        def tune(self,s,e):
            self.tracking.strength=self.strength.Value/100.
            self.tracking.sensitivity=self.sensitivity.Value/100.
            self.settings['sensitivity']=self.tracking.sensitivity
            self.strength_label.Text=self.tr('👀 視角影響程度','👀 View strength','👀 視点の移動量')+' : '+str(self.strength.Value)+'%'
            self.sensitivity_label.Text=self.tr('🐇 靈敏度','🐇 Sensitivity','🐇 感度')+' : '+str(self.sensitivity.Value)+'%'
            self.write()

        def show_help(self,s,e):
            text=self.tr(
                '開始時以目前攝影機為基準。空間模式：頭部左右、上下與遠近移動控制視角。物體模式：拇指、食指與中指抓握後移動手掌旋轉攝影機；抓握期間暫停頭部控制。雙手各伸出食指，拉開可展開爆炸圖，靠攏或放開即還原。紅球代表偵測到手，綠球代表抓握啟動。視角影響程度控制頭部與抓握的移動幅度；靈敏度越高，反應越快、平滑越少。0% 幅度會固定頭部與抓握視角。揮手功能已停用。',
                'Start captures the current camera as the baseline. Space mode: move your head sideways, vertically or closer/farther. Object mode: grasp with thumb, index and middle finger, then move your hand to orbit the camera. Head control pauses while grasping. Extend both index fingers and separate them to explode parts; bring them together or release to restore. Red means hand detected; green means grasp active. Strength adjusts head and grasp movement. Higher sensitivity responds faster with less smoothing. 0% strength fixes head and grasp movement. Waving is disabled.',
                '開始時のカメラを基準にします。空間モードでは頭の左右・上下・前後移動で視点を操作します。物体モードでは親指・人差し指・中指でつかみ、手を動かしてカメラを回転します。つかんでいる間は頭の操作を停止します。両手の人差し指を伸ばし、離すと分解表示、近づけるか解除すると元に戻ります。赤い球は手の検出、緑はつかみ操作を示します。移動量は頭と手による視点変化の大きさ、感度は反応速度を調整します。感度が高いほど平滑化が少なくなります。移動量0%で頭と手による視点移動を固定します。手を振る操作は無効です。')
            dialog=ui(forms.Dialog,Title=self.help_button.Text,ClientSize=drawing.Size(480,300),Resizable=True)
            label=ui(forms.Label,Text=text,Wrap=forms.WrapMode.Word)
            button=ui(forms.Button,Text=self.tr('關閉','Close','閉じる'))
            button.Click+=lambda s,e:dialog.Close()
            layout=ui(forms.DynamicLayout,Padding=drawing.Padding(18),Spacing=drawing.Size(10,10))
            layout.AddRow(label);layout.AddRow(button);dialog.Content=layout
            dialog.ShowModal(self)

        def toggle_fullscreen(self,s,e):
            try:self.enter_fullscreen(s,e)
            except Exception as error:
                self.label.Text=str(error)
                self.restore_fullscreen()

        def enter_fullscreen(self,s,e):
            if self.fullscreen_state:
                self.escape_fullscreen(s,e)
                return
            view=Rhino.RhinoDoc.ActiveDoc.Views.ActiveView
            if view is None:return
            import rhinoscriptsyntax as rs
            if not rs.IsCommand('Fullscreen'):
                self.label.Text=self.tr('此 Rhino 版本不支援 Fullscreen 指令','Fullscreen command unavailable in this Rhino version','この Rhino では Fullscreen コマンドは使えません')
                Rhino.RhinoApp.RunScript('_Fullscreen',False)
                return
            self.fullscreen_state=(view,view.Maximized,Rhino.DocObjects.ViewportInfo(view.ActiveViewport),False)
            if not Rhino.RhinoApp.RunScript('_Fullscreen',False):
                self.restore_fullscreen()
                return
            self.restore_fullscreen()

        def panel_keydown(self,s,e):
            if e.Key==forms.Keys.Escape and self.fullscreen_state:
                e.Handled=True
                self.escape_fullscreen(s,e)

        def escape_fullscreen(self,s,e):
            if not self.fullscreen_state:return
            self.restore_fullscreen()

        def native_exit(self,s,e):
            self.restore_fullscreen()

        def restore_fullscreen(self):
            if not self.fullscreen_state:return
            view,maximized,projection,already=self.fullscreen_state
            self.fullscreen_state=None
            self.tracking.reset_explosion()
            original=Rhino.DocObjects.ViewportInfo(self.tracking.original) if self.tracking.original else None
            self.tracking.stop(False)
            view.Maximized=maximized
            view.ActiveViewport.SetViewProjection(projection,False)
            projection.Dispose();view.Redraw()
            if self.running and not self.settings.get('paused'):
                self.tracking.start(view)
                if original:
                    self.tracking.original.Dispose();self.tracking.original=original;original=None
            if original:original.Dispose()
            self.settings['calibration']+=1;self.write()
            self.label.Text=self.tr('已返回原本狀態','Previous view restored','元の状態に戻りました')

        def change_mode(self,mode,e):
            self.settings['mode']=mode
            self.settings['calibration']+=1
            self.translate(None,None)
            self.write()

        def begin(self,s,e):
            try:
                if not self.running or self.settings.get('paused'):
                    doc=Rhino.RhinoDoc.ActiveDoc
                    view=doc.Views.ActiveView
                    if view and not view.ActiveViewport.IsPerspectiveProjection: view=None
                    if view is None: raise RuntimeError(self.tr('請先開啟透視視窗','Open a perspective viewport first','透視ビューを開いてください'))
                    doc.Views.ActiveView=view
                    self.tracking.start(view)
                    self.settings['calibration']+=1
                    self.running=True
                self.settings.update(paused=False,stop=False,camera=int(self.camera.Value))
                self.write()
                if self.worker is None or self.worker.poll() is not None:
                    if self.log: self.log.close()
                    self.log=open(ROOT+'/runtime/webcam.log','w')
                    if os.name=='nt':
                        executable=os.path.join(ROOT,'.venv','Scripts','pythonw.exe')
                        if not os.path.isfile(executable):raise RuntimeError(self.tr('請先執行 Windows 安裝程式','Run the Windows setup first','先に Windows セットアップを実行してください'))
                        self.worker=subprocess.Popen([executable,os.path.join(ROOT,'tools','webcam_tracker.py'),'--client','rhino'],stdout=self.log,stderr=self.log,cwd=ROOT,creationflags=0x08000000)
                    else:
                        self.worker=subprocess.Popen(['/usr/bin/open','-W','-n','-a',ROOT+'/tools/NakedEye3D Webcam.app'],stdout=self.log,stderr=self.log,cwd=ROOT)
                    self.label.Text=self.tr('正在開啟 webcam…','Opening webcam…','Webcam を起動中…')
                self.camera.Enabled=False
            except Exception as error: self.label.Text=str(error)

        def pause(self,s,e):
            self.settings['paused']=True; self.write()
            self.tracking.pause()
            self.label.Text=self.tr('已暫停，保留目前視角','Paused; view preserved','一時停止・視点を保持')

        def calibrate(self,s,e):
            self.settings['calibration']+=1; self.write()

        def collapse(self,s,e):
            self.tracking.reset_explosion()
            self.settings['calibration']+=1;self.write()
            self.label.Text=self.tr('爆炸圖已收回；請先解除雙食指手勢','Restored; release both index fingers','復元しました。両手の指操作を解除してください')

        def stop(self,s,e):
            self.settings.update(stop=True,paused=True); self.write()
            if self.worker and self.worker.poll() is None:
                try: self.worker.wait(timeout=2)
                except subprocess.TimeoutExpired: pass
            Rhino.RhinoApp.RunScript('_NakedEye3DStop',False)
            self.tracking.stop(True)
            self.running=False; self.camera.Enabled=True
            self.label.Text=self.tr('已停止，原始視角已還原','Stopped; original view restored','停止・元の視点を復元')
            self.preview.Image=None
            if self.preview_bitmap: self.preview_bitmap.Dispose(); self.preview_bitmap=None

        def update(self,s,e):
            if self.worker is None or self.settings.get('stop'): return
            self.write()
            if not self.settings.get('paused'):
                try: self.tracking.update()
                except Exception as error:
                    self.pause(s,e); self.label.Text=str(error)
            try:
                with urllib.request.urlopen('http://127.0.0.1:39540',timeout=.08) as response: data=response.read()
                if data:
                    stream=System.IO.MemoryStream(System.Array[System.Byte](data))
                    bitmap=drawing.Bitmap(stream)
                    stream.Dispose()
                    old=self.preview_bitmap
                    self.preview.Image=bitmap; self.preview_bitmap=bitmap
                    if old: old.Dispose()
            except Exception: pass
            try:
                with open(ROOT+'/runtime/status.json') as f: value=json.load(f)
                if time.time()-value['time']<3:
                    self.label.Text=self.tr('追蹤中','Tracking','トラッキング中')+' · '+self.tr('遠近比例','Depth ratio','距離比')+': '+str(value.get('depth','—')) if not self.settings.get('paused') else self.tr('已暫停','Paused','一時停止中')
                if self.worker.poll() is not None:
                    self.camera.Enabled=True
                    if not value.get('error') and self.settings.get('stop') is False:
                        self.label.Text=self.tr('相機程序已退出，請重新開始','Camera exited; restart tracking','カメラが終了しました。再開してください')
            except (IOError,ValueError,KeyError): pass

        def close_panel(self,s,e):
            self.escape_fullscreen(s,e)
            self.restore_fullscreen()
            Rhino.RhinoApp.EscapeKeyPressed-=self.escape_fullscreen
            self.stop(s,e); self.timer.Stop()
            if self.log: self.log.close()
            scriptcontext.sticky.pop(KEY,None)

    panel=TrackingPanel()
    scriptcontext.sticky[KEY]=panel
    panel.Show()
    if hasattr(panel.ControlObject,'HidesOnDeactivate'):
        panel.ControlObject.HidesOnDeactivate=True
    print('裸視3D 控制面板已開啟')
