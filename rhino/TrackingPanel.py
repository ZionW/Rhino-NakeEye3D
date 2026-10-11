#! python 3
"""Open the webcam panel in the current Rhino document; never load demo files."""
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
host=None
for assembly in System.AppDomain.CurrentDomain.GetAssemblies():
    host_type=assembly.GetType('RhinoNakeEye3D.PanelHost.TrackingHost')
    if host_type:
        host=host_type.GetProperty('Pending').GetValue(None)
        if host is not None:break
if host is not None:
    floating=scriptcontext.sticky.get(KEY)
    if floating:floating.Close()
    KEY='NakedEye3D.DockedPanel.'+str(host.GetHashCode())
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
    stack=ui(forms.StackLayout,Orientation=forms.Orientation.Horizontal,Spacing=5)
    for control in controls: stack.Items.Add(forms.StackLayoutItem(control))
    return stack
def inset(control):
    stack=ui(forms.StackLayout,Orientation=forms.Orientation.Horizontal,Spacing=4,Padding=drawing.Padding(13,0,12,0))
    stack.Items.Add(forms.StackLayoutItem(control))
    return stack

existing=scriptcontext.sticky.get(KEY)
if host is not None and existing is not None:
    try: existing.close_panel(None,None)
    except Exception:
        existing.timer.Stop()
        scriptcontext.sticky.pop(KEY,None)
    existing=None
if existing:
    if host is None:
        existing.Topmost=False
        existing.BringToFront()
    else:host.Content=existing
