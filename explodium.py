bl_info = {
    "name": "Explodium",
    "author": "Shawn Shipley",
    "version": (1, 1, 1),
    "blender": (4, 0, 0),
    "location": "View3D > Edit Mode > N-Panel > Edit Tab",
    "description": "Preview exploded mesh with user-editable amount and reset button",
    "category": "Mesh",
}

import bpy
import rna_keymap_ui

# ---------------------------------------------
# Global keymap storage
# ---------------------------------------------
addon_keymaps = []


# ---------------------------------------------
# Scene Properties (user-editable scale values)
# ---------------------------------------------
class ExplodiumProperties(bpy.types.PropertyGroup):
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
        min=0.0,
        max=5.0,
    )


# ---------------------------------------------
# Operator
# ---------------------------------------------
class MESH_OT_explodium(bpy.types.Operator):
    """Preview exploded mesh (hold hotkey)"""
    bl_idname = "mesh.explodium"
    bl_label = "Explode Preview"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None
    original_mesh_data = None

    def modal(self, context, event):
        kmi = get_keymap_item()
        if kmi and event.type == kmi.type and event.value == 'RELEASE':
            self.cancel(context)
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}

    def execute(self, context):
        props = context.scene.explodium_props
        shrink = props.shrink_factor
        expand = props.expand_factor

        obj = context.active_object
        bpy.ops.object.mode_set(mode='OBJECT')
        self.original_mesh_data = obj.data.copy()
        bpy.ops.object.mode_set(mode='EDIT')

        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.edge_split()
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='SELECT')

        # Step 1: Shrink each face
        context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
        bpy.ops.transform.resize(value=(shrink, shrink, shrink), orient_type='LOCAL')

        # Step 2: Expand the entire mesh
        context.scene.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
        bpy.ops.transform.resize(value=(expand, expand, expand))

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        obj = context.active_object
        bpy.ops.object.mode_set(mode='OBJECT')
        old_mesh = obj.data
        obj.data = self.original_mesh_data
        bpy.data.meshes.remove(old_mesh)
        bpy.ops.object.mode_set(mode='EDIT')

        wm = context.window_manager
        wm.event_timer_remove(self._timer)


# ---------------------------------------------
# Helper Functions
# ---------------------------------------------
def get_keymap_item():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.user
    km = kc.keymaps.get('Mesh')
    if km:
        for kmi in km.keymap_items:
            if kmi.idname == "mesh.explodium":
                return kmi
    return None


def get_hotkey_string():
    kmi = get_keymap_item()
    if not kmi:
        return "Not Set"
    parts = []
    if kmi.ctrl: parts.append("Ctrl")
    if kmi.shift: parts.append("Shift")
    if kmi.alt: parts.append("Alt")
    if kmi.oskey:
        parts.append("Cmd" if bpy.app.build_platform == 'DARWIN' else "Win")
    parts.append(kmi.type)
    return "+".join(parts)


# ---------------------------------------------
# Add-on Preferences
# ---------------------------------------------
class ExplodiumPreferences(bpy.types.AddonPreferences):
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
            if km_user:
                for kmi_user in km_user.keymap_items:
                    if kmi_user.idname == "mesh.explodium":
                        rna_keymap_ui.draw_kmi(
                            ["ADDON", "USER", "DEFAULT"],
                            kc, km_user, kmi_user, col, 0
                        )
                        break


# ---------------------------------------------
# Restore Defaults Operator
# ---------------------------------------------
class EXPLODIUM_OT_restore_defaults(bpy.types.Operator):
    """Restore default shrink/expand values"""
    bl_idname = "explodium.restore_defaults"
    bl_label = "Restore Default Values"

    def execute(self, context):
        props = context.scene.explodium_props
        props.shrink_factor = 0.7
        props.expand_factor = 1.5
        self.report({'INFO'}, "Explodium values restored to defaults")
        return {'FINISHED'}


# ---------------------------------------------
# N-Panel
# ---------------------------------------------
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

        layout.label(text="Explode Preview:")
        layout.label(text=f"Hold {get_hotkey_string()}", icon='INFO')

        layout.separator()
        layout.label(text="Adjust Explosion Amount:")
        layout.prop(props, "shrink_factor")
        layout.prop(props, "expand_factor")
        layout.operator("explodium.restore_defaults", icon="FILE_REFRESH")


# ---------------------------------------------
# Keymap Registration
# ---------------------------------------------
def register_keymaps():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Mesh', space_type='EMPTY')
        kmi = km.keymap_items.new("mesh.explodium", 'P', 'PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))


def unregister_keymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


# ---------------------------------------------
# Registration
# ---------------------------------------------
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