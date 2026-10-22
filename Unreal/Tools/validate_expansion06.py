"""Reload final 05, inspect scenic placements, run quest route, capture UE overview."""
import unreal as u
import runpy,json,time,traceback,hashlib
from pathlib import Path
root=Path(u.Paths.project_dir()).resolve().parent
ed=u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert not ed.get_game_world() and not u.EditorLoadingAndSavingUtils.get_dirty_map_packages()
u.EditorPythonScripting.set_keep_python_script_alive(True)
u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/TownLayout_06')
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
checks={'actor_count':len(actors)==3945,'three_herbs':len([a for a in actors if a.actor_has_tag('QuestHerb')])==3}
for a in actors:
 name=a.get_actor_label()
 if name.startswith(('ValleyRidge_','DistantPeak_')):
  r=a.get_actor_rotation();checks[name+'_upright']=abs(r.pitch)<.01 and abs(r.roll)<.01
 if a.actor_has_tag('DriftCloud'):
  c,e=a.get_actor_bounds(False);checks[name+'_above_route']=c.z-e.z>2500
  checks[name+'_no_shadows']=not a.static_mesh_component.get_editor_property('cast_shadow')
checks['one_board']=len([a for a in actors if a.actor_has_tag('QuestBoard')])==1
board=next(a for a in actors if a.actor_has_tag('QuestBoard'))
checks['board_position']=(board.get_actor_location()-u.Vector(260,-3450,132)).length()<.1
checks['new_asset_instances']=len([a for a in actors if str(a.get_folder_path())=='Expansion06'])==35
palette=json.loads((root/'expansion06_palette.json').read_text())
for name,data in palette['sources'].items():
 mesh=u.load_asset('/Game/Art/Expansion06/Meshes/'+name)
 checks[name+'_loaded']=isinstance(mesh,u.StaticMesh)
 if mesh:
  checks[name+'_materials']=all(x.material_interface and x.material_interface.get_path_name().startswith('/Game/Art/Expansion06/') for x in mesh.static_materials)
  box=mesh.get_bounding_box()
  actual=sorted([box.max.x-box.min.x,box.max.y-box.min.y])+[box.max.z-box.min.z]
  bounds=data['bounds_m'];expected=sorted([(bounds[1][i]-bounds[0][i])*100 for i in [0,1]])+[(bounds[1][2]-bounds[0][2])*100]
  checks[name+'_scale']=all(abs(a-b)<max(3,b*.04) for a,b in zip(actual,expected))
assert all(checks.values()),checks
report={'status':'running_route','map':'/Game/Maps/TownLayout_06','saved_checks':checks,'screenshots':[]}
def write():(root/'expansion06_validation.json').write_text(json.dumps(report,indent=2))
state={'phase':'route','start':time.monotonic()}
perf=u.get_default_object(u.load_class(None,'/Script/UnrealEd.EditorPerformanceSettings'))
old=perf.get_editor_property('bThrottleCPUWhenNotForeground')
shots=[('expansion06_reststop',(-2400,-2950,1300),(-1050,-4450,420)),('expansion06_trail',(1300,-3400,1000),(-600,-4900,380)),('expansion06_board',(-240,-3020,420),(260,-3450,290)),('expansion06_pavilion_inside',(-960,-4450,310),(-1350,-4450,320))]
def done():
 perf.set_editor_property('bThrottleCPUWhenNotForeground',old)
 u.unregister_slate_post_tick_callback(final05_handle)
def tick(dt):
 try:
  now=time.monotonic()
  if now-state['start']>400:raise RuntimeError('Final validation timeout')
  if state['phase']=='route':
   r=json.loads((root/'expansion06_runtime.json').read_text())
   if r['status']!='running' and not ed.get_game_world():
    assert r['status']=='passed',r
    perf.set_editor_property('bThrottleCPUWhenNotForeground',False)
    state.update(phase='view',index=0)
  elif state['phase']=='view':
   name,loc,target=shots[state['index']];v=u.Vector(*loc)
   ed.set_level_viewport_camera_info(v,u.MathLibrary.find_look_at_rotation(v,u.Vector(*target)))
   state.update(phase='capture',t=now)
  elif state['phase']=='capture' and now-state['t']>3:
   name=shots[state['index']][0];path=str(root/'Validation'/(name+'.png'))
   # Set phase first: screenshot rendering may re-enter Slate callbacks.
   report['screenshots'].append(path);state.update(phase='next',t=now)
   u.AutomationLibrary.take_high_res_screenshot(1600,1000,path)
  elif state['phase']=='next' and now-state['t']>4:
   if state['index']+1<len(shots):state.update(index=state['index']+1,phase='view')
   else:
    report.update(status='runtime_passed_captures_pending_review',map_sha256=hashlib.sha256((root/'XiuXianTown/Content/Maps/TownLayout_06.umap').read_bytes()).hexdigest());write();done()
 except Exception:
  report.update(status='error',error=traceback.format_exc());write();done()
runpy.run_path(str(root/'Tools/test_expansion06.py'))
write()
final05_handle=u.register_slate_post_tick_callback(tick)
