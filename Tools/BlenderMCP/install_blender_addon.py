"""Install the pinned bundled add-on and preserve existing Blender preferences."""
import bpy
import addon_utils
import shutil
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parent
source = root / '.venv/lib/python3.14/site-packages/blender_mcp/bundled/addon.py'
folder = Path(bpy.utils.user_resource('SCRIPTS', path='addons', create=True))
target = folder / 'blender_mcp.py'
stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
prefs = Path(bpy.utils.user_resource('CONFIG')) / 'userpref.blend'
for old in (target, prefs):
    if old.exists():
        shutil.copy2(old, old.with_name(old.name + '.' + stamp + '.bak'))
shutil.copy2(source, target)
bpy.utils.refresh_script_paths()
addon_utils.modules_refresh()
addon_utils.enable('blender_mcp', default_set=True, persistent=True)
assert 'blender_mcp' in bpy.context.preferences.addons, 'Add-on did not enable'
bpy.context.preferences.addons['blender_mcp'].preferences.telemetry_consent = False
bpy.ops.wm.save_userpref()
print('BLENDER_MCP_INSTALLED', bpy.app.version_string, str(target))
