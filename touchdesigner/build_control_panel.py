b=op('/project1/cyber_apple')
if b.op('control_panel'):b.op('control_panel').destroy()
ui=b.create(containerCOMP,'control_panel');ui.par.w=440;ui.par.h=400
items=[('Start','開始 / 繼續'),('Pause','暫停'),('Stop','停止並恢復'),('Calibrate','目前視角校正'),('Space','空間模式'),('Object','物體模式')]
for i,(name,label) in enumerate(items):
    button=ui.create(buttonCOMP,name.lower()+'_button');button.store('action',name);button.par.label=label;button.par.buttontype='momentary';button.par.w=200;button.par.h=42;button.par.x=12+(i%2)*216;button.par.y=340-(i//2)*52
    event=button.create(panelexecuteDAT,'click');event.par.panels=button;event.par.panelvalue='select';event.par.offtoon=True
    event.text="""def onOffToOn(panelValue):
    b=me.parent(3);name=me.parent().fetch('action')
    if name=='Space':b.par.Viewingmode='space'
    elif name=='Object':b.par.Viewingmode='object'
    else:getattr(b.par,name).pulse()
"""
preview=ui.create(containerCOMP,'webcam');preview.par.x=12;preview.par.y=38;preview.par.w=224;preview.par.h=168;preview.par.top=b.op('tracking_preview')
status=ui.create(textCOMP,'status');status.par.x=12;status.par.y=8;status.par.w=416;status.par.h=28;status.par.text.expr="parent(2).par.Status.eval()"
mode=ui.create(textCOMP,'mode');mode.par.x=250;mode.par.y=155;mode.par.w=176;mode.par.h=36;mode.par.text.expr="'空間模式' if parent(2).par.Viewingmode.eval()=='space' else '物體模式'"
for i,label in enumerate(['三指抓握：旋轉','雙食指：爆炸圖','先停止其他追蹤']):
    help=ui.create(textCOMP,'help'+str(i));help.par.x=250;help.par.y=122-i*34;help.par.w=176;help.par.h=28;help.par.text=label
startup=b.op('open_controls') or b.create(executeDAT,'open_controls');startup.par.start=True
startup.text="""def onStart():
    parent().par.Tracking=False
    parent().op('control_panel').openViewer()
"""
if not globals().get('SKIP_SAVE',False):ui.openViewer()
print('Created native control panel',ui.path)
