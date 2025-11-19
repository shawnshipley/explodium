bl_info = {
    "name": "Explodium",
    "author": "Shawn Shipley",
    "version": (1, 0, 5),
    "blender": (4, 2, 0),
    "location": "View3D > Edit Mode > N-Panel > Edit Tab",
    "description": "Shows an exploded view of your mesh",
    "category": "Mesh",
}

import bpy
import rna_keymap_ui

# =============================================================
# GLOBALS
# =============================================================

addon_keymaps = []


# =============================================================
# SCENE PROPERTIES
# =============================================================

class ExplodiumProperties(bpy.types.PropertyGroup):
    """Custom scene properties for Explodium"""

    shrink_factor: bpy.props.FloatProperty(
        name="Shrink Faces",
        description="Shrink each face individually",
        default=0.7,
        min=0.0,
        max=1.0,
    )

    expand_factor: bpy.props.FloatProperty(
        name="Expand Mesh",
        description="Overall expansion of exploded mesh",
        default=1.5,
        min=1.0,
        max=10.0,
    )


# =============================================================
# OPERATOR: Explode Mesh Preview
# =============================================================

class MESH_OT_explodium(bpy.types.Operator):
    """Preview exploded mesh while holding hotkey"""
    bl_idname = "mesh.explodium"
    bl_label = "Exploded Preview"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None
    _original_mesh_data = None

    def modal(self, context, event):
        kmi = get_keymap_item()
        if kmi and event.type == kmi.type and event.value == 'RELEASE':
            self.cancel(context)
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}

    def execute(self, context):
        props = context.scene.explodium_props
        obj = context.active_object

        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "Active object must be a mesh")
            return {'CANCELLED'}

        if obj.mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except RuntimeError:
                self.report({'WARNING'}, "Cannot switch object mode")
                return {'CANCELLED'}

        # Copy original mesh for restoration
        self._original_mesh_data = obj.data.copy()

        try:
            bpy.ops.object.mode_set(mode='EDIT')
        except RuntimeError:
            # Clean up if mode switch fails
            if self._original_mesh_data:
                bpy.data.meshes.remove(self._original_mesh_data)
                self._original_mesh_data = None
            self.report({'WARNING'}, "Cannot switch to edit mode")
            return {'CANCELLED'}

        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.edge_split()
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='SELECT')

        # Step 1: Shrink each face
        context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
        s = props.shrink_factor
        bpy.ops.transform.resize(value=(s, s, s), orient_type='LOCAL')

        # Step 2: Expand the entire mesh
        context.scene.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
        e = props.expand_factor
        bpy.ops.transform.resize(value=(e, e, e))

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        
        try:
            wm.modal_handler_add(self)
        except:
            wm.event_timer_remove(self._timer)
            self._timer = None
            self.cancel(context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)
            self._timer = None
        
        obj = context.active_object
        if not obj or not self._original_mesh_data:
            return

        if obj.mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except RuntimeError:
                pass

        old_mesh = obj.data
        obj.data = self._original_mesh_data
        bpy.data.meshes.remove(old_mesh)
        self._original_mesh_data = None

        try:
            bpy.ops.object.mode_set(mode='EDIT')
        except RuntimeError:
            pass

    def __del__(self):
        if self._original_mesh_data and self._original_mesh_data.users == 0:
            bpy.data.meshes.remove(self._original_mesh_data)


# =============================================================
# HELPERS
# =============================================================

def get_keymap_item():
    """Find the registered keymap item for Explodium"""
    wm = bpy.context.window_manager
    kc = getattr(wm.keyconfigs, "user", None)
    if not kc:
        return None

    km = kc.keymaps.get('Mesh')
    if not km:
        return None

    for kmi in km.keymap_items:
        if kmi.idname == "mesh.explodium":
            return kmi
    return None


def get_hotkey_string():
    """Return a formatted string representing the active hotkey"""
    kmi = get_keymap_item()
    if not kmi:
        return "Not Set"

    parts = []
    if kmi.ctrl:
        parts.append("Ctrl")
    if kmi.shift:
        parts.append("Shift")
    if kmi.alt:
        parts.append("Alt")
    if kmi.oskey:
        parts.append("Cmd" if bpy.app.build_platform == 'DARWIN' else "Win")
    parts.append(kmi.type)

    return "+".join(parts)


# =============================================================
# ADD-ON PREFERENCES
# =============================================================

class ExplodiumPreferences(bpy.types.AddonPreferences):
    """Preferences panel for keymap customization"""
    bl_idname = __package__

    def draw(self, context):
        layout = self.layout
        layout.label(text="Explodium Settings")
        layout.separator()

        wm = context.window_manager
        kc = wm.keyconfigs.user
        col = layout.column()
        col.label(text="Hotkey:")

        for km, kmi in addon_keymaps:
            km_user = kc.keymaps.get(km.name)
            if not km_user:
                continue
            for kmi_user in km_user.keymap_items:
                if kmi_user.idname == "mesh.explodium":
                    rna_keymap_ui.draw_kmi(
                        ["ADDON", "USER", "DEFAULT"],
                        kc, km_user, kmi_user, col, 0
                    )
                    break
            else:
                continue
            break


# =============================================================
# OPERATOR: Restore Defaults
# =============================================================

class EXPLODIUM_OT_restore_defaults(bpy.types.Operator):
    """Restore default shrink and expand values"""
    bl_idname = "explodium.restore_defaults"
    bl_label = "Restore Defaults"

    def execute(self, context):
        props = context.scene.explodium_props
        props.shrink_factor = 0.7
        props.expand_factor = 1.5
        self.report({'INFO'}, "Explodium values restored to defaults")

        if context.area:
            context.area.tag_redraw()

        return {'FINISHED'}


# =============================================================
# UI PANEL
# =============================================================

class VIEW3D_PT_explodium(bpy.types.Panel):
    """Explodium panel in the N-Panel Edit tab"""
    bl_label = "Explodium"
    bl_idname = "VIEW3D_PT_explodium"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Edit'
    bl_context = "mesh_edit"

    def draw(self, context):
        layout = self.layout
        props = context.scene.explodium_props

        layout.label(text="Exploded Preview:")
        layout.label(text=f"Hold {get_hotkey_string()}", icon='INFO')

        layout.separator()
        layout.label(text="Adjust Explosion Amount:")
        layout.prop(props, "shrink_factor")
        layout.prop(props, "expand_factor")
        layout.operator("explodium.restore_defaults", icon="FILE_REFRESH")


# =============================================================
# KEYMAP REGISTRATION
# =============================================================

def register_keymaps():
    """Register hotkeys for Explodium"""
    try:
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.addon

        if kc:
            km = kc.keymaps.new(name='Mesh', space_type='EMPTY')
            kmi = km.keymap_items.new("mesh.explodium", 'P', 'PRESS', ctrl=True, shift=True)
            addon_keymaps.append((km, kmi))
    except:
        pass


def unregister_keymaps():
    """Unregister addon keymaps"""
    for km, kmi in addon_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except:
            pass
    addon_keymaps.clear()


# =============================================================
# REGISTRATION
# =============================================================

classes = (
    ExplodiumProperties,
    MESH_OT_explodium,
    ExplodiumPreferences,
    EXPLODIUM_OT_restore_defaults,
    VIEW3D_PT_explodium,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.explodium_props = bpy.props.PointerProperty(type=ExplodiumProperties)
    register_keymaps()


def unregister():
    unregister_keymaps()
    del bpy.types.Scene.explodium_props

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()