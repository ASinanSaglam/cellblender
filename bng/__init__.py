import bpy
from . import bng_operators
from . import bng_panels


def menu_func_import(self, context):
    self.layout.operator("bng.import_data", text="BNG Model (.bngl)")
    
def register():
    bpy.types.INFO_MT_file_import.append(menu_func_import)

def unregister():
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    
register()

