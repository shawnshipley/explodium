bl_info = {
    "name": "Explodium",
    "author": "Shawn Shipley",
    "version": (1, 0, 4),
    "blender": (4, 0, 0),
    "location": "View3D > Edit Mode > N-Panel > Edit Tab",
    "description": "Preview exploded mesh",
    "category": "Mesh",
}

import bpy
import rna_keymap_ui

# Global list so we can unregister keymaps later
addon_keymaps = []


# =========================================================
#   OPERATOR
# =========================================================
class MESH_OT_explodium(bpy.types.Operator):
    """Preview exploded mesh (hold hotkey)"""
    bl_idname = "mesh.explodium"
    bl_label = "Explode Preview"
    bl_options = {'REGISTER', 'UNDO'}
    
    _timer = None
    original_mesh_data = None

    def modal(self, context, event):
        # Detect when the configured key is released
        kmi = get_keymap_item()
        if kmi and event.type == kmi.type and event.value == 'RELEASE':
            self.cancel(context)
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}

    def execute(self, context):
        obj = context.active_object
        bpy.ops.object.mode_set(mode='OBJECT')
        self.original_mesh_data = obj.data.copy()
        bpy.ops.object.mode_set(mode='EDIT')

        # Split faces for explode look
        bpy.ops.mesh.select_mode(type='EDGE')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.edge_split()
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.mesh.select_all(action='SELECT')

        # Change pivot and scale for visual explosion
        context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
        bpy.ops.transform.resize(value=(0.7, 0.7, 0.7), orient_type='LOCAL')
        context.scene.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
        bpy.ops.transform.resize(value=(1.5, 1.5, 1.5))

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


# =========================================================
#   HELPER FUNCTIONS
# =========================================================
def get_keymap_item():
    """Return the keymap item for this add-on, if any"""
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


# =========================================================
#   ADD-ON PREFERENCES
# =========================================================
class ExplodiumPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__  # Correct pattern

    def draw(self, context):
        layout = self.layout
        layout.label(text="Explodium Settings")
        layout.separator()

        wm = context.window_manager
        kc = wm.keyconfigs.user
        col = layout.column()
        col.label(text="Hotkey:")

        # Draw editable keymap just like official add-ons
        for km, kmi in addon_keymaps:
            km_user = kc.keymaps.get(km.name)
            if km_user:
                for kmi_user in km_user.keymap_items:
                    if kmi_user.idname == "mesh.explodium":
                        rna_keymap_ui.draw_kmi(
                            ["ADDON", "USER", "DEFAULT"],
                            kc,
                            km_user,
                            kmi_user,
                            col,
                            0
                        )
                        break


# =========================================================
#   N-PANEL
# =========================================================
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
        layout.label(text="Explode Preview:")
        layout.label(text=f"Hold {get_hotkey_string()}", icon='INFO')


# =========================================================
#   KEYMAP SETUP
# =========================================================
def register_keymaps():
    """Register default keymap for this add-on"""
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Mesh', space_type='EMPTY')
        kmi = km.keymap_items.new("mesh.explodium", 'P', 'PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))


def unregister_keymaps():
    """Clean up keymaps on unregister"""
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


# =========================================================
#   REGISTRATION
# =========================================================
classes = (
    MESH_OT_explodium,
    ExplodiumPreferences,
    VIEW3D_PT_explodium,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_keymaps()


def unregister():
    unregister_keymaps()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()