s=bpy.context.scene;s.camera.data.clip_end=5000
for o in s.objects:
    if o.name.startswith('Fuji / Forest crown'):o.location.y+=95
    if any(o.name.startswith('Fuji / '+label) for label in ['Concrete terrace','Seat','Canopy support','Roof truss','Grandstand canopy']):o.location.x-=13
for a in bpy.context.screen.areas:
    if a.type=='VIEW_3D':a.spaces.active.clip_end=5000;a.spaces.active.overlay.show_overlays=False
# Keep the saved file directly usable with the existing webcam panel.
if 'nakedeye3d' not in bpy.context.preferences.addons:bpy.ops.preferences.addon_enable(module='nakedeye3d')
s.render.filepath=str(ROOT/'blender/FujiA1-realistic-preview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/FujiA1.blend'),copy=True)
bpy.ops.render.render(write_still=True)