else:
    demo=scriptcontext.sticky.pop('NakedEye3D.Demo',None)
    if demo:
        demo[0].Stop(); demo[1].close()
    os.makedirs(ROOT+'/runtime',exist_ok=True)

    class TrackingPanel(forms.Panel if host is not None else forms.Form):
        def __init__(self):
            super().__init__()
            if host is None:
                self.Title='裸視3D · Webcam 追蹤'
                self.Topmost=False
                self.Owner=Rhino.UI.RhinoEtoApp.MainWindowForDocument(Rhino.RhinoDoc.ActiveDoc)
                self.ClientSize=drawing.Size(229,520)
                self.Resizable=False
            self.worker=None; self.log=None; self.running=False
            self.fullscreen_state=None
            Rhino.RhinoApp.EscapeKeyPressed+=self.escape_fullscreen
            self.tracking=ViewportTracking()
            self.settings=dict(paused=True,stop=False,camera=0,calibration=0,mode='space',wave_enabled=False,sensitivity=1.,explosion_method='two_index')
            self.language=ui(forms.DropDown)
            for name in ['中文','English','日本語']: self.language.Items.Add(name)
            self.language.SelectedIndex=0
            self.language.SelectedIndexChanged+=lambda s,e:self.safe(self.translate,s,e)
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
            self.pause_button.Width=97
            self.calibrate_button=ui(forms.Button,Text='校正目前頭部位置')
            self.stop_button=ui(forms.Button,Text='停止並還原視角')
            self.collapse_button=ui(forms.Button,Text='收回爆炸圖（原位置）')
            self.collapse_button.Click+=self.collapse
            self.start.Click+=self.toggle_tracking
            self.pause_button.Click+=self.pause
            self.calibrate_button.Click+=self.calibrate
            self.stop_button.Click+=self.stop
            self.camera_label=ui(forms.Label,Width=66,TextAlignment=forms.TextAlignment.Left)
            self.strength_label=ui(forms.Label,Width=199,TextAlignment=forms.TextAlignment.Left)
            self.sensitivity_label=ui(forms.Label,Width=199,TextAlignment=forms.TextAlignment.Left)
            self.strength=ui(forms.Slider,MinValue=0,MaxValue=300,Value=100)
            self.sensitivity=ui(forms.Slider,MinValue=20,MaxValue=300,Value=100)
            self.strength.ValueChanged+=lambda s,e:self.safe(self.tune,s,e)
            self.sensitivity.ValueChanged+=lambda s,e:self.safe(self.tune,s,e)
            self.explosion_label=ui(forms.Label,Width=199,TextAlignment=forms.TextAlignment.Left)
            self.explosion_slider=ui(forms.Slider,Width=199,MinValue=100,MaxValue=500,Value=300)
            self.explosion_slider.ValueChanged+=lambda s,e:self.safe(self.tune,s,e)
            self.explosion_method=ui(forms.DropDown,Width=199)
            self.explosion_method.SelectedIndexChanged+=lambda s,e:self.safe(self.change_explosion_method,s,e)
            self.fullscreen_button=ui(forms.Button,Width=199)
            self.fullscreen_button.Click+=self.toggle_fullscreen
            self.KeyDown+=self.panel_keydown
            self.help_button=ui(forms.Button,Width=199)
            self.help_button.ToolTip='中文 / English / 日本語'
            for button in [self.space,self.object,self.calibrate_button,self.stop_button,self.fullscreen_button,self.help_button]: button.Width=97
            self.collapse_button.Width=199
            for control in [self.strength,self.sensitivity,self.explosion_slider]: control.Width=94
            for label in [self.strength_label,self.sensitivity_label,self.explosion_label]: label.Width=100
            self.help_button.Click+=self.show_help
            layout=ui(forms.DynamicLayout,Padding=drawing.Padding(2,8,3,8),Spacing=drawing.Size(4,4))
            layout.AddRow(row(self.camera_label,self.camera,self.language))
            layout.AddRow(inset(row(self.space,self.object)))
            layout.AddRow(inset(self.start))
            layout.AddRow(inset(row(self.calibrate_button,self.stop_button)))
            layout.AddRow(inset(self.label))
            layout.AddRow(self.preview)
            layout.AddRow(inset(row(self.strength_label,self.strength)))
            layout.AddRow(inset(row(self.sensitivity_label,self.sensitivity)))
            layout.AddRow(inset(self.explosion_method))
            layout.AddRow(inset(row(self.explosion_label,self.explosion_slider)))
            layout.AddRow(inset(self.collapse_button))
            layout.AddRow(inset(row(self.fullscreen_button,self.help_button)))
            self.translate(None,None)
            self.Content=ui(forms.Scrollable,Content=layout) if host is not None else layout
            self.timer=ui(forms.UITimer,Interval=.033)
            self.timer.Elapsed+=self.update
            self.timer.Start()
            if host is None:self.Closed+=self.close_panel
            else:host.StopTracking=System.Action(lambda:self.stop(None,None))

        def safe(self,handler,s,e):
            try:handler(s,e)
            except Exception as error:
                import traceback
                with open(ROOT+'/runtime/panel-error.log','w') as f:f.write(traceback.format_exc())
                self.label.Text=str(error)

        def write(self):
            self.settings['heartbeat']=time.time()
            path=ROOT+'/runtime/control.json'
            with open(path+'.tmp','w') as f: json.dump(self.settings,f)
            os.replace(path+'.tmp',path)

        def tr(self,zh,en,ja):
            return (zh,en,ja)[self.language.SelectedIndex]

        def translate(self,s,e):
            if host is None:self.Title=self.tr('裸視3D · Webcam 追蹤','NakedEye3D · Webcam tracking','裸眼3D · Webcam トラッキング')
            for control,text in [(self.camera_label,('📷 相機','📷 Cam','📷 カメラ')),
                (self.space,('🌌 空間模式','🌌 Space','🌌 空間')),
                (self.object,('🧸 物體模式','🧸 Object','🧸 物体')),
                (self.start,('▶️ 開始／繼續','▶️ Start','▶️ 開始／再開')),
                (self.pause_button,('⏸️ 暫停','⏸️ Pause','⏸️ 一時停止')),
                (self.calibrate_button,('🎯 校正','🎯 Calibrate','🎯 調整')),
                (self.stop_button,('🏠 停止還原','🏠 Restore','🏠 停止・復元')),
                (self.collapse_button,('🧩 收回爆炸圖（原位置）','🧩 Restore parts','🧩 分解表示を戻す')),
                (self.fullscreen_button,('🖥️ 全螢幕','🖥️ Fullscreen','🖥️ 全画面')),
                (self.help_button,('💡 使用說明','💡 Help','💡 使い方'))]:
                control.Text=self.tr(*text)
            selected=0 if self.settings['explosion_method']=='two_index' else 1
            self.explosion_method.Items.Clear()
            self.explosion_method.Items.Add(self.tr('☝️ 雙食指控制爆炸圖','☝️ Two index fingers','☝️ 両手の人差し指'))
            self.explosion_method.Items.Add(self.tr('✋ 單手握拳／張掌','✋ Fist / open palm','✋ 片手の拳／開いた手'))
            self.explosion_method.SelectedIndex=selected
            self.space.Enabled=self.settings['mode']!='space'
            self.object.Enabled=self.settings['mode']!='object'
            self.tune(None,None)
            self.refresh_tracking_button()
            self.label.Text=self.tr('準備就緒','Ready','準備完了')

        def tune(self,s,e):
            self.tracking.strength=self.strength.Value/100.
            self.tracking.sensitivity=self.sensitivity.Value/100.
            self.settings['sensitivity']=self.tracking.sensitivity
            self.tracking.explosion_factor=self.explosion_slider.Value/100.
            self.explosion_label.Text=self.tr('🧩 爆炸比例','🧩 Explosion ratio','🧩 分解倍率')+' : '+str(round(self.tracking.explosion_factor,2))+'×'
            self.strength_label.Text=self.tr('👀 視角幅度','👀 Strength','👀 移動量')+' : '+str(self.strength.Value)+'%'
            self.sensitivity_label.Text=self.tr('🐇 靈敏度','🐇 Sensitivity','🐇 感度')+' : '+str(self.sensitivity.Value)+'%'
            self.write()

        def change_explosion_method(self,s,e):
            if self.explosion_method.SelectedIndex<0:return
            method='palm' if self.explosion_method.SelectedIndex==1 else 'two_index'
            if self.settings['explosion_method']==method:return
            self.settings['explosion_method']=method
            self.tracking.reset_explosion()
            self.settings['calibration']+=1;self.write()

        def show_help(self,s,e):
            text=self.tr(
                '開始時以目前攝影機為基準。空間模式：頭部左右、上下與遠近移動控制視角。物體模式：拇指、食指與中指抓握後移動手掌旋轉攝影機；抓握期間暫停頭部控制。雙手各伸出食指，拉開可展開爆炸圖，靠攏或放開即還原。紅球代表偵測到手，綠球代表抓握啟動。視角影響程度控制頭部與抓握的移動幅度；靈敏度越高，反應越快、平滑越少。0% 幅度會固定頭部與抓握視角。揮手功能已停用。',
                'Start captures the current camera as the baseline. Space mode: move your head sideways, vertically or closer/farther. Object mode: grasp with thumb, index and middle finger, then move your hand to orbit the camera. Head control pauses while grasping. Extend both index fingers and separate them to explode parts; bring them together or release to restore. Red means hand detected; green means grasp active. Strength adjusts head and grasp movement. Higher sensitivity responds faster with less smoothing. 0% strength fixes head and grasp movement. Waving is disabled.',
                '開始時のカメラを基準にします。空間モードでは頭の左右・上下・前後移動で視点を操作します。物体モードでは親指・人差し指・中指でつかみ、手を動かしてカメラを回転します。つかんでいる間は頭の操作を停止します。両手の人差し指を伸ばし、離すと分解表示、近づけるか解除すると元に戻ります。赤い球は手の検出、緑はつかみ操作を示します。移動量は頭と手による視点変化の大きさ、感度は反応速度を調整します。感度が高いほど平滑化が少なくなります。移動量0%で頭と手による視点移動を固定します。手を振る操作は無効です。')
            text+='\n\n'+self.tr('三指抓握時，手靠近相機可拉近，退後可拉遠；放開保留視角。','While grasping, bring your hand closer to dolly in; move it away to dolly out. Release to keep the view.','三指でつかみ、手をカメラに近づけると接近、遠ざけると後退します。解除すると視点を保持します。')
            text+='\n\n'+self.tr('爆炸控制可選雙食指或單手握拳／五指張開。單手張掌展開、握拳收回；移出鏡頭也會還原。爆炸比例 1–5 倍，1 倍為原位置。','Choose two index fingers or one-hand fist/open palm. Open all five fingers to explode; make a fist or leave the camera to restore. Ratio 1–5×; 1× is the original position.','分解操作は両手の人差し指、または片手の拳／開いた手を選べます。五指を開くと展開し、握るか手を画面から外すと復元します。倍率は1–5倍、1倍は元の位置です。')
            dialog=ui(forms.Dialog,Title=self.help_button.Text,ClientSize=drawing.Size(480,300),Resizable=True)
            label=ui(forms.Label,Text=text,Wrap=forms.WrapMode.Word)
            button=ui(forms.Button,Text=self.tr('關閉','Close','閉じる'))
            button.Click+=lambda s,e:dialog.Close()
            layout=ui(forms.DynamicLayout,Padding=drawing.Padding(18),Spacing=drawing.Size(10,10))
            layout.AddRow(label);layout.AddRow(button);dialog.Content=layout
            dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindowForDocument(Rhino.RhinoDoc.ActiveDoc) if host is not None else self)

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

        def refresh_tracking_button(self):
            if self.running and not self.settings.get('paused'):
                self.start.Text=self.tr('⏸️ 暫停追蹤','⏸️ Pause tracking','⏸️ 一時停止')
            elif self.running:
                self.start.Text=self.tr('▶️ 繼續追蹤','▶️ Resume tracking','▶️ 再開')
            else:
                self.start.Text=self.tr('▶️ 開始追蹤','▶️ Start tracking','▶️ 開始')

        def toggle_tracking(self,s,e):
            if self.running and not self.settings.get('paused'):self.pause(s,e)
            else:self.begin(s,e)
            self.refresh_tracking_button()

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
                self.timer.Stop()
                self.timer.Start()
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
                self.refresh_tracking_button()
            except Exception as error: self.label.Text=str(error)

        def pause(self,s,e):
            self.settings['paused']=True; self.write()
            self.tracking.pause()
            self.refresh_tracking_button()
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
            self.tracking.stop(True)
            self.running=False; self.camera.Enabled=True
            self.refresh_tracking_button()
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
                with open(ROOT+'/runtime/preview.jpg','rb') as response: data=response.read()
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
    if host is not None:host.Content=panel
    else:panel.Show()
    if host is None and hasattr(panel.ControlObject,'HidesOnDeactivate'):
        panel.ControlObject.HidesOnDeactivate=True
    print('裸視3D 控制面板已開啟')
