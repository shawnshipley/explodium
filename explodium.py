import bpy
from bpy import context

# Main operator
class MESH_OT_explodium(bpy.types.Operator):
    """Preview exploded mesh (hold Ctrl+Shift+P)"""
    bl_idname = "mesh.explodium"
    bl_label = "Explode Preview"
    bl_options = {'REGISTER', 'UNDO'}
    
    original_mesh: bpy.props.IntProperty()
    _timer = None
    
    def modal(self, context, event):
        if event.type == 'P' and event.value == 'RELEASE':
            # Key released - restore original state
            self.cancel(context)
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        # Store original mesh
        obj = context.active_object
        bpy.ops.object.mode_set(mode='OBJECT')
        self.original_mesh_data = obj.data.copy()
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Switch to edge select mode
        bpy.ops.mesh.select_mode(type='EDGE')
        
        # Select all edges
        bpy.ops.mesh.select_all(action='SELECT')
        
        # Split faces by edges (this is the correct operator)
        bpy.ops.mesh.edge_split()
        
        # Switch to face select mode
        bpy.ops.mesh.select_mode(type='FACE')
        
        # Select all
        bpy.ops.mesh.select_all(action='SELECT')
        
        # Change pivot to Individual Origins
        context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'
        
        # Scale down 10% to create separation (shrink each face from its own center)
        bpy.ops.transform.resize(value=(0.7, 0.7, 0.7), orient_type='LOCAL')
        
        # Change pivot to Median Point
        context.scene.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
        
        # Scale up 50% (scale the whole exploded mesh)
        bpy.ops.transform.resize(value=(1.5, 1.5, 1.5))
        
        # Set up modal handler
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        # Restore original mesh
        obj = context.active_object
        bpy.ops.object.mode_set(mode='OBJECT')
        old_mesh = obj.data
        obj.data = self.original_mesh_data
        bpy.data.meshes.remove(old_mesh)
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Remove timer
        wm = context.window_manager
        wm.event_timer_remove(self._timer)

# Keymap
addon_keymaps = []

def register():
    bpy.utils.register_class(MESH_OT_explodium)
    
    # Add keymap
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Mesh', space_type='EMPTY')
        kmi = km.keymap_items.new(MESH_OT_explodium.bl_idname, 'P', 'PRESS', ctrl=True, shift=True)
        addon_keymaps.append((km, kmi))

def unregister():
    # Remove keymap
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    
    bpy.utils.unregister_class(MESH_OT_explodium)

if __name__ == "__main__":
    register()