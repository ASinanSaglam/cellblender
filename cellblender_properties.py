# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


# ############
#
#  Property Groups
#   CellBlender consists primarily of Property Groups which are the
#   classes which are templates for objects.
#
#   Each Property Group must implement the following functions:
#
#     init_properties - Deletes old and Creates a new object including children
#     build_data_model_from_properties - Builds a Data Model Dictionary from the existing properties
#     @staticmethod upgrade_data_model - Produces a current data model from an older version
#     build_properties_from_data_model - Calls init_properties and builds properties from a data model
#     check_properties_after_building - Used to resolve dependencies
#     
#
# ############


# <pep8 compliant>


"""
This script contains the custom properties used in CellBlender.
"""
# blender imports
import bpy
from . import cellblender_operators
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, \
    FloatProperty, FloatVectorProperty, IntProperty, IntVectorProperty, PointerProperty, StringProperty, BoolVectorProperty

from bpy.app.handlers import persistent

from . import cellblender_preferences
from . import cellblender_initialization
from . import cellblender_molecules
from . import cellblender_reactions
from . import cellblender_release
from . import cellblender_surface_classes
from . import cellblender_partitions
from . import cellblender_reaction_output
from . import parameter_system
from . import data_model

# python imports
import os
from multiprocessing import cpu_count

from cellblender.cellblender_utils import project_files_path

# we use per module class registration/unregistration
def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)


#Custom Properties

class MCellStringProperty(bpy.types.PropertyGroup):
    """ Generic PropertyGroup to hold string for a CollectionProperty """
    name = StringProperty(name="Text")
    def remove_properties ( self, context ):
        #print ( "Removing an MCell String Property with name \"" + self.name + "\" ... no collections to remove." )
        pass


class MCellFloatVectorProperty(bpy.types.PropertyGroup):
    """ Generic PropertyGroup to hold float vector for a CollectionProperty """
    vec = bpy.props.FloatVectorProperty(name="Float Vector")
    def remove_properties ( self, context ):
        #print ( "Removing an MCell Float Vector Property... no collections to remove. Is there anything special do to for Vectors?" )
        pass




class MCellModSurfRegionsProperty(bpy.types.PropertyGroup):
    """ Assign a surface class to a surface region. """

    name = StringProperty(name="Assign Surface Class")
    surf_class_name = StringProperty(
        name="Surface Class Name",
        description="This surface class will be assigned to the surface "
                    "region listed below.",
        update=cellblender_operators.check_active_mod_surf_regions)
    object_name = StringProperty(
        name="Object Name",
        description="A region on this object will have the above surface "
                    "class assigned to it.",
        update=cellblender_operators.check_active_mod_surf_regions)
    region_name = StringProperty(
        name="Region Name",
        description="This surface region will have the above surface class "
                    "assigned to it.",
        update=cellblender_operators.check_active_mod_surf_regions)
    status = StringProperty(name="Status")

    def remove_properties ( self, context ):
        print ( "Removing all Surface Regions Properties... no collections to remove." )

    def build_data_model_from_properties ( self, context ):
        print ( "Surface Region building Data Model" )
        sr_dm = {}
        sr_dm['data_model_version'] = "DM_2014_10_24_1638"
        sr_dm['name'] = self.name
        sr_dm['surf_class_name'] = self.surf_class_name
        sr_dm['object_name'] = self.object_name
        sr_dm['region_name'] = self.region_name
        return sr_dm


    @staticmethod
    def upgrade_data_model ( dm ):
        # Upgrade the data model as needed. Return updated data model or None if it can't be upgraded.
        print ( "------------------------->>> Upgrading MCellModSurfRegionsProperty Data Model" )
        if not ('data_model_version' in dm):
            # Make changes to move from unversioned to DM_2014_10_24_1638
            dm['data_model_version'] = "DM_2014_10_24_1638"

        if dm['data_model_version'] != "DM_2014_10_24_1638":
            data_model.flag_incompatible_data_model ( "Error: Unable to upgrade MCellModSurfRegionsProperty data model to current version." )
            return None

        return dm


    def build_properties_from_data_model ( self, context, dm ):

        # Check that the data model version matches the version for this property group
        if dm['data_model_version'] != "DM_2014_10_24_1638":
            data_model.handle_incompatible_data_model ( "Error: Unable to upgrade MCellModSurfRegionsProperty data model to current version." )

        self.name = dm["name"]
        self.surf_class_name = dm["surf_class_name"]
        self.object_name = dm["object_name"]
        self.region_name = dm["region_name"]

    def check_properties_after_building ( self, context ):
        print ( "Implementing check_properties_after_building for " + str(self) )
        print ( "Calling check_mod_surf_regions on object named: " + self.object_name )
        cellblender_operators.check_mod_surf_regions(self, context)
        




#class MCellScratchPropertyGroup(bpy.types.PropertyGroup):
#    show_all_icons = BoolProperty(
#        name="Show All Icons",
#        description="Show all Blender icons and their names",
#        default=False)
#    print_all_icons = BoolProperty(
#        name="Print All Icon Names",
#        description="Print all Blender icon names (helpful for searching)",
#        default=False)


class MCellProjectPropertyGroup(bpy.types.PropertyGroup):
    base_name = StringProperty(
        name="Project Base Name", default="cellblender_project")

    status = StringProperty(name="Status")

    def draw_layout (self, context, layout):
        mcell = context.scene.mcell

        if not mcell.initialized:
            mcell.draw_uninitialized ( layout )
        else:

            row = layout.row()
            split = row.split(0.96)
            col = split.column()
            col.label(text="CellBlender ID: "+cellblender.cellblender_info['cellblender_source_sha1'])
            col = split.column()
            col.prop ( mcell, "refresh_source_id", icon='FILE_REFRESH', text="" )
            if 'cellblender_source_id_from_file' in cellblender.cellblender_info:
                # This means that the source ID didn't match the refreshed version
                # Draw a second line showing the original file ID as an error
                row = layout.row()
                row.label("File ID: " + cellblender.cellblender_info['cellblender_source_id_from_file'], icon='ERROR')

            # if not mcell.versions_match:
            if not cellblender.cellblender_info['versions_match']:
                # Version in Blend file does not match Addon, so give user a button to upgrade if desired
                row = layout.row()
                row.label ( "Blend File version doesn't match CellBlender version", icon='ERROR' )

                row = layout.row()
                row.operator ( "mcell.upgrade", text="Upgrade Blend File to Current Version", icon='RADIO' )
                #row = layout.row()
                #row.operator ( "mcell.delete", text="Delete CellBlender Collection Properties", icon='RADIO' )

                row = layout.row()
                row.label ( "Note: Saving this file will FORCE an upgrade!!!", icon='ERROR' )

            row = layout.row()
            if not bpy.data.filepath:
                row.label(
                    text="No Project Directory: Use File/Save or File/SaveAs",
                    icon='UNPINNED')
            else:
                row.label(
                    text="Project Directory: " + os.path.dirname(bpy.data.filepath),
                    icon='FILE_TICK')

            row = layout.row()
            layout.prop(context.scene, "name", text="Project Base Name")

    def remove_properties ( self, context ):
        print ( "Removing all Preferences Properties... no collections to remove." )

    def draw_panel ( self, context, panel ):
        """ Create a layout from the panel and draw into it """
        layout = panel.layout
        self.draw_layout ( context, layout )


class MCellExportProjectPropertyGroup(bpy.types.PropertyGroup):
    export_format_enum = [
        ('mcell_mdl_unified', "Single Unified MCell MDL File", ""),
        ('mcell_mdl_modular', "Modular MCell MDL Files", "")]
    export_format = EnumProperty(items=export_format_enum,
                                 name="Export Format",
                                 default='mcell_mdl_modular')

    def remove_properties ( self, context ):
        print ( "Removing all Export Project Properties... no collections to remove." )


class MCellRunSimulationProcessesProperty(bpy.types.PropertyGroup):
    name = StringProperty(name="Simulation Runner Process")
    #pid = IntProperty(name="PID")

    def remove_properties ( self, context ):
        print ( "Removing all Run Simulation Process Properties for " + self.name + "... no collections to remove." )

    def build_data_model_from_properties ( self, context ):
        print ( "MCellRunSimulationProcesses building Data Model" )
        dm = {}
        dm['data_model_version'] = "DM_2015_04_23_1753"
        dm['name'] = self.name
        return dm


    @staticmethod
    def upgrade_data_model ( dm ):
        # Upgrade the data model as needed. Return updated data model or None if it can't be upgraded.
        print ( "------------------------->>> Upgrading MCellRunSimulationProcessesProperty Data Model" )
        if not ('data_model_version' in dm):
            # Make changes to move from unversioned to DM_2015_04_23_1753
            dm['data_model_version'] = "DM_2015_04_23_1753"

        if dm['data_model_version'] != "DM_2015_04_23_1753":
            data_model.flag_incompatible_data_model ( "Error: Unable to upgrade MCellRunSimulationProcessesProperty data model to current version." )
            return None

        return dm


    def build_properties_from_data_model ( self, context, dm ):
        # Check that the data model version matches the version for this property group
        if dm['data_model_version'] != "DM_2015_04_23_1753":
            data_model.handle_incompatible_data_model ( "Error: Unable to upgrade MCellRunSimulationProcessesProperty data model to current version." )
        self.name = dm["name"]


def sim_runner_changed_callback ( self, context ):
    """ The run lists are somewhat incompatible between sim runners, so just clear them when switching. """
    # print ( "Sim Runner has been changed!!" )
    # mcell = context.scene.mcell
    bpy.ops.mcell.clear_run_list()
    bpy.ops.mcell.clear_simulation_queue()
    

class MCellRunSimulationPropertyGroup(bpy.types.PropertyGroup):
    start_seed = IntProperty(
        name="Start Seed", default=1, min=1,
        description="The starting value of the random number generator seed",
        update=cellblender_operators.check_start_seed)
    end_seed = IntProperty(
        name="End Seed", default=1, min=1,
        description="The ending value of the random number generator seed",
        update=cellblender_operators.check_end_seed)
    mcell_processes = IntProperty(
        name="Number of Processes",
        default=cpu_count(),
        min=1,
        max=cpu_count(),
        description="Number of simultaneous MCell processes")
    log_file_enum = [
        ('none', "Do not Generate", ""),
        ('file', "Send to File", ""),
        ('console', "Send to Console", "")]
    log_file = EnumProperty(
        items=log_file_enum, name="Output Log", default='console',
        description="Where to send MCell log output")
    error_file_enum = [
        ('none', "Do not Generate", ""),
        ('file', "Send to File", ""),
        ('console', "Send to Console", "")]
    error_file = EnumProperty(
        items=error_file_enum, name="Error Log", default='console',
        description="Where to send MCell error output")
    remove_append_enum = [
        ('remove', "Remove Previous Data", ""),
        ('append', "Append to Previous Data", "")]
    remove_append = EnumProperty(
        items=remove_append_enum, name="Previous Simulation Data",
        default='remove',
        description="Remove or append to existing rxn/viz data from previous"
                    " simulations before running new simulations.")
    processes_list = CollectionProperty(
        type=MCellRunSimulationProcessesProperty,
        name="Simulation Runner Processes")
    active_process_index = IntProperty(
        name="Active Simulation Runner Process Index", default=0)
    status = StringProperty(name="Status")
    error_list = CollectionProperty(
        type=MCellStringProperty,
        name="Error List")
    active_err_index = IntProperty(
        name="Active Error Index", default=0)


    show_output_options = BoolProperty ( name='Output Options', default=False )


    simulation_run_control_enum = [
        ('COMMAND', "Command Line", ""),
        ('JAVA', "Java Control", ""),
        ('OPENGL', "OpenGL Control", ""),
        ('QUEUE', "Queue Control", "")]
    simulation_run_control = EnumProperty(
        items=simulation_run_control_enum, name="",
        description="Mechanism for running and controlling the simulation",
        default='QUEUE', update=sim_runner_changed_callback)


    def remove_properties ( self, context ):
        print ( "Removing all Run Simulation Properties..." )
        for item in self.processes_list:
            item.remove_properties(context)
        self.processes_list.clear()
        self.active_process_index = 0
        for item in self.error_list:
            item.remove_properties(context)
        self.error_list.clear()
        self.active_err_index = 0
        print ( "Done removing all Run Simulation Properties." )

    def build_data_model_from_properties ( self, context ):
        print ( "MCellRunSimulationPropertyGroup building Data Model" )
        dm = {}
        dm['data_model_version'] = "DM_2015_04_23_1753"
        dm['name'] = self.name
        p_list = []
        for p in self.processes_list:
            p_list.append ( p.build_data_model_from_properties(context) )
        dm['processes_list'] = p_list
        return dm


    @staticmethod
    def upgrade_data_model ( dm ):
        # Upgrade the data model as needed. Return updated data model or None if it can't be upgraded.
        print ( "------------------------->>> Upgrading MCellRunSimulationPropertyGroup Data Model" )
        if not ('data_model_version' in dm):
            # Make changes to move from unversioned to DM_2015_04_23_1753
            dm['data_model_version'] = "DM_2015_04_23_1753"

        if dm['data_model_version'] != "DM_2015_04_23_1753":
            data_model.flag_incompatible_data_model ( "Error: Unable to upgrade MCellRunSimulationPropertyGroup data model to current version." )
            return None
        return dm


    def build_properties_from_data_model ( self, context, dm ):

        if dm['data_model_version'] != "DM_2015_04_23_1753":
            data_model.handle_incompatible_data_model ( "Error: Unable to upgrade MCellRunSimulationPropertyGroup data model to current version." )

        self.name = dm["name"]
        self.processes_list.clear()
        for p in dm['processes_list']:
            self.processes_list.add()
            self.active_process_index = len(self.processes_list) - 1
            self.processes_list[self.active_process_index].build_properties_from_data_model(context, p)



    def draw_layout_queue(self, context, layout):
        mcell = context.scene.mcell

        if not mcell.initialized:
            mcell.draw_uninitialized ( layout )
        else:
            ps = mcell.parameter_system

            # Filter or replace problem characters (like space, ...)
            scene_name = context.scene.name.replace(" ", "_")

            # Set this for now to have it hopefully propagate until base_name can
            # be removed
            #mcell.project_settings.base_name = scene_name

            main_mdl = project_files_path()
            main_mdl = os.path.join(main_mdl, scene_name + ".main.mdl")

            row = layout.row()

            # Only allow the simulation to be run if both an MCell binary and a
            # project dir have been selected. There also needs to be a main mdl
            # file present.
            if not mcell.cellblender_preferences.mcell_binary:
                row.label(text="Set an MCell binary in CellBlender - Preferences Panel", icon='ERROR')
            elif not os.path.dirname(bpy.data.filepath):
                row.label(
                    text="Open or save a .blend file to set the project directory",
                    icon='ERROR')
            elif (not os.path.isfile(main_mdl) and
                    mcell.cellblender_preferences.decouple_export_run):
                row.label(text="Export the project", icon='ERROR')
                row = layout.row()
                row.operator(
                    "mcell.export_project",
                    text="Export CellBlender Project", icon='EXPORT')
            else:

                row = layout.row(align=True)
                if mcell.cellblender_preferences.decouple_export_run:
                    row.operator(
                        "mcell.export_project", text="Export CellBlender Project",
                        icon='EXPORT')
                row.operator("mcell.run_simulation", text="Run",
                             icon='COLOR_RED')
                
                if self.simulation_run_control != "QUEUE":
                    if self.processes_list and (len(self.processes_list) > 0):
                        row = layout.row()
                        row.template_list("MCELL_UL_run_simulation", "run_simulation",
                                          self, "processes_list",
                                          self, "active_process_index",
                                          rows=2)
                        row = layout.row()
                        row.operator("mcell.clear_run_list")

                else:

                    if (self.processes_list and
                            cellblender.simulation_queue.task_dict):
                        row = layout.row()
                        row.label(text="MCell Processes:",
                                  icon='FORCE_LENNARDJONES')
                        row = layout.row()
                        row.template_list("MCELL_UL_run_simulation_queue", "run_simulation_queue",
                                          self, "processes_list",
                                          self, "active_process_index",
                                          rows=2)
                        row = layout.row()
                        row.operator("mcell.clear_simulation_queue")
                        row = layout.row()
                        row.operator("mcell.kill_simulation")
                        row.operator("mcell.kill_all_simulations")


                box = layout.box()

                if self.show_output_options:
                    row = box.row(align=True)
                    row.alignment = 'LEFT'
                    row.prop(self, "show_output_options", icon='TRIA_DOWN',
                             text="Output / Control Options", emboss=False)

                    row = box.row(align=True)
                    row.prop(self, "start_seed")
                    row.prop(self, "end_seed")
                    row = box.row()
                    row.prop(self, "mcell_processes")
                    #row = box.row()
                    #row.prop(self, "log_file")
                    #row = box.row()
                    #row.prop(self, "error_file")
                    row = box.row()
                    row.prop(mcell.export_project, "export_format")

                    row = box.row()
                    row.prop(self, "remove_append", expand=True)
                    row = box.row()
                    col = row.column()
                    col.prop(mcell.cellblender_preferences, "decouple_export_run")

# Disable selector for simulation_run_control options
#  Queue control is the default
#  Queue control is currently the only option which properly disables the
#  run_simulation operator while simulations are currenlty running or queued
                    if mcell.cellblender_preferences.show_sim_runner_options:
                        col = row.column()
                        col.prop(self, "simulation_run_control")

                else:
                    row = box.row(align=True)
                    row.alignment = 'LEFT'
                    row.prop(self, "show_output_options", icon='TRIA_RIGHT',
                             text="Output / Control Options", emboss=False)

                
            if self.status:
                row = layout.row()
                row.label(text=self.status, icon='ERROR')
            
            if self.error_list: 
                row = layout.row() 
                row.label(text="Errors:", icon='ERROR')
                row = layout.row()
                col = row.column()
                col.template_list("MCELL_UL_error_list", "run_simulation_queue",
                                  self, "error_list",
                                  self, "active_err_index", rows=2)


    def draw_panel ( self, context, panel ):
        """ Create a layout from the panel and draw into it """
        layout = panel.layout
        self.draw_layout_queue ( context, layout )



class MCellMolVizPropertyGroup(bpy.types.PropertyGroup):
    """ Property group for for molecule visualization.

      This is the "Visualize Simulation Results Panel".

    """

    mol_viz_seed_list = CollectionProperty(
        type=MCellStringProperty, name="Visualization Seed List")
    active_mol_viz_seed_index = IntProperty(
        name="Current Visualization Seed Index", default=0,
        update=cellblender_operators.read_viz_data_callback)
        #update= bpy.ops.mcell.read_viz_data)
    mol_file_dir = StringProperty(
        name="Molecule File Dir", subtype='NONE')
    mol_file_list = CollectionProperty(
        type=MCellStringProperty, name="Molecule File Name List")
    mol_file_num = IntProperty(
        name="Number of Molecule Files", default=0)
    mol_file_name = StringProperty(
        name="Current Molecule File Name", subtype='NONE')
    mol_file_index = IntProperty(name="Current Molecule File Index", default=0)
    mol_file_start_index = IntProperty(
        name="Molecule File Start Index", default=0)
    mol_file_stop_index = IntProperty(
        name="Molecule File Stop Index", default=0)
    mol_file_step_index = IntProperty(
        name="Molecule File Step Index", default=1)
    mol_viz_list = CollectionProperty(
        type=MCellStringProperty, name="Molecule Viz Name List")
    render_and_save = BoolProperty(name="Render & Save Images")
    mol_viz_enable = BoolProperty(
        name="Enable Molecule Vizualization",
        description="Disable for faster animation preview",
        default=True, update=cellblender_operators.mol_viz_update)
    color_list = CollectionProperty(
        type=MCellFloatVectorProperty, name="Molecule Color List")
    color_index = IntProperty(name="Color Index", default=0)
    manual_select_viz_dir = BoolProperty(
        name="Manually Select Viz Directory", default=False,
        description="Toggle the option to manually load viz data.",
        update=cellblender_operators.mol_viz_toggle_manual_select)


    def build_data_model_from_properties ( self, context ):
        print ( "Building Mol Viz data model from properties" )
        mv_dm = {}
        mv_dm['data_model_version'] = "DM_2015_04_13_1700"

        mv_seed_list = []
        for s in self.mol_viz_seed_list:
            mv_seed_list.append ( str(s.name) )
        mv_dm['seed_list'] = mv_seed_list

        mv_dm['active_seed_index'] = self.active_mol_viz_seed_index
        mv_dm['file_dir'] = self.mol_file_dir

        # mv_file_list = []
        # for s in self.mol_file_list:
        #     mv_file_list.append ( str(s.name) )
        # mv_dm['file_list'] = mv_file_list

        mv_dm['file_num'] = self.mol_file_num
        mv_dm['file_name'] = self.mol_file_name
        mv_dm['file_index'] = self.mol_file_index
        mv_dm['file_start_index'] = self.mol_file_start_index
        mv_dm['file_stop_index'] = self.mol_file_stop_index
        mv_dm['file_step_index'] = self.mol_file_step_index

        mv_viz_list = []
        for s in self.mol_viz_list:
            mv_viz_list.append ( str(s.name) )
        mv_dm['viz_list'] = mv_viz_list

        mv_dm['render_and_save'] = self.render_and_save
        mv_dm['viz_enable'] = self.mol_viz_enable

        mv_color_list = []
        for c in self.color_list:
            mv_color = []
            for i in c.vec:
                mv_color.append ( i )
            mv_color_list.append ( mv_color )
        mv_dm['color_list'] = mv_color_list

        mv_dm['color_index'] = self.color_index
        mv_dm['manual_select_viz_dir'] = self.manual_select_viz_dir

        return mv_dm


    @staticmethod
    def upgrade_data_model ( dm ):
        # Upgrade the data model as needed. Return updated data model or None if it can't be upgraded.
        print ( "------------------------->>> Upgrading MCellMolVizPropertyGroup Data Model" )
        if not ('data_model_version' in dm):
            # Make changes to move from unversioned to DM_2015_04_13_1700
            dm['data_model_version'] = "DM_2015_04_13_1700"

        if dm['data_model_version'] == "DM_2015_04_13_1700":
            # Change on June 22nd, 2015: The molecule file list will no longer be stored in the data model
            if 'file_list' in dm:
                dm.pop ( 'file_list' )
            dm['data_model_version'] = "DM_2015_06_22_1430"

        if dm['data_model_version'] != "DM_2015_06_22_1430":
            data_model.flag_incompatible_data_model ( "Error: Unable to upgrade MCellMolVizPropertyGroup data model to current version." )
            return None

        return dm



    def build_properties_from_data_model ( self, context, dm ):
        # Check that the data model version matches the version for this property group
        if dm['data_model_version'] != "DM_2015_06_22_1430":
            data_model.handle_incompatible_data_model ( "Error: Unable to upgrade MCellMolVizPropertyGroup data model to current version." )

        # Remove the old properties (includes emptying collections)
        self.remove_properties ( context )

        # Build the new properties
        
        for s in dm["seed_list"]:
            new_item = self.mol_viz_seed_list.add()
            new_item.name = s
            
        self.active_mol_viz_seed_index = dm['active_seed_index']

        self.mol_file_dir = dm['file_dir']

        #for s in dm["file_list"]:
        #    new_item = self.mol_file_list.add()
        #    new_item.name = s

        self.mol_file_num = dm['file_num']
        self.mol_file_name = dm['file_name']
        self.mol_file_index = dm['file_index']
        self.mol_file_start_index = dm['file_start_index']
        self.mol_file_stop_index = dm['file_stop_index']
        self.mol_file_step_index = dm['file_step_index']
            
        for s in dm["viz_list"]:
            new_item = self.mol_viz_list.add()
            new_item.name = s
            
        self.render_and_save = dm['render_and_save']
        self.mol_viz_enable = dm['viz_enable']

        for c in dm["color_list"]:
            new_item = self.color_list.add()
            new_item.vec = c
            
        if 'color_index' in dm:
            self.color_index = dm['color_index']
        else:
            self.color_index = 0

        self.manual_select_viz_dir = dm['manual_select_viz_dir']


    def check_properties_after_building ( self, context ):
        print ( "check_properties_after_building not implemented for " + str(self) )


    def remove_properties ( self, context ):
        print ( "Removing all Molecule Visualization Properties..." )

        """
        while len(self.mol_viz_seed_list) > 0:
            self.mol_viz_seed_list.remove(0)

        while len(self.mol_file_list) > 0:
            self.mol_file_list.remove(0)

        while len(self.mol_viz_list) > 0:
            self.mol_viz_list.remove(0)

        while len(self.color_list) > 0:
            # It's not clear if anything needs to be done to remove individual color components first
            self.color_list.remove(0)
        """

        for item in self.mol_viz_seed_list:
            item.remove_properties(context)
        self.mol_viz_seed_list.clear()
        self.active_mol_viz_seed_index = 0
        for item in self.mol_file_list:
            item.remove_properties(context)
        self.mol_file_list.clear()
        self.mol_file_index = 0
        self.mol_file_start_index = 0
        self.mol_file_stop_index = 0
        self.mol_file_step_index = 1
        for item in self.mol_viz_list:
            item.remove_properties(context)
        self.mol_viz_list.clear()
        for item in self.color_list:
            item.remove_properties(context)
        self.color_list.clear()
        self.color_index = 0
        print ( "Done removing all Molecule Visualization Properties." )





    def draw_layout(self, context, layout):
        mcell = context.scene.mcell

        if not mcell.initialized:
            mcell.draw_uninitialized ( layout )
        else:

            row = layout.row()
            row.prop(mcell.mol_viz, "manual_select_viz_dir")
            row = layout.row()
            if self.manual_select_viz_dir:
                row.operator("mcell.select_viz_data", icon='IMPORT')
            else:
                row.operator("mcell.read_viz_data", icon='IMPORT')
            row = layout.row()
            row.label(text="Molecule Viz Directory: " + self.mol_file_dir,
                      icon='FILE_FOLDER')
            row = layout.row()
            if not self.manual_select_viz_dir:
                row.template_list("UI_UL_list", "viz_seed", mcell.mol_viz,
                                "mol_viz_seed_list", mcell.mol_viz,
                                "active_mol_viz_seed_index", rows=2)
            row = layout.row()

            row = layout.row()
            row.label(text="Current Molecule File: "+self.mol_file_name,
                      icon='FILE')
# Disabled to explore UI slowdown behavior of Plot Panel and run options subpanel when mol_file_list is large
#            row = layout.row()
#            row.template_list("UI_UL_list", "viz_results", mcell.mol_viz,
#                              "mol_file_list", mcell.mol_viz, "mol_file_index",
#                              rows=2)
            row = layout.row()
            layout.prop(mcell.mol_viz, "mol_viz_enable")


    def draw_panel ( self, context, panel ):
        """ Create a layout from the panel and draw into it """
        layout = panel.layout
        self.draw_layout ( context, layout )



# from . import parameter_system



class MCellModSurfRegionsPropertyGroup(bpy.types.PropertyGroup):
    mod_surf_regions_list = CollectionProperty(
        type=MCellModSurfRegionsProperty, name="Assign Surface Class List")
    active_mod_surf_regions_index = IntProperty(
        name="Active Assign Surface Class Index", default=0)

    def build_data_model_from_properties ( self, context ):
        print ( "Assign Surface Class List building Data Model" )
        sr_dm = {}
        sr_dm['data_model_version'] = "DM_2014_10_24_1638"
        sr_list = []
        for sr in self.mod_surf_regions_list:
            sr_list.append ( sr.build_data_model_from_properties(context) )
        sr_dm['modify_surface_regions_list'] = sr_list
        return sr_dm


    @staticmethod
    def upgrade_data_model ( dm ):
        # Upgrade the data model as needed. Return updated data model or None if it can't be upgraded.
        print ( "------------------------->>> Upgrading MCellModSurfRegionsPropertyGroup Data Model" )
        if not ('data_model_version' in dm):
            # Make changes to move from unversioned to DM_2014_10_24_1638
            dm['data_model_version'] = "DM_2014_10_24_1638"

        if dm['data_model_version'] != "DM_2014_10_24_1638":
            data_model.flag_incompatible_data_model ( "Error: Unable to upgrade MCellModSurfRegionsPropertyGroup data model to current version." )
            return None

        if "modify_surface_regions_list" in dm:
            for item in dm["modify_surface_regions_list"]:
                if MCellModSurfRegionsProperty.upgrade_data_model ( item ) == None:
                    return None

        return dm


    def build_properties_from_data_model ( self, context, dm ):

        # Check that the data model version matches the version for this property group
        if dm['data_model_version'] != "DM_2014_10_24_1638":
            data_model.handle_incompatible_data_model ( "Error: Unable to upgrade MCellModSurfRegionsPropertyGroup data model to current version." )

        while len(self.mod_surf_regions_list) > 0:
            self.mod_surf_regions_list.remove(0)
        if "modify_surface_regions_list" in dm:
            for s in dm["modify_surface_regions_list"]:
                self.mod_surf_regions_list.add()
                self.active_mod_surf_regions_index = len(self.mod_surf_regions_list)-1
                sr = self.mod_surf_regions_list[self.active_mod_surf_regions_index]
                # sr.init_properties(context.scene.mcell.parameter_system)
                sr.build_properties_from_data_model ( context, s )


    def check_properties_after_building ( self, context ):
        print ( "Implementing check_properties_after_building for " + str(self) )
        for sr in self.mod_surf_regions_list:
            sr.check_properties_after_building(context)

    def remove_properties ( self, context ):
        print ( "Removing all Surface Regions Properties ..." )
        for item in self.mod_surf_regions_list:
            item.remove_properties(context)
        self.mod_surf_regions_list.clear()
        self.active_mod_surf_regions_index = 0
        print ( "Done removing all Surface Regions Properties." )


    def draw_layout(self, context, layout):
        mcell = context.scene.mcell

        if not mcell.initialized:
            mcell.draw_uninitialized ( layout )
        else:

            # mod_surf_regions = context.scene.mcell.mod_surf_regions

            row = layout.row()
            if not mcell.surface_classes.surf_class_list:
                row.label(text="Define at least one surface class", icon='ERROR')
            elif not mcell.model_objects.object_list:
                row.label(text="Add a mesh to the Model Objects list",
                          icon='ERROR')
            else:
                col = row.column()
                col.template_list("MCELL_UL_check_mod_surface_regions",
                                  "mod_surf_regions", self,
                                  "mod_surf_regions_list", self,
                                  "active_mod_surf_regions_index", rows=2)
                col = row.column(align=True)
                col.operator("mcell.mod_surf_regions_add", icon='ZOOMIN', text="")
                col.operator("mcell.mod_surf_regions_remove", icon='ZOOMOUT',
                             text="")
                if self.mod_surf_regions_list:
                    active_mod_surf_regions = \
                        self.mod_surf_regions_list[
                            self.active_mod_surf_regions_index]
                    row = layout.row()
                    row.prop_search(active_mod_surf_regions, "surf_class_name",
                                    mcell.surface_classes, "surf_class_list",
                                    icon='FACESEL_HLT')
                    row = layout.row()
                    row.prop_search(active_mod_surf_regions, "object_name",
                                    mcell.model_objects, "object_list",
                                    icon='MESH_ICOSPHERE')
                    if active_mod_surf_regions.object_name:
                        try:
                            regions = bpy.data.objects[
                                active_mod_surf_regions.object_name].mcell.regions
                            layout.prop_search(active_mod_surf_regions,
                                               "region_name", regions,
                                               "region_list", icon='FACESEL_HLT')
                        except KeyError:
                            pass


    def draw_panel ( self, context, panel ):
        """ Create a layout from the panel and draw into it """
        layout = panel.layout
        self.draw_layout ( context, layout )




class MCellModelObjectsProperty(bpy.types.PropertyGroup):
    name = StringProperty(
        name="Object Name", update=cellblender_operators.check_model_object)
    status = StringProperty(name="Status")
    """
    def build_data_model_from_properties ( self, context ):
        print ( "Model Object building Data Model" )
        mo_dm = {}
        mo_dm['data_model_version'] = "DM_2014_10_24_1638"
        mo_dm['name'] = self.name
        return mo_dm


    @staticmethod
    def upgrade_data_model ( dm ):
        # Upgrade the data model as needed. Return updated data model or None if it can't be upgraded.
        print ( "------------------------->>> Upgrading MCellModelObjectsProperty Data Model" )
        print ( "-------------->>>>>>>>>>>>>>>>>>>>> NOT IMPLEMENTED YET!!!" )
        return dm



    def build_properties_from_data_model ( self, context, dm ):

        # Upgrade the data model as needed
        if not ('data_model_version' in dm):
            # Make changes to move from unversioned to DM_2014_10_24_1638
            dm['data_model_version'] = "DM_2014_10_24_1638"

        if dm['data_model_version'] != "DM_2014_10_24_1638":
            data_model.handle_incompatible_data_model ( "Error: Unable to upgrade MCellModelObjectsProperty data model to current version." )

        print ( "Assigning Model Object " + dm['name'] )
        self.name = dm["name"]

    def check_properties_after_building ( self, context ):
        print ( "check_properties_after_building not implemented for " + str(self) )

    """

    def remove_properties ( self, context ):
        print ( "Removing all Model Objects Properties... no collections to remove." )



import mathutils

class MCellModelObjectsPropertyGroup(bpy.types.PropertyGroup):
    object_list = CollectionProperty(
        type=MCellModelObjectsProperty, name="Object List")
    active_obj_index = IntProperty(name="Active Object Index", default=0)
    show_display = bpy.props.BoolProperty(default=False)  # If Some Properties are not shown, they may not exist!!!

    def remove_properties ( self, context ):
        print ( "Removing all Model Object List Properties..." )
        for item in self.object_list:
            item.remove_properties(context)
        self.object_list.clear()
        self.active_obj_index = 0
        print ( "Done removing all Model Object List Properties." )


    def draw_layout ( self, context, layout ):
        mcell = context.scene.mcell

        if not mcell.initialized:
            mcell.draw_uninitialized ( layout )
        else:

            if context.active_object != None:
                row = layout.row()
                row.prop ( context.active_object, "name", text="Active:" )

            row = layout.row()
            col = row.column()
            col.template_list("MCELL_UL_model_objects", "model_objects",
                              self, "object_list",
                              self, "active_obj_index", rows=2)
            col = row.column(align=True)
#           col.active = (len(context.selected_objects) == 1)
            col.operator("mcell.model_objects_add", icon='ZOOMIN', text="")
            col.operator("mcell.model_objects_remove", icon='ZOOMOUT', text="")
            
            if len(self.object_list) > 0:
                box = layout.box()
                row = box.row()
                if not self.show_display:
                    row.prop(self, "show_display", icon='TRIA_RIGHT',
                             text=str(self.object_list[self.active_obj_index].name)+" Display Options", emboss=False)
                else:
                    row.prop(self, "show_display", icon='TRIA_DOWN',
                             text=str(self.object_list[self.active_obj_index].name)+" Display Options", emboss=False)

                    row = box.row()
                    row.prop ( context.scene.objects[self.object_list[self.active_obj_index].name], "draw_type" )
                    row = box.row()
                    row.prop ( context.scene.objects[self.object_list[self.active_obj_index].name], "show_transparent" )

#           row = layout.row()
#           sub = row.row(align=True)
#           sub.operator("mcell.model_objects_include", text="Include")
#           sub = row.row(align=True)
#           sub.operator("mcell.model_objects_select", text="Select")
#           sub.operator("mcell.model_objects_deselect", text="Deselect")

            """
            row = layout.row()
            row.label(text="Object Color:", icon='COLOR')
            
            active = None
            for o in self.object_list.keys():
                # print ( "Object: " + o )
                row = layout.row()
                if bpy.context.scene.objects[o] == bpy.context.scene.objects.active:
                    active = bpy.context.scene.objects[o]
                    row.label(text=o, icon='TRIA_RIGHT')
                else:
                    row.label(text=o, icon='DOT')

            if active == None:
                row = layout.row()
                row.label(text="No CellBlender object is active", icon='DOT')
            else:
                row = layout.row()
                row.label ( icon='DOT', text="  Object " + active.name + " is active and has " +
                    str(len(active.material_slots)) + " material slots" )
            """


    def draw_panel ( self, context, panel ):
        """ Create a layout from the panel and draw into it """
        layout = panel.layout
        self.draw_layout ( context, layout )


    def build_data_model_from_properties ( self, context ):
    
        print ( "Model Objects List building Data Model" )
        mo_dm = {}
        mo_dm['data_model_version'] = "DM_2014_10_24_1638"
        mo_list = []
        for scene_object in context.scene.objects:
            if scene_object.type == 'MESH':
                if scene_object.mcell.include:
                    print ( "MCell object: " + scene_object.name )
                    mo_list.append ( { "name": scene_object.name } )
        mo_dm['model_object_list'] = mo_list
        return mo_dm


    @staticmethod
    def upgrade_data_model ( dm ):
        # Upgrade the data model as needed. Return updated data model or None if it can't be upgraded.
        print ( "------------------------->>> Upgrading MCellModelObjectsPropertyGroup Data Model" )
        if not ('data_model_version' in dm):
            # Make changes to move from unversioned to DM_2014_10_24_1638
            dm['data_model_version'] = "DM_2014_10_24_1638"

        # Check that the upgraded data model version matches the version for this property group
        if dm['data_model_version'] != "DM_2014_10_24_1638":
            data_model.flag_incompatible_data_model ( "Error: Unable to upgrade MCellModelObjectsPropertyGroup data model to current version." )
            return None

        return dm


    def build_properties_from_data_model ( self, context, dm ):
        # Note that model object list is represented in two places:
        #   context.scene.mcell.model_objects.object_list[] - stores the name
        #   context.scene.objects[].mcell.include - boolean is true for model objects
        # This code updates both locations based on the data model

        if dm['data_model_version'] != "DM_2014_10_24_1638":
            data_model.handle_incompatible_data_model ( "Error: Unable to upgrade MCellModelObjectsPropertyGroup data model to current version." )
        
        # Remove all model objects in the list
        while len(self.object_list) > 0:
            self.object_list.remove(0)
            
        # Create a list of model object names from the Data Model
        mo_list = []
        if "model_object_list" in dm:
          for m in dm["model_object_list"]:
              print ( "Data model contains " + m["name"] )
              self.object_list.add()
              self.active_obj_index = len(self.object_list)-1
              mo = self.object_list[self.active_obj_index]
              #mo.init_properties(context.scene.mcell.parameter_system)
              #mo.build_properties_from_data_model ( context, m )
              mo.name = m['name']
              mo_list.append ( m["name"] )

        # Use the list of Data Model names to set flags of all objects
        for k,o in context.scene.objects.items():
            if k in mo_list:
                o.mcell.include = True
            else:
                o.mcell.include = False

    def check_properties_after_building ( self, context ):
        print ( "check_properties_after_building not implemented for " + str(self) )



    def build_data_model_materials_from_materials ( self, context ):
        print ( "Model Objects List building Materials for Data Model" )
        mat_dm = {}
        mat_dict = {}

        # First build the list of materials from all objects
        for data_object in context.scene.objects:
            if data_object.type == 'MESH':
                if data_object.mcell.include:
                    print ( "Saving Materials for: " + data_object.name )
                    for mat_slot in data_object.material_slots:
                        if not mat_slot.name in mat_dict:
                            # This is a new material, so add it
                            mat = bpy.data.materials[mat_slot.name]
                            print ( "  Adding " + mat_slot.name )
                            mat_obj = {}
                            mat_obj['diffuse_color'] = {
                                'r': mat.diffuse_color.r,
                                'g': mat.diffuse_color.g,
                                'b': mat.diffuse_color.b,
                                'a': mat.alpha }
                            # Need to set:
                            #  mat.use_transparency
                            #  obj.show_transparent
                            mat_dict[mat_slot.name] = mat_obj;
        mat_dm['material_dict'] = mat_dict
        return mat_dm


    def build_materials_from_data_model_materials ( self, context, dm ):

        # Delete any materials with conflicting names and then rebuild all

        # Start by creating a list of named materials in the data model
        mat_names = dm['material_dict'].keys()
        print ( "Material names = " + str(mat_names) )
        
        # Delete all materials with identical names
        for mat_name in mat_names:
            if mat_name in bpy.data.materials:
                bpy.data.materials.remove ( bpy.data.materials[mat_name] )
        
        # Now add all the new materials
        
        for mat_name in mat_names:
            new_mat = bpy.data.materials.new(mat_name)
            c = dm['material_dict'][mat_name]['diffuse_color']
            new_mat.diffuse_color = ( c['r'], c['g'], c['b'] )
            new_mat.alpha = c['a']
            if new_mat.alpha < 1.0:
                new_mat.use_transparency = True


    def build_data_model_geometry_from_mesh ( self, context ):
        print ( "Model Objects List building Geometry for Data Model" )
        g_dm = {}
        g_list = []

        for data_object in context.scene.objects:
            if data_object.type == 'MESH':
                if data_object.mcell.include:
                    print ( "MCell object: " + data_object.name )

                    g_obj = {}
                    
                    saved_hide_status = data_object.hide
                    data_object.hide = False

                    context.scene.objects.active = data_object
                    bpy.ops.object.mode_set(mode='OBJECT')

                    g_obj['name'] = data_object.name
                    
                    loc_x = data_object.location.x
                    loc_y = data_object.location.y
                    loc_z = data_object.location.z

                    g_obj['location'] = [loc_x, loc_y, loc_z]
                    
                    if len(data_object.data.materials) > 0:
                        g_obj['material_names'] = []
                        for mat in data_object.data.materials:
                            g_obj['material_names'].append ( mat.name )
                            # g_obj['material_name'] = data_object.data.materials[0].name
                    
                    v_list = []
                    mesh = data_object.data
                    matrix = data_object.matrix_world
                    vertices = mesh.vertices
                    for v in vertices:
                        t_vec = matrix * v.co
                        v_list.append ( [t_vec.x-loc_x, t_vec.y-loc_y, t_vec.z-loc_z] )
                    g_obj['vertex_list'] = v_list

                    f_list = []
                    faces = mesh.polygons
                    for f in faces:
                        f_list.append ( [f.vertices[0], f.vertices[1], f.vertices[2]] )
                    g_obj['element_connections'] = f_list
                    
                    if len(data_object.data.materials) > 1:
                        # This object has multiple materials, so store the material index for each face
                        mi_list = []
                        for f in faces:
                            mi_list.append ( f.material_index )
                        g_obj['element_material_indices'] = mi_list

                    regions = data_object.mcell.get_regions_dictionary(data_object)
                    if regions:
                        r_list = []

                        region_names = [k for k in regions.keys()]
                        region_names.sort()
                        for region_name in region_names:
                            rgn = {}
                            rgn['name'] = region_name
                            rgn['include_elements'] = regions[region_name]
                            r_list.append ( rgn )
                        g_obj['define_surface_regions'] = r_list

                    # restore proper object visibility state
                    data_object.hide = saved_hide_status

                    g_list.append ( g_obj )

        g_dm['object_list'] = g_list
        return g_dm


    def delete_all_mesh_objects ( self, context ):
        bpy.ops.object.select_all(action='DESELECT')
        for scene_object in context.scene.objects:
            if scene_object.type == 'MESH':
                print ( "Deleting Mesh object: " + scene_object.name )
                scene_object.hide = False
                scene_object.select = True
                bpy.ops.object.delete()
                # TODO Need to delete the mesh for this object as well!!!


    def build_mesh_from_data_model_geometry ( self, context, dm ):
            
        # Delete any objects with conflicting names and then rebuild all

        print ( "Model Objects List building Mesh Objects from Data Model Geometry" )
        
        # Start by creating a list of named objects in the data model
        model_names = [ o['name'] for o in dm['object_list'] ]
        print ( "Model names = " + str(model_names) )

        # Delete all objects with identical names to model objects in the data model
        bpy.ops.object.select_all(action='DESELECT')
        for scene_object in context.scene.objects:
            if scene_object.type == 'MESH':
                print ( "Mesh object: " + scene_object.name )
                if scene_object.name in model_names:
                    print ( "  will be recreated from the data model ... deleting." )
                    # TODO preserve hidden/shown status
                    scene_object.hide = False
                    scene_object.select = True
                    bpy.ops.object.delete()
                    # TODO Need to delete the mesh for this object as well!!!

        # Now create all the object meshes from the data model
        for model_object in dm['object_list']:

            vertices = []
            for vertex in model_object['vertex_list']:
                vertices.append ( mathutils.Vector((vertex[0],vertex[1],vertex[2])) )
            faces = []
            for face_element in model_object['element_connections']:
                faces.append ( face_element )
            new_mesh = bpy.data.meshes.new ( model_object['name'] )
            new_mesh.from_pydata ( vertices, [], faces )
            new_mesh.update()
            new_obj = bpy.data.objects.new ( model_object['name'], new_mesh )
            if 'location' in model_object:
                new_obj.location = mathutils.Vector((model_object['location'][0],model_object['location'][1],model_object['location'][2]))

            # Add the materials to the object
            if 'material_names' in model_object:
                print ( "Object " + model_object['name'] + " has material names" )
                for mat_name in model_object['material_names']:
                    new_obj.data.materials.append ( bpy.data.materials[mat_name] )
                    if bpy.data.materials[mat_name].alpha < 1:
                        new_obj.show_transparent = True
                if 'element_material_indices' in model_object:
                    print ( "Object " + model_object['name'] + " has material indices" )
                    faces = new_obj.data.polygons
                    dm_count = len(model_object['element_material_indices'])
                    index = 0
                    for f in faces:
                        f.material_index = model_object['element_material_indices'][index % dm_count]
                        index += 1

            context.scene.objects.link ( new_obj )
            bpy.ops.object.select_all ( action = "DESELECT" )
            new_obj.select = True
            context.scene.objects.active = new_obj
            

            # Add the surface regions to new_obj.mcell
            
            if model_object.get('define_surface_regions'):
                for rgn in model_object['define_surface_regions']:
                    print ( "  Building region[" + rgn['name'] + "]" )
                    new_obj.mcell.regions.add_region_by_name ( context, rgn['name'] )
                    reg = new_obj.mcell.regions.region_list[rgn['name']]
                    reg.set_region_faces ( new_mesh, set(rgn['include_elements']) )



class MCellVizOutputPropertyGroup(bpy.types.PropertyGroup):
    active_mol_viz_index = IntProperty(
        name="Active Molecule Viz Index", default=0)
    all_iterations = bpy.props.BoolProperty(
        name="All Iterations",
        description="Include all iterations for visualization.", default=True)
    start = bpy.props.IntProperty(
        name="Start", description="Starting iteration", default=0, min=0)
    end = bpy.props.IntProperty(
        name="End", description="Ending iteration", default=1, min=1)
    step = bpy.props.IntProperty(
        name="Step", description="Output viz data every n iterations.",
        default=1, min=1)
    export_all = BoolProperty(
        name="Export All",
        description="Visualize all molecules",
        default=True)

    def build_data_model_from_properties ( self, context ):
        print ( "Viz Output building Data Model" )
        vo_dm = {}
        vo_dm['data_model_version'] = "DM_2014_10_24_1638"
        vo_dm['all_iterations'] = self.all_iterations
        vo_dm['start'] = str(self.start)
        vo_dm['end'] = str(self.end)
        vo_dm['step'] = str(self.step)
        vo_dm['export_all'] = self.export_all
        return vo_dm


    @staticmethod
    def upgrade_data_model ( dm ):
        # Upgrade the data model as needed. Return updated data model or None if it can't be upgraded.
        print ( "------------------------->>> Upgrading MCellVizOutputPropertyGroup Data Model" )
        if not ('data_model_version' in dm):
            # Make changes to move from unversioned to DM_2014_10_24_1638
            dm['data_model_version'] = "DM_2014_10_24_1638"

        # Check that the upgraded data model version matches the version for this property group
        if dm['data_model_version'] != "DM_2014_10_24_1638":
            data_model.flag_incompatible_data_model ( "Error: Unable to upgrade MCellVizOutputPropertyGroup data model to current version." )
            return None

        return dm



    def build_properties_from_data_model ( self, context, dm ):
        # Check that the data model version matches the version for this property group
        if dm['data_model_version'] != "DM_2014_10_24_1638":
            data_model.handle_incompatible_data_model ( "Error: Unable to upgrade MCellVizOutputPropertyGroup data model to current version." )
        
        self.all_iterations = dm["all_iterations"]
        self.start = int(dm["start"])
        self.end = int(dm["end"])
        self.step = int(dm["step"])
        self.export_all = dm["export_all"]

    def check_properties_after_building ( self, context ):
        print ( "check_properties_after_building not implemented for " + str(self) )


    def remove_properties ( self, context ):
        print ( "Removing all Visualization Output Properties... no collections to remove." )


    def draw_layout ( self, context, layout ):
        """ Draw the reaction output "panel" within the layout """
        mcell = context.scene.mcell

        if not mcell.initialized:
            mcell.draw_uninitialized ( layout )
        else:
            row = layout.row()
            if mcell.molecules.molecule_list:
                row.label(text="Molecules To Visualize:",
                          icon='FORCE_LENNARDJONES')
                row.prop(self, "export_all")
                layout.template_list("MCELL_UL_visualization_export_list",
                                     "viz_export", mcell.molecules,
                                     "molecule_list", self,
                                     "active_mol_viz_index", rows=2)
                layout.prop(self, "all_iterations")
                if self.all_iterations is False:
                    row = layout.row(align=True)
                    row.prop(self, "start")
                    row.prop(self, "end")
                    row.prop(self, "step")
            else:
                row.label(text="Define at least one molecule", icon='ERROR')


    def draw_panel ( self, context, panel ):
        """ Create a layout from the panel and draw into it """
        layout = panel.layout
        self.draw_layout ( context, layout )


import cellblender


class MCellMoleculeGlyphsPropertyGroup(bpy.types.PropertyGroup):
    glyph_lib = os.path.join(
        os.path.dirname(__file__), "glyph_library.blend/Mesh/")
    glyph_enum = [
        ('Cone', "Cone", ""),
        ('Cube', "Cube", ""),
        ('Cylinder', "Cylinder", ""),
        ('Icosahedron', "Icosahedron", ""),
        ('Octahedron', "Octahedron", ""),
        ('Receptor', "Receptor", ""),
        ('Sphere_1', "Sphere_1", ""),
        ('Sphere_2', "Sphere_2", ""),
        ('Torus', "Torus", "")]
    glyph = EnumProperty(items=glyph_enum, name="Molecule Shapes")
    show_glyph = BoolProperty(name="Show Glyphs",description="Show Glyphs ... can cause slowness!!",default=True)
    status = StringProperty(name="Status")

    def remove_properties ( self, context ):
        print ( "Removing all Molecule Glyph Properties... no collections to remove." )



class MCellMeshalyzerPropertyGroup(bpy.types.PropertyGroup):
    object_name = StringProperty(name="Object Name")
    vertices = IntProperty(name="Vertices", default=0)
    edges = IntProperty(name="Edges", default=0)
    faces = IntProperty(name="Faces", default=0)
    watertight = StringProperty(name="Watertight")
    manifold = StringProperty(name="Manifold")
    normal_status = StringProperty(name="Surface Normals")
    area = FloatProperty(name="Area", default=0)
    volume = FloatProperty(name="Volume", default=0)
    sav_ratio = FloatProperty(name="SA/V Ratio", default=0)
    status = StringProperty(name="Status")

    def remove_properties ( self, context ):
        print ( "Removing all Meshalyzer Properties... no collections to remove." )



class MCellObjectSelectorPropertyGroup(bpy.types.PropertyGroup):
    filter = StringProperty(
        name="Object Name Filter",
        description="Enter a regular expression for object names.")

    def remove_properties ( self, context ):
        print ( "Removing all Object Selector Properties... no collections to remove." )




class PP_OT_init_mcell(bpy.types.Operator):
    bl_idname = "mcell.init_cellblender"
    bl_label = "Init CellBlender"
    bl_description = "Initialize CellBlender"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        print ( "Initializing CellBlender" )
        mcell = context.scene.mcell
        mcell.init_properties()
        mcell.rxn_output.init_properties(mcell.parameter_system)
        print ( "CellBlender has been initialized" )
        return {'FINISHED'}




def show_old_scene_panels ( show=False ):
    if show:
        print ( "Showing the Old CellBlender panels in the Scene tab" )
        try:
            bpy.utils.register_class(cellblender_panels.MCELL_PT_cellblender_preferences)
            bpy.utils.register_class(cellblender_panels.MCELL_PT_project_settings)
            # bpy.utils.register_class(cellblender_panels.MCELL_PT_run_simulation)
            bpy.utils.register_class(cellblender_panels.MCELL_PT_run_simulation_queue)
            bpy.utils.register_class(cellblender_panels.MCELL_PT_viz_results)
            bpy.utils.register_class(parameter_system.MCELL_PT_parameter_system)
            bpy.utils.register_class(cellblender_panels.MCELL_PT_model_objects)
            bpy.utils.register_class(cellblender_panels.MCELL_PT_partitions)
            bpy.utils.register_class(cellblender_panels.MCELL_PT_initialization)
            bpy.utils.register_class(cellblender_molecules.MCELL_PT_define_molecules)
            bpy.utils.register_class(cellblender_panels.MCELL_PT_define_reactions)
            bpy.utils.register_class(cellblender_panels.MCELL_PT_define_surface_classes)
            bpy.utils.register_class(cellblender_panels.MCELL_PT_mod_surface_regions)
            bpy.utils.register_class(cellblender_panels.MCELL_PT_release_pattern)
            bpy.utils.register_class(cellblender_panels.MCELL_PT_molecule_release)
            bpy.utils.register_class(cellblender_panels.MCELL_PT_reaction_output_settings)
            bpy.utils.register_class(cellblender_panels.MCELL_PT_visualization_output_settings)
        except:
            pass
    else:
        print ( "Hiding the Old CellBlender panels in the Scene tab" )
        try:
            bpy.utils.unregister_class(cellblender_panels.MCELL_PT_cellblender_preferences)
            bpy.utils.unregister_class(cellblender_panels.MCELL_PT_project_settings)
            # bpy.utils.unregister_class(cellblender_panels.MCELL_PT_run_simulation)
            bpy.utils.unregister_class(cellblender_panels.MCELL_PT_run_simulation_queue)
            bpy.utils.unregister_class(cellblender_panels.MCELL_PT_viz_results)
            bpy.utils.unregister_class(cellblender_panels.MCELL_PT_model_objects)
            bpy.utils.unregister_class(cellblender_panels.MCELL_PT_partitions)
            bpy.utils.unregister_class(cellblender_panels.MCELL_PT_initialization)
            bpy.utils.unregister_class(parameter_system.MCELL_PT_parameter_system)
            bpy.utils.unregister_class(cellblender_molecules.MCELL_PT_define_molecules)
            bpy.utils.unregister_class(cellblender_panels.MCELL_PT_define_reactions)
            bpy.utils.unregister_class(cellblender_panels.MCELL_PT_define_surface_classes)
            bpy.utils.unregister_class(cellblender_panels.MCELL_PT_mod_surface_regions)
            bpy.utils.unregister_class(cellblender_panels.MCELL_PT_release_pattern)
            bpy.utils.unregister_class(cellblender_panels.MCELL_PT_molecule_release)
            bpy.utils.unregister_class(cellblender_panels.MCELL_PT_reaction_output_settings)
            bpy.utils.unregister_class(cellblender_panels.MCELL_PT_visualization_output_settings)
        except:
            pass



def show_hide_tool_panel ( show=True ):
    if show:
        print ( "Showing CellBlender panel in the Tool tab" )
        try:
            bpy.utils.register_class(MCELL_PT_main_panel)
        except:
            pass
    else:
        print ( "Hiding the CellBlender panel in the Tool tab" )
        try:
            bpy.utils.unregister_class(MCELL_PT_main_panel)
        except:
            pass


def show_hide_scene_panel ( show=True ):
    if show:
        print ( "Showing the CellBlender panel in the Scene tab" )
        try:
            bpy.utils.register_class(MCELL_PT_main_scene_panel)
        except:
            pass
    else:
        print ( "Hiding the CellBlender panel in the Scene tab" )
        try:
            bpy.utils.unregister_class(MCELL_PT_main_scene_panel)
        except:
            pass






    

# My panel class (which happens to augment 'Scene' properties)
class MCELL_PT_main_panel(bpy.types.Panel):
    # bl_idname = "SCENE_PT_CB_MU_APP"
    bl_label = "  CellBlender"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "CellBlender"
    
    @classmethod
    def poll(cls, context):
        return (context.scene is not None)


    def draw_header(self, context):
        # LOOK HERE!! This is where the icon is actually included in the panel layout!
        # The icon() method takes the image data-block in and returns an integer that
        # gets passed to the 'icon_value' argument of your label/prop constructor or 
        # within a UIList subclass
        img = bpy.data.images.get('cellblender_icon')
        #could load multiple images and animate the icon too.
        #icons = [img for img in bpy.data.images if hasattr(img, "icon")]
        if img is not None:
            icon = self.layout.icon(img)
            self.layout.label(text="", icon_value=icon)

    def draw(self, context):
        context.scene.mcell.cellblender_main_panel.draw_self(context,self.layout)

'''
class MCELL_PT_main_scene_panel(bpy.types.Panel):
    bl_label = "CellBlender Scene"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        # LOOK HERE!! This is where the icon is actually included in the panel layout!
        # The icon() method takes the image data-block in and returns an integer that
        # gets passed to the 'icon_value' argument of your label/prop constructor or 
        # within a UIList subclass
        img = bpy.data.images.get('cellblender_icon')
        #could load multiple images and animate the icon too.
        #icons = [img for img in bpy.data.images if hasattr(img, "icon")]
        if img is not None:
            icon = self.layout.icon(img)
            self.layout.label(text="", icon_value=icon)

    def draw(self, context):
        context.scene.mcell.cellblender_main_panel.draw_self(context,self.layout)
'''


# load_pre callback
@persistent
def report_load_pre(dummy):
    # Note that load_pre may not be called when the startup file is loaded for earlier versions of Blender (somewhere before 2.73)
    print ( "===================================================================================" )
    print ( "================================= Load Pre called =================================" )
    print ( "===================================================================================" )


# Load scene callback
@persistent
def scene_loaded(dummy):
    # Icon
    #print("ADDON_ICON")
    icon_files = { 'cellblender_icon': 'cellblender_icon.png', 'mol_u': 'mol_unsel.png', 'mol_s': 'mol_sel.png', 'reaction_u': 'reactions_unsel.png', 'reaction_s': 'reactions_sel.png' }
    for icon_name in icon_files:
        fname = icon_files[icon_name]
        dirname = os.path.dirname(__file__)
        dirname = os.path.join(dirname,'icons')
        icon = bpy.data.images.get(icon_name)
        if icon is None:
            img = bpy.data.images.load(os.path.join(dirname, fname))
            img.name = icon_name
            img.use_alpha = True
            img.user_clear() # Won't get saved into .blend files
        # remove scene_update handler
        elif "icon" not in icon.keys():
            icon["icon"] = True
            for f in bpy.app.handlers.scene_update_pre:
                if f.__name__ == "scene_loaded":
                    print("Removing scene_loaded handler now that icons are loaded")
                    bpy.app.handlers.scene_update_pre.remove(f)




class CBM_OT_refresh_operator(bpy.types.Operator):
    bl_idname = "cbm.refresh_operator"
    bl_label = "Refresh"
    bl_description = ("Refresh Molecules from Simulation")
    bl_options = {'REGISTER'}

    def execute(self, context):
        print ( "Refreshing/Reloading the Molecules..." )
        bpy.ops.mcell.read_viz_data()
        return {'FINISHED'}



def select_callback ( self, context ):
    self.select_callback(context)


class CellBlenderMainPanelPropertyGroup(bpy.types.PropertyGroup):

    preferences_select = BoolProperty ( name="pref_sel", description="Preferences", default=False, subtype='NONE', update=select_callback)
    settings_select = BoolProperty ( name="set_sel", description="Project Settings", default=False, subtype='NONE', update=select_callback)
    parameters_select = BoolProperty ( name="par_sel", description="Model Parameters", default=False, subtype='NONE', update=select_callback)
    reaction_select = BoolProperty ( name="react_sel", description="Reactions", default=False, subtype='NONE', update=select_callback)
    molecule_select = BoolProperty ( name="mol_sel", description="Molecules", default=False, subtype='NONE', update=select_callback)
    placement_select = BoolProperty ( name="place_sel", description="Molecule Placement", default=False, subtype='NONE', update=select_callback)
    objects_select = BoolProperty ( name="obj_sel", description="Model Objects", default=False, subtype='NONE', update=select_callback)
    surf_classes_select = BoolProperty ( name="surfc_sel", description="Surface Classes", default=False, subtype='NONE', update=select_callback)
    surf_regions_select = BoolProperty ( name="surfr_sel", description="Assign Surface Classes", default=False, subtype='NONE', update=select_callback)
    rel_patterns_select = BoolProperty ( name="relpat_sel", description="Release Patterns", default=False, subtype='NONE', update=select_callback)
    partitions_select = BoolProperty ( name="part_sel", description="Partitions", default=False, subtype='NONE', update=select_callback)
    init_select = BoolProperty ( name="init_sel", description="Run Simulation", default=False, subtype='NONE', update=select_callback)
    # run_select = BoolProperty ( name="run_sel", description="Old Run Simulation", default=False, subtype='NONE', update=select_callback)
    graph_select = BoolProperty ( name="graph_sel", description="Plot Output Settings", default=False, subtype='NONE', update=select_callback)
    mol_viz_select = BoolProperty ( name="mviz_sel", description="Visual Output Settings", default=False, subtype='NONE', update=select_callback)
    viz_select = BoolProperty ( name="viz_sel", description="Visual Output Settings", default=False, subtype='NONE', update=select_callback)
    reload_viz = BoolProperty ( name="reload", description="Reload Simulation Data", default=False, subtype='NONE', update=select_callback)
    
    select_multiple = BoolProperty ( name="multiple", description="Show Multiple Panels", default=False, subtype='NONE', update=select_callback)
    
    last_state = BoolVectorProperty ( size=22 ) # Keeps track of previous button state to detect transitions
    
    dummy_bool = BoolProperty( name="DummyBool", default=True )
    dummy_string = StringProperty( name="DummyString", default=" " )
    dummy_float = FloatProperty ( name="DummyFloat", default=12.34 )

    def remove_properties ( self, context ):
        print ( "Removing all CellBlender Main Panel Properties... no collections to remove." )

    
    def select_callback ( self, context ):
        """
        Desired Logic:
          pin_state 0->1 with no others selected:
            Show All
          pin_state 0->1 with just 1 selected:
            No Change (continue showing the currently selected, and allow more)
          pin_state 0->1 with more than 1 selected ... should NOT happen because only one panel should show when pin_state is 0
            Illegal state
          pin_state 1->0 :
            Hide all panels ... always
            
        """
        prop_keys = [ 'preferences_select', 'settings_select', 'parameters_select', 'reaction_select', 'molecule_select', 'placement_select', 'objects_select', 'surf_classes_select', 'surf_regions_select', 'rel_patterns_select', 'partitions_select', 'init_select', 'graph_select', 'viz_select', 'select_multiple' ]
        
        pin_state = False
        
        """
        try:
            pin_state = (self['select_multiple'] != 0)
        except:
            pass
        old_pin_state = (self.last_state[prop_keys.index('select_multiple')] != 0)
        """

        if self.get('select_multiple'):
            pin_state = (self['select_multiple'] != 0)
        old_pin_state = (self.last_state[prop_keys.index('select_multiple')] != 0)
        
        print ( "Select Called without try/except with pin state:" + str(pin_state) + ", and old pin state = " + str(old_pin_state) )

        if (old_pin_state and (not pin_state)):
            # Pin has been removed, so hide all panels ... always
            # print ("Hiding all")
            for k in prop_keys:
                self.last_state[prop_keys.index(k)] = False
                self[k] = 0
                """
                try:
                    self.last_state[prop_keys.index(k)] = False
                    self[k] = 0
                except:
                    pass
                """
            self.last_state[prop_keys.index('select_multiple')] = False
            
        elif ((not old_pin_state) and pin_state):
            # Pin has been pushed
            # Find out how many panels are currently shown
            num_panels_shown = 0
            for k in prop_keys:
                if k != 'select_multiple':
                    if self.get(k):
                        if self[k] != 0:
                            num_panels_shown += 1
                    """
                    try:
                        if self[k] != 0:
                            num_panels_shown += 1
                    except:
                        pass
                    """
            # Check for case where no panels are showing
            if num_panels_shown == 0:
                # print ("Showing all")
                # Show all panels
                for k in prop_keys:
                    if self.get(k):
                        self[k] = 1
                        self.last_state[prop_keys.index(k)] = False
                    """
                    try:
                        self[k] = 1
                        self.last_state[prop_keys.index(k)] = False
                    except:
                        pass
                    """
        
            self.last_state[prop_keys.index('select_multiple')] = True
        
        else:
            # Pin state has not changed, so assume some other button has been toggled

            # Go through and find which one has changed to positive, setting all others to 0 if not pin_state
            for k in prop_keys:
                if self.get(k):
                    # print ( "Key " + k + " is " + str(self[k]) + ", Last state = " + str(self.last_state[index]) )
                    if (self[k] != 0) and (self.last_state[prop_keys.index(k)] == False):
                        self.last_state[prop_keys.index(k)] = True
                    else:
                        if not pin_state:
                            self.last_state[prop_keys.index(k)] = False
                            self[k] = 0
                """
                try:
                    if (self[k] != 0) and (self.last_state[prop_keys.index(k)] == False):
                        self.last_state[prop_keys.index(k)] = True
                    else:
                        if not pin_state:
                            self.last_state[prop_keys.index(k)] = False
                            self[k] = 0
                except:
                    pass
                """


    def draw_self (self, context, layout):
        # print ( "Top of CellBlenderMainPanelPropertyGroup.draw_self" )

        #######################################################################################
        """
        #######################################################################################
        def draw_panel_code_worked_out_with_Tom_on_Feb_18_2015:
            if not scn.mcell.get('CB_ID'):
                # This .blend file has no CellBlender data or was created with CellBlender RC3
                if not scn.mcell['initialized']:
                    # This .blend file has no CellBlender data (never saved with CellBlender enabled)
                    display "Initialize"
                else:
                    # This is a CellBlender RC3 or RC4 file
                    display "Update"
            else:
                # This is a CellBlender .blend file >= 1.0
                CB_ID = scn.mcell['CB_ID']
                if CB_ID != cb.cellblender_source_info['cb_src_sha1']
                    display "Update"
                else:
                    display normal panel
        #######################################################################################
        """
        #######################################################################################

        mcell = context.scene.mcell
        
        if not mcell.get ( 'saved_by_source_id' ):
            # This .blend file has no CellBlender data at all or was created with CellBlender RC3 / RC4
            if not mcell.initialized:  # if not mcell['initialized']:
                # This .blend file has no CellBlender data (never saved with CellBlender enabled)
                mcell.draw_uninitialized ( layout )
            else:
                # This is a CellBlender RC3 or RC4 file so draw the RC3/4 upgrade button
                row = layout.row()
                row.label ( "Blend File version (RC3/4) doesn't match CellBlender version", icon='ERROR' )
                row = layout.row()
                row.operator ( "mcell.upgraderc3", text="Upgrade RC3/4 Blend File to Current Version", icon='RADIO' )
        else:
            CB_ID = mcell['saved_by_source_id']
            source_id = cellblender.cellblender_info['cellblender_source_sha1']

            if CB_ID != source_id:
                # This is a CellBlender file >= 1.0, so draw the normal upgrade button
                row = layout.row()
                row.label ( "Blend File version doesn't match CellBlender version", icon='ERROR' )
                row = layout.row()
                row.operator ( "mcell.upgrade", text="Upgrade Blend File to Current Version", icon='RADIO' )

            else:
                # The versions matched, so draw the normal panels

                if not mcell.cellblender_preferences.use_long_menus:

                    # Draw all the selection buttons in a single row

                    real_row = layout.row()
                    split = real_row.split(0.9)
                    col = split.column()

                    #row = layout.row(align=True)
                    row = col.row(align=True)

                    if mcell.cellblender_preferences.show_button_num[0]: row.prop ( self, "preferences_select", icon='PREFERENCES' )
                    if mcell.cellblender_preferences.show_button_num[1]: row.prop ( self, "settings_select", icon='SETTINGS' )
                    if mcell.cellblender_preferences.show_button_num[2]: row.prop ( self, "parameters_select", icon='SEQ_SEQUENCER' )

                    if mcell.cellblender_preferences.use_stock_icons:
                        # Use "stock" icons to check on drawing speed problem
                        if mcell.cellblender_preferences.show_button_num[3]: row.prop ( self, "molecule_select", icon='FORCE_LENNARDJONES' )
                        if mcell.cellblender_preferences.show_button_num[4]: row.prop ( self, "reaction_select", icon='ARROW_LEFTRIGHT' )
                    else:
                        if self.molecule_select:
                            if mcell.cellblender_preferences.show_button_num[3]: molecule_img_sel = bpy.data.images.get('mol_s')
                            if mcell.cellblender_preferences.show_button_num[3]: mol_s = layout.icon(molecule_img_sel)
                            if mcell.cellblender_preferences.show_button_num[3]: row.prop ( self, "molecule_select", icon_value=mol_s )
                        else:
                            if mcell.cellblender_preferences.show_button_num[3]: molecule_img_unsel = bpy.data.images.get('mol_u')
                            if mcell.cellblender_preferences.show_button_num[3]: mol_u = layout.icon(molecule_img_unsel)
                            if mcell.cellblender_preferences.show_button_num[3]: row.prop ( self, "molecule_select", icon_value=mol_u )

                        if self.reaction_select:
                            if mcell.cellblender_preferences.show_button_num[4]: react_img_sel = bpy.data.images.get('reaction_s')
                            if mcell.cellblender_preferences.show_button_num[4]: reaction_s = layout.icon(react_img_sel)
                            if mcell.cellblender_preferences.show_button_num[4]: row.prop ( self, "reaction_select", icon_value=reaction_s )
                        else:
                            if mcell.cellblender_preferences.show_button_num[4]: react_img_unsel = bpy.data.images.get('reaction_u')
                            if mcell.cellblender_preferences.show_button_num[4]: reaction_u = layout.icon(react_img_unsel)
                            if mcell.cellblender_preferences.show_button_num[4]: row.prop ( self, "reaction_select", icon_value=reaction_u )

                    if mcell.cellblender_preferences.show_button_num[5]: row.prop ( self, "placement_select", icon='GROUP_VERTEX' )
                    if mcell.cellblender_preferences.show_button_num[6]: row.prop ( self, "rel_patterns_select", icon='TIME' )
                    if mcell.cellblender_preferences.show_button_num[7]: row.prop ( self, "objects_select", icon='MESH_ICOSPHERE' )  # Or 'MESH_CUBE'
                    if mcell.cellblender_preferences.show_button_num[8]: row.prop ( self, "surf_classes_select", icon='FACESEL_HLT' )
                    if mcell.cellblender_preferences.show_button_num[9]: row.prop ( self, "surf_regions_select", icon='SNAP_FACE' )
                    if mcell.cellblender_preferences.show_button_num[10]: row.prop ( self, "partitions_select", icon='GRID' )
                    if mcell.cellblender_preferences.show_button_num[11]: row.prop ( self, "graph_select", icon='FCURVE' )
                    if mcell.cellblender_preferences.show_button_num[12]: row.prop ( self, "viz_select", icon='SEQUENCE' )
                    if mcell.cellblender_preferences.show_button_num[13]: row.prop ( self, "init_select", icon='COLOR_RED' )

                    col = split.column()
                    row = col.row()

                    if self.select_multiple:
                        if mcell.cellblender_preferences.show_button_num[0]: row.prop ( self, "select_multiple", icon='PINNED' )
                    else:
                        if mcell.cellblender_preferences.show_button_num[0]: row.prop ( self, "select_multiple", icon='UNPINNED' )

                    # Use an operator rather than a property to make it an action button
                    # row.prop ( self, "reload_viz", icon='FILE_REFRESH' )
                    if mcell.cellblender_preferences.show_button_num[0]: row.operator ( "cbm.refresh_operator",text="",icon='FILE_REFRESH')
                        
                else:


                    current_marker = "Before drawing any buttons"

                    # Draw all the selection buttons with labels in 2 columns:

                    brow = layout.row()
                    bcol = brow.column()
                    bcol.prop ( self, "preferences_select", icon='PREFERENCES', text="Preferences" )
                    bcol = brow.column()
                    bcol.prop ( self, "settings_select", icon='SETTINGS', text="Settings" )

                    current_marker = "After drawing preferences_select"

                    brow = layout.row()
                    bcol = brow.column()
                    bcol.prop ( self, "parameters_select", icon='SEQ_SEQUENCER', text="Parameters" )
                    bcol = brow.column()
                    
                    current_marker = "After drawing parameters_select"


                    if mcell.cellblender_preferences.use_stock_icons:
                        # Use "stock" icons to check on drawing speed problem
                        bcol.prop ( self, "molecule_select", icon='FORCE_LENNARDJONES', text="Molecules" )
                        brow = layout.row()
                        bcol = brow.column()
                        bcol.prop ( self, "reaction_select", icon='ARROW_LEFTRIGHT', text="Reactions" )
                    else:
                        # Use custom icons for some buttons
                        if self.molecule_select:
                            if mcell.cellblender_preferences.use_stock_icons:
                                # Use "stock" icons to check on drawing speed problem
                                bcol.prop ( self, "reaction_select", icon='FORCE_LENNARDJONES', text="Molecules" )
                            else:
                                molecule_img_sel = bpy.data.images.get('mol_s')
                                mol_s = layout.icon(molecule_img_sel)
                                bcol.prop ( self, "molecule_select", icon_value=mol_s, text="Molecules" )
                        else:
                            if mcell.cellblender_preferences.use_stock_icons:
                                # Use "stock" icons to check on drawing speed problem
                                bcol.prop ( self, "reaction_select", icon='FORCE_LENNARDJONES', text="Molecules" )
                            else:
                                molecule_img_unsel = bpy.data.images.get('mol_u')
                                mol_u = layout.icon(molecule_img_unsel)
                                bcol.prop ( self, "molecule_select", icon_value=mol_u, text="Molecules" )

                        brow = layout.row()
                        bcol = brow.column()
                        if self.reaction_select:
                            if mcell.cellblender_preferences.use_stock_icons:
                                # Use "stock" icons to check on drawing speed problem
                                bcol.prop ( self, "reaction_select", icon='ARROW_LEFTRIGHT', text="Reactions" )
                            else:
                                react_img_sel = bpy.data.images.get('reaction_s')
                                reaction_s = layout.icon(react_img_sel)
                                bcol.prop ( self, "reaction_select", icon_value=reaction_s, text="Reactions" )
                        else:
                            if mcell.cellblender_preferences.use_stock_icons:
                                # Use "stock" icons to check on drawing speed problem
                                bcol.prop ( self, "reaction_select", icon='ARROW_LEFTRIGHT', text="Reactions" )
                            else:
                                react_img_unsel = bpy.data.images.get('reaction_u')
                                reaction_u = layout.icon(react_img_unsel)
                                bcol.prop ( self, "reaction_select", icon_value=reaction_u, text="Reactions" )


                    current_marker = "After drawing molecules and reactions"


                    ## Drawing is fast when exiting here

                    bcol = brow.column()
                    bcol.prop ( self, "placement_select", icon='GROUP_VERTEX', text=" Molecule Placement" )

                    current_marker = "After drawing placement_select"
                    ## Drawing is a little slower when exiting here


                    brow = layout.row()
                    bcol = brow.column()
                    bcol.prop ( self, "rel_patterns_select", icon='TIME', text="Release Patterns" )
                    bcol = brow.column()
                    bcol.prop ( self, "objects_select", icon='MESH_ICOSPHERE', text="Model Objects" )

                    current_marker = "After drawing release patterns"

                    brow = layout.row()
                    bcol = brow.column()
                    bcol.prop ( self, "surf_classes_select", icon='FACESEL_HLT', text="Surface Classes" )
                    bcol = brow.column()
                    bcol.prop ( self, "surf_regions_select", icon='SNAP_FACE', text="Assign Surface Classes" )
                    

                    current_marker = "After drawing surface selections"


                    ## Drawing is slower when exiting here


                    brow = layout.row()
                    bcol = brow.column()
                    bcol.prop ( self, "partitions_select", icon='GRID', text="Partitions" )
                    bcol = brow.column()
                    bcol.prop ( self, "graph_select", icon='FCURVE', text="Plot Output Settings" )


                    current_marker = "After drawing partition and graph buttons"


                    brow = layout.row()
                    bcol = brow.column()
                    bcol.prop ( self, "viz_select", icon='SEQUENCE', text="Visualization Settings" )
                    bcol = brow.column()
                    bcol.prop ( self, "init_select", icon='COLOR_RED', text="Run Simulation" )


                    current_marker = "After drawing the viz and run buttons buttons"




                    ############################################
                    ############################################
                    #print ( "Exiting ... " + current_marker )
                    #return
                    ############################################
                    ############################################



                    brow = layout.row()
                    bcol = brow.column()
                    if self.select_multiple:
                        bcol.prop ( self, "select_multiple", icon='PINNED', text="Show All / Multiple" )
                    else:
                        bcol.prop ( self, "select_multiple", icon='UNPINNED', text="Show All / Multiple" )
                    bcol = brow.column()
                    bcol.operator ( "cbm.refresh_operator",icon='FILE_REFRESH', text="Reload Visualization Data")



                current_marker = "After drawing all buttons"



                # Draw each panel only if it is selected

                if self.preferences_select:
                    layout.box() # Use as a separator
                    layout.label ( "Preferences", icon='PREFERENCES' )
                    context.scene.mcell.cellblender_preferences.draw_layout ( context, layout )

                if self.settings_select:
                    layout.box() # Use as a separator
                    layout.label ( "Project Settings", icon='SETTINGS' )
                    context.scene.mcell.project_settings.draw_layout ( context, layout )

                if self.parameters_select:
                    layout.box() # Use as a separator
                    layout.label ( "Model Parameters", icon='SEQ_SEQUENCER' )
                    context.scene.mcell.parameter_system.draw_layout ( context, layout )

                if self.molecule_select:
                    layout.box() # Use as a separator
                    layout.label(text="Defined Molecules", icon='FORCE_LENNARDJONES')
                    context.scene.mcell.molecules.draw_layout ( context, layout )

                if self.reaction_select:
                    layout.box() # Use as a separator
                    if mcell.cellblender_preferences.use_stock_icons:
                        # Use "stock" icons to check on drawing speed problem
                        layout.label ( "Defined Reactions", icon='ARROW_LEFTRIGHT' )
                    else:
                        react_img_sel = bpy.data.images.get('reaction_s')
                        reaction_s = layout.icon(react_img_sel)
                        layout.label ( "Defined Reactions", icon_value=reaction_s )
                    context.scene.mcell.reactions.draw_layout ( context, layout )

                if self.placement_select:
                    layout.box() # Use as a separator
                    layout.label ( "Molecule Release/Placement", icon='GROUP_VERTEX' )
                    context.scene.mcell.release_sites.draw_layout ( context, layout )

                if self.rel_patterns_select:
                    layout.box() # Use as a separator
                    layout.label ( "Release Patterns", icon='TIME' )
                    context.scene.mcell.release_patterns.draw_layout ( context, layout )

                if self.objects_select:
                    layout.box() # Use as a separator
                    layout.label ( "Model Objects", icon='MESH_ICOSPHERE' )  # Or 'MESH_CUBE'
                    context.scene.mcell.model_objects.draw_layout ( context, layout )
                    # layout.box() # Use as a separator
                    if context.object != None:
                        context.object.mcell.regions.draw_layout(context, layout)

                if self.surf_classes_select:
                    layout.box() # Use as a separator
                    layout.label ( "Defined Surface Classes", icon='FACESEL_HLT' )
                    context.scene.mcell.surface_classes.draw_layout ( context, layout )

                if self.surf_regions_select:
                    layout.box() # Use as a separator
                    layout.label ( "Assigned Surface Classes", icon='SNAP_FACE' )
                    context.scene.mcell.mod_surf_regions.draw_layout ( context, layout )

                if self.partitions_select:
                    layout.box() # Use as a separator
                    layout.label ( "Partitions", icon='GRID' )
                    context.scene.mcell.partitions.draw_layout ( context, layout )

                if self.graph_select:
                    layout.box() # Use as a separator
                    layout.label ( "Reaction Data Output", icon='FCURVE' )
                    context.scene.mcell.rxn_output.draw_layout ( context, layout )

                #if self.mol_viz_select:
                #    layout.box()
                #    layout.label ( "Visualization Output Settings", icon='SEQUENCE' )
                #    context.scene.mcell.mol_viz.draw_layout ( context, layout )
                    
                if self.viz_select:
                    layout.box()
                    layout.label ( "Visualization", icon='SEQUENCE' )
                    context.scene.mcell.viz_output.draw_layout ( context, layout )
                    context.scene.mcell.mol_viz.draw_layout ( context, layout )
                    
                if self.init_select:
                    layout.box() # Use as a separator
                    layout.label ( "Run Simulation", icon='COLOR_RED' )
                    context.scene.mcell.initialization.draw_layout ( context, layout )
                    
                #if self.run_select:
                #    layout.box() # Use as a separator
                #    layout.label ( "Run Simulation", icon='COLOR_RED' )
                #    context.scene.mcell.run_simulation.draw_layout ( context, layout )
                    
                # The reload_viz button refreshes rather than brings up a panel
                #if self.reload_viz:
                #    layout.box()
                #    layout.label ( "Reload Simulation Data", icon='FILE_REFRESH' )
        # print ( "Bottom of CellBlenderMainPanelPropertyGroup.draw_self" )


import pickle

# Main MCell (CellBlender) Properties Class:
def refresh_source_id_callback ( self, context ):
    # This is a boolean which defaults to false. So clicking it should change it to true which triggers this callback:
    if self.refresh_source_id:
        print ("Updating ID")
        if not ('cellblender_source_id_from_file' in cellblender.cellblender_info):
            # Save the version that was read from the file
            cellblender.cellblender_info.update ( { "cellblender_source_id_from_file": cellblender.cellblender_info['cellblender_source_sha1'] } )
        # Compute the new version
        cellblender.cellblender_source_info.identify_source_version(os.path.dirname(__file__),verbose=True)
        # Check to see if they match
        if cellblender.cellblender_info['cellblender_source_sha1'] == cellblender.cellblender_info['cellblender_source_id_from_file']:
            # They still match, so remove the "from file" version from the info to let the panel know that there's no longer a mismatch:
            cellblender.cellblender_info.pop('cellblender_source_id_from_file')
        # Setting this to false will redraw the panel
        self.refresh_source_id = False



class MCellPropertyGroup(bpy.types.PropertyGroup):
    initialized = BoolProperty(name="Initialized", default=False)
    # versions_match = BoolProperty ( default=True )

    cellblender_version = StringProperty(name="CellBlender Version", default="0")
    cellblender_addon_id = StringProperty(name="CellBlender Addon ID", default="0")
    cellblender_data_model_version = StringProperty(name="CellBlender Data Model Version", default="0")
    refresh_source_id = BoolProperty ( default=False, description="Recompute the Source ID from actual files", update=refresh_source_id_callback )
    #cellblender_source_hash = StringProperty(
    #    name="CellBlender Source Hash", default="unknown")


    cellblender_main_panel = PointerProperty(
        type=CellBlenderMainPanelPropertyGroup,
        name="CellBlender Main Panel")


    cellblender_preferences = PointerProperty(
        type=cellblender_preferences.CellBlenderPreferencesPropertyGroup,
        name="CellBlender Preferences")
    project_settings = PointerProperty(
        type=MCellProjectPropertyGroup, name="CellBlender Project Settings")
    export_project = PointerProperty(
        type=MCellExportProjectPropertyGroup, name="Export Simulation")
    run_simulation = PointerProperty(
        type=MCellRunSimulationPropertyGroup, name="Run Simulation")
    mol_viz = PointerProperty(
        type=MCellMolVizPropertyGroup, name="Mol Viz Settings")
    initialization = PointerProperty(
        type=cellblender_initialization.MCellInitializationPropertyGroup, name="Model Initialization")
    partitions = bpy.props.PointerProperty(
        type=cellblender_partitions.MCellPartitionsPropertyGroup, name="Partitions")
    ############# DB: added for parameter import from BNG, SBML models####
    #parameters = PointerProperty(
    #    type=MCellParametersPropertyGroup, name="Defined Parameters")
    parameter_system = PointerProperty(
        type=parameter_system.ParameterSystemPropertyGroup, name="Parameter System")
    molecules = PointerProperty(
        type=cellblender_molecules.MCellMoleculesListProperty, name="Defined Molecules")
    reactions = PointerProperty(
        type=cellblender_reactions.MCellReactionsListProperty, name="Defined Reactions")
    surface_classes = PointerProperty(
        type=cellblender_surface_classes.MCellSurfaceClassesPropertyGroup, name="Defined Surface Classes")
    mod_surf_regions = PointerProperty(
        type=MCellModSurfRegionsPropertyGroup, name="Assign Surface Classes")
    release_patterns = PointerProperty(
        type=cellblender_release.MCellReleasePatternPropertyGroup, name="Defined Release Patterns")
    release_sites = PointerProperty(
        type=cellblender_release.MCellMoleculeReleasePropertyGroup, name="Defined Release Sites")
    model_objects = PointerProperty(
        type=MCellModelObjectsPropertyGroup, name="Instantiated Objects")
    viz_output = PointerProperty(
        type=MCellVizOutputPropertyGroup, name="Viz Output")
    rxn_output = PointerProperty(
        type=cellblender_reaction_output.MCellReactionOutputPropertyGroup, name="Reaction Output")
    meshalyzer = PointerProperty(
        type=MCellMeshalyzerPropertyGroup, name="CellBlender Project Settings")
    object_selector = PointerProperty(
        type=MCellObjectSelectorPropertyGroup,
        name="CellBlender Project Settings")
    molecule_glyphs = PointerProperty(
        type=MCellMoleculeGlyphsPropertyGroup, name="Molecule Shapes")

    #scratch_settings = PointerProperty(
    #    type=MCellScratchPropertyGroup, name="CellBlender Scratch Settings")

    def init_properties ( self ):
        self.cellblender_version = "0.1.54"
        self.cellblender_addon_id = "0"
        self.cellblender_data_model_version = "0"
        self.parameter_system.init_properties()
        self.initialization.init_properties ( self.parameter_system )
        self.molecules.init_properties ( self.parameter_system )
        # Don't forget to update the "saved_by_source_id" to match the current version of the addon
        self['saved_by_source_id'] = cellblender.cellblender_info['cellblender_source_sha1']
        self.initialized = True


    def remove_properties ( self, context ):
        print ( "Removing all MCell Properties..." )
        self.molecule_glyphs.remove_properties(context)
        self.object_selector.remove_properties(context)
        self.meshalyzer.remove_properties(context)
        self.rxn_output.remove_properties(context)
        self.viz_output.remove_properties(context)
        self.model_objects.remove_properties(context)
        self.release_sites.remove_properties(context)
        self.release_patterns.remove_properties(context)
        self.mod_surf_regions.remove_properties(context)
        self.surface_classes.remove_properties(context)
        self.reactions.remove_properties(context)
        self.molecules.remove_properties(context)
        self.partitions.remove_properties(context)
        self.initialization.remove_properties(context)
        self.mol_viz.remove_properties(context)
        self.run_simulation.remove_properties(context)
        self.export_project.remove_properties(context)
        self.project_settings.remove_properties(context)
        self.cellblender_preferences.remove_properties(context)
        self.cellblender_main_panel.remove_properties(context)
        self.parameter_system.remove_properties(context)
        print ( "Done removing all MCell Properties." )



    def build_data_model_from_properties ( self, context, geometry=False ):
        print ( "build_data_model_from_properties: Constructing a data_model dictionary from current properties" )
        dm = {}
        dm['data_model_version'] = "DM_2014_10_24_1638"
        dm['blender_version'] = [v for v in bpy.app.version]
        dm['cellblender_version'] = self.cellblender_version
        #dm['cellblender_source_hash'] = self.cellblender_source_hash
        dm['cellblender_source_sha1'] = cellblender.cellblender_info["cellblender_source_sha1"]
        if 'api_version' in self:
            dm['api_version'] = self['api_version']
        else:
            dm['api_version'] = 0
        dm['parameter_system'] = self.parameter_system.build_data_model_from_properties(context)
        dm['initialization'] = self.initialization.build_data_model_from_properties(context)
        dm['initialization']['partitions'] = self.partitions.build_data_model_from_properties(context)
        dm['define_molecules'] = self.molecules.build_data_model_from_properties(context)
        dm['define_reactions'] = self.reactions.build_data_model_from_properties(context)
        dm['release_sites'] = self.release_sites.build_data_model_from_properties(context)
        dm['define_release_patterns'] = self.release_patterns.build_data_model_from_properties(context)
        dm['define_surface_classes'] = self.surface_classes.build_data_model_from_properties(context)
        dm['modify_surface_regions'] = self.mod_surf_regions.build_data_model_from_properties(context)
        dm['model_objects'] = self.model_objects.build_data_model_from_properties(context)
        dm['viz_output'] = self.viz_output.build_data_model_from_properties(context)
        dm['simulation_control'] = self.run_simulation.build_data_model_from_properties(context)
        dm['mol_viz'] = self.mol_viz.build_data_model_from_properties(context)
        dm['reaction_data_output'] = self.rxn_output.build_data_model_from_properties(context)
        if geometry:
            print ( "Adding Geometry to Data Model" )
            dm['geometrical_objects'] = self.model_objects.build_data_model_geometry_from_mesh(context)
            dm['materials'] = self.model_objects.build_data_model_materials_from_materials(context)
        return dm



    @staticmethod
    def upgrade_data_model ( dm ):
        # Upgrade the data model as needed. Return updated data model or None if it can't be upgraded.
        print ( "------------------------->>> Upgrading MCellPropertyGroup Data Model" )
        # cellblender.data_model.dump_data_model ( "Dump of dm passed to MCellPropertyGroup.upgrade_data_model", dm )

        # Perform any upgrades to this top level data model

        if not ('data_model_version' in dm):
            # Make changes to move from unversioned to DM_2014_10_24_1638
            dm['data_model_version'] = "DM_2014_10_24_1638"

        if dm['data_model_version'] != "DM_2014_10_24_1638":
            data_model.flag_incompatible_data_model ( "Error: Unable to upgrade MCellPropertyGroup data model to current version." )
            return None

        # Perform any upgrades to all components within this top level data model

        group_name = "parameter_system"
        if group_name in dm:
            dm[group_name] = parameter_system.ParameterSystemPropertyGroup.upgrade_data_model ( dm[group_name] )
            if dm[group_name] == None:
                return None

        group_name = "initialization"
        if group_name in dm:
            dm[group_name] = cellblender_initialization.MCellInitializationPropertyGroup.upgrade_data_model ( dm[group_name] )
            if dm[group_name] == None:
                return None

            subgroup_name = "partitions"
            if subgroup_name in dm[group_name]:
                dm[group_name][subgroup_name] = cellblender_partitions.MCellPartitionsPropertyGroup.upgrade_data_model ( dm[group_name] )
                if dm[group_name][subgroup_name] == None:
                    return None

        group_name = "define_molecules"
        if group_name in dm:
            dm[group_name] = cellblender_molecules.MCellMoleculesListProperty.upgrade_data_model ( dm[group_name] )
            if dm[group_name] == None:
                return None

        group_name = "define_reactions"
        if group_name in dm:
            dm[group_name] = cellblender_reactions.MCellReactionsListProperty.upgrade_data_model ( dm[group_name] )
            if dm[group_name] == None:
                return None

        group_name = "release_sites"
        if group_name in dm:
            dm[group_name] = cellblender_release.MCellMoleculeReleasePropertyGroup.upgrade_data_model ( dm[group_name] )
            if dm[group_name] == None:
                return None

        group_name = "define_release_patterns"
        if group_name in dm:
            dm[group_name] = cellblender_release.MCellReleasePatternPropertyGroup.upgrade_data_model ( dm[group_name] )
            if dm[group_name] == None:
                return None

        group_name = "define_surface_classes"
        if group_name in dm:
            dm[group_name] = cellblender_surface_classes.MCellSurfaceClassesPropertyGroup.upgrade_data_model ( dm[group_name] )
            if dm[group_name] == None:
                return None

        group_name = "modify_surface_regions"
        if group_name in dm:
            dm[group_name] = MCellModSurfRegionsPropertyGroup.upgrade_data_model ( dm[group_name] )
            if dm[group_name] == None:
                return None

        group_name = "model_objects"
        if group_name in dm:
            dm[group_name] = MCellModelObjectsPropertyGroup.upgrade_data_model ( dm[group_name] )
            if dm[group_name] == None:
                return None

        group_name = "viz_output"
        if group_name in dm:
            dm[group_name] = MCellVizOutputPropertyGroup.upgrade_data_model ( dm[group_name] )
            if dm[group_name] == None:
                return None

        group_name = "simulation_control"
        if group_name in dm:
            dm[group_name] = MCellRunSimulationPropertyGroup.upgrade_data_model ( dm[group_name] )
            if dm[group_name] == None:
                return None

        group_name = "mol_viz"
        if group_name in dm:
            dm[group_name] = MCellMolVizPropertyGroup.upgrade_data_model ( dm[group_name] )
            if dm[group_name] == None:
                return None

        group_name = "reaction_data_output"
        if group_name in dm:
            dm[group_name] = cellblender_reaction_output.MCellReactionOutputPropertyGroup.upgrade_data_model ( dm[group_name] )
            if dm[group_name] == None:
                return None

        return dm



    def build_properties_from_data_model ( self, context, dm, geometry=False ):
        print ( "build_properties_from_data_model: Data Model Keys = " + str(dm.keys()) )

        # Check that the data model version matches the version for this property group
        if dm['data_model_version'] != "DM_2014_10_24_1638":
            data_model.handle_incompatible_data_model ( "Error: Unable to upgrade MCellPropertyGroup data model to current version." )

        # Remove the existing MCell Property Tree
        self.remove_properties(context)

        # Now convert the updated Data Model into CellBlender Properties
        print ( "Overwriting properites based on data in the data model dictionary" )
        self.init_properties()
        if "parameter_system" in dm:
            print ( "Overwriting the parameter_system properties" )
            self.parameter_system.build_properties_from_data_model ( context, dm["parameter_system"] )
        
        if "initialization" in dm:
            print ( "Overwriting the initialization properties" )
            self.initialization.build_properties_from_data_model ( context, dm["initialization"] )
            if "partitions" in dm:
                print ( "Overwriting the partitions properties" )
                self.partitions.build_properties_from_data_model ( context, dm["initialization"]["partitions"] )
        if "define_molecules" in dm:
            print ( "Overwriting the define_molecules properties" )
            self.molecules.build_properties_from_data_model ( context, dm["define_molecules"] )
        if "define_reactions" in dm:
            print ( "Overwriting the define_reactions properties" )
            self.reactions.build_properties_from_data_model ( context, dm["define_reactions"] )
        if "release_sites" in dm:
            print ( "Overwriting the release_sites properties" )
            self.release_sites.build_properties_from_data_model ( context, dm["release_sites"] )
        if "define_release_patterns" in dm:
            print ( "Overwriting the define_release_patterns properties" )
            self.release_patterns.build_properties_from_data_model ( context, dm["define_release_patterns"] )
        if "define_surface_classes" in dm:
            print ( "Overwriting the define_surface_classes properties" )
            self.surface_classes.build_properties_from_data_model ( context, dm["define_surface_classes"] )
        # Move below model objects?
        #if "modify_surface_regions" in dm:
        #    print ( "Overwriting the modify_surface_regions properties" )
        #    self.mod_surf_regions.build_properties_from_data_model ( context, dm["modify_surface_regions"] )
        if geometry:
            print ( "Deleting all mesh objects" )
            self.model_objects.delete_all_mesh_objects(context)
            if "materials" in dm:
                print ( "Overwriting the materials properties" )
                print ( "Building Materials from Data Model Materials" )
                self.model_objects.build_materials_from_data_model_materials ( context, dm['materials'] )
            if "geometrical_objects" in dm:
                print ( "Overwriting the geometrical_objects properties" )
                print ( "Building Mesh Geometry from Data Model Geometry" )
                self.model_objects.build_mesh_from_data_model_geometry ( context, dm["geometrical_objects"] )
            print ( "Not fully implemented yet!!!!" )
        if "model_objects" in dm:
            print ( "Overwriting the model_objects properties" )
            self.model_objects.build_properties_from_data_model ( context, dm["model_objects"] )
        if "modify_surface_regions" in dm:
            print ( "Overwriting the modify_surface_regions properties" )
            self.mod_surf_regions.build_properties_from_data_model ( context, dm["modify_surface_regions"] )
        if "viz_output" in dm:
            print ( "Overwriting the viz_output properties" )
            self.viz_output.build_properties_from_data_model ( context, dm["viz_output"] )
        if "mol_viz" in dm:
            print ( "Overwriting the mol_viz properties" )
            self.mol_viz.build_properties_from_data_model ( context, dm["mol_viz"] )
        # This is commented out because it's not clear how it should work yet...
        #if "simulation_control" in dm:
        #    print ( "Overwriting the simulation_control properties" )
        #    self.run_simulation.build_properties_from_data_model ( context, dm["simulation_control"] )
        if "reaction_data_output" in dm:
            print ( "Overwriting the reaction_data_output properties" )
            self.rxn_output.build_properties_from_data_model ( context, dm["reaction_data_output"] )


        # Now call the various "check" routines to clean up any unresolved references
        print ( "Checking the initialization and partitions properties" )
        self.initialization.check_properties_after_building ( context )
        self.partitions.check_properties_after_building ( context )
        print ( "Checking the define_molecules properties" )
        self.molecules.check_properties_after_building ( context )
        print ( "Checking the define_reactions properties" )
        self.reactions.check_properties_after_building ( context )
        print ( "Checking the release_sites properties" )
        self.release_sites.check_properties_after_building ( context )
        print ( "Checking the define_release_patterns properties" )
        self.release_patterns.check_properties_after_building ( context )
        print ( "Checking the define_surface_classes properties" )
        self.surface_classes.check_properties_after_building ( context )
        print ( "Checking the modify_surface_regions properties" )
        self.mod_surf_regions.check_properties_after_building ( context )
        print ( "Checking all mesh objects" )
        self.model_objects.check_properties_after_building ( context )
        print ( "Checking the viz_output properties" )
        self.viz_output.check_properties_after_building ( context )
        print ( "Checking the mol_viz properties" )
        self.mol_viz.check_properties_after_building ( context )
        print ( "Checking the reaction_data_output properties" )
        self.rxn_output.check_properties_after_building ( context )
        print ( "Checking/Updating the model_objects properties" )
        cellblender_operators.model_objects_update(context)

        print ( "Done building properties from the data model." )
        


    def draw_uninitialized ( self, layout ):
        row = layout.row()
        row.operator("mcell.init_cellblender", text="Initialize CellBlender")




    def print_id_property_tree ( self, obj, name, depth ):
        """ Recursive routine that prints an ID Property Tree """
        depth = depth + 1
        indent = "".join([ '  ' for x in range(depth) ])
        print ( indent + "Depth="+str(depth) )
        print ( indent + "print_ID_property_tree() called with \"" + name + "\" of type " + str(type(obj)) )
        if "'IDPropertyGroup'" in str(type(obj)):
            print ( indent + "This is an ID property group: " + name )
            for k in obj.keys():
                self.print_id_property_tree ( obj[k], k, depth )
        elif "'list'" in str(type(obj)):
            print ( indent + "This is a list: " + name )
            i = 0
            for k in obj:
                self.print_id_property_tree ( k, name + '['+str(i)+']', depth )
                i += 1
        else:
            print ( indent + "This is NOT an ID property group: " + name + " = " + str(obj) )

        depth = depth - 1
        return




    #################### Special RC3 Code Below ####################

    def RC3_add_from_ID_panel_parameter ( self, dm_dict, dm_name, prop_dict, prop_name, panel_param_list ):
        dm_dict[dm_name] = [ x for x in panel_param_list if x['name'] == prop_dict[prop_name]['unique_static_name'] ] [0] ['expr']

    def RC3_add_from_ID_string ( self, dm_dict, dm_name, prop_dict, prop_name, default_value ):
        if prop_dict.get(prop_name):
          dm_dict[dm_name] = prop_dict[prop_name]
        else:
          dm_dict[dm_name] = default_value

    def RC3_add_from_ID_float ( self, dm_dict, dm_name, prop_dict, prop_name, default_value ):
        if prop_dict.get(prop_name):
          dm_dict[dm_name] = prop_dict[prop_name]
        else:
          dm_dict[dm_name] = default_value

    def RC3_add_from_ID_int ( self, dm_dict, dm_name, prop_dict, prop_name, default_value ):
        if prop_dict.get(prop_name):
          dm_dict[dm_name] = prop_dict[prop_name]
        else:
          dm_dict[dm_name] = default_value

    def RC3_add_from_ID_floatstr ( self, dm_dict, dm_name, prop_dict, prop_name, default_value ):
        if prop_dict.get(prop_name):
          dm_dict[dm_name] = str(prop_dict[prop_name])
        else:
          dm_dict[dm_name] = str(default_value)

    def RC3_add_from_ID_boolean ( self, dm_dict, dm_name, prop_dict, prop_name, default_value ):
        if prop_dict.get(prop_name):
          dm_dict[dm_name] = ( prop_dict[prop_name] != 0 )
        else:
          dm_dict[dm_name] = default_value

    def RC3_add_from_ID_enum ( self, dm_dict, dm_name, prop_dict, prop_name, default_value, enum_list ):
        if prop_dict.get(prop_name):
          dm_dict[dm_name] = enum_list[int(prop_dict[prop_name])]
        else:
          dm_dict[dm_name] = default_value

    def build_data_model_from_RC3_ID_properties ( self, context, geometry=False ):
        # Build an unversioned data model from RC3 ID properties to match the pre-versioned data models that can be upgraded to versioned data models

        print ( "build_data_model_from_RC3_ID_properties: Constructing a data_model dictionary from RC3 ID properties" )
        print ( "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" )
        print ( "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" )
        print ( "!!!!!!!!!!!!!! THIS MAY NOT WORK YET !!!!!!!!!!!!!!!!" )
        print ( "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" )
        print ( "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" )

        dm = None

        # Remove the RNA properties overlaying the ID Property 'mcell'
        del bpy.types.Scene.mcell
        
        mcell = context.scene.get('mcell')
        if mcell != None:

          # There's an mcell in the scene
          dm = {}
          

          # Build the parameter system first
          par_sys = mcell.get('parameter_system')
          if par_sys != None:
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )
            print ( "There's a parameter system" )
            # There's a parameter system
            dm['parameter_system'] = {}
            dm_ps = dm['parameter_system']
            gpl = par_sys.get('general_parameter_list')
            if gpl != None:
              dm_ps['model_parameters'] = []
              dm_mp = dm_ps['model_parameters']
              if len(gpl) > 0:
                for gp in gpl:
                  print ( "Par name = " + str(gp['par_name']) )
                  dm_p = {}
                  dm_p['par_name'] = str(gp['par_name'])
                  dm_p['par_expression'] = str(gp['expr'])
                  dm_p['par_description'] = str(gp['descr'])
                  dm_p['par_units'] = str(gp['units'])
                  extras = {}
                  extras['par_id_name'] = str(gp['name'])
                  extras['par_valid'] = gp['isvalid'] != 0
                  extras['par_value'] = gp['value']
                  dm_p['extras'] = extras
                  dm_mp.append ( dm_p )

            print ( "Done parameter system" )
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )

          ppl = par_sys.get('panel_parameter_list')
          

          # Build the rest of the data model

          # Initialization

          init = mcell.get('initialization')
          if init != None:
            # dm['initialization'] = self.initialization.build_data_model_from_properties(context)
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )
            print ( "There is initialization" )

            # There is initialization
            dm['initialization'] = {}
            dm_init = dm['initialization']

            self.RC3_add_from_ID_panel_parameter ( dm_init, 'iterations',              init, 'iterations', ppl )
            self.RC3_add_from_ID_panel_parameter ( dm_init, 'time_step',               init, 'time_step',  ppl )
            self.RC3_add_from_ID_panel_parameter ( dm_init, 'time_step_max',           init, 'time_step_max', ppl )
            self.RC3_add_from_ID_panel_parameter ( dm_init, 'space_step',              init, 'space_step', ppl )
            self.RC3_add_from_ID_panel_parameter ( dm_init, 'interaction_radius',      init, 'interaction_radius', ppl )
            self.RC3_add_from_ID_panel_parameter ( dm_init, 'radial_directions',       init, 'radial_directions', ppl )
            self.RC3_add_from_ID_panel_parameter ( dm_init, 'radial_subdivisions',     init, 'radial_subdivisions', ppl )
            self.RC3_add_from_ID_panel_parameter ( dm_init, 'vacancy_search_distance', init, 'vacancy_search_distance', ppl )
            self.RC3_add_from_ID_panel_parameter ( dm_init, 'surface_grid_density',    init, 'surface_grid_density', ppl )

            self.RC3_add_from_ID_boolean ( dm_init, 'accurate_3d_reactions',     init, 'accurate_3d_reactions', True )
            self.RC3_add_from_ID_boolean ( dm_init, 'center_molecules_on_grid',  init, 'center_molecules_grid', False )


            if init.get('microscopic_reversibility'):
              dm_init['microscopic_reversibility'] = init['microscopic_reversibility']
            else:
              dm_init['microscopic_reversibility'] = 'OFF'

            # Notifications

            dm_init['notifications'] = {}
            dm_note = dm_init['notifications']
            if init.get('all_notifications'):
              dm_note['all_notifications'] = init['all_notifications']
            else:
              dm_note['all_notifications'] = 'INDIVIDUAL'

            if init.get('diffusion_constant_report'):
              dm_note['diffusion_constant_report'] = init['diffusion_constant_report']
            else:
              dm_note['diffusion_constant_report'] = 'BRIEF'

            if init.get('file_output_report'):
              dm_note['file_output_report'] = init['file_output_report'] != 0
            else:
              dm_note['file_output_report'] = False

            if init.get('final_summary'):
              dm_note['final_summary'] = init['final_summary'] != 0
            else:
              dm_note['final_summary'] = True

            if init.get('iteration_report'):
              dm_note['iteration_report'] = init['iteration_report'] != 0
            else:
              dm_note['iteration_report'] = True

            if init.get('partition_location_report'):
              dm_note['partition_location_report'] = init['partition_location_report'] != 0
            else:
              dm_note['partition_location_report'] = False

            if init.get('probability_report'):
              dm_note['probability_report'] = init['probability_report']
            else:
              dm_note['probability_report'] = 'ON'

            if init.get('probability_report_threshold'):
              dm_note['probability_report_threshold'] = init['probability_report_threshold']
            else:
              dm_note['probability_report_threshold'] = 0.0


            if init.get('varying_probability_report'):
              dm_note['varying_probability_report'] = init['varying_probability_report'] != 0
            else:
              dm_note['varying_probability_report'] = True

            if init.get('progress_report'):
              dm_note['progress_report'] = init['progress_report'] != 0
            else:
              dm_note['progress_report'] = True

            if init.get('release_event_report'):
              dm_note['release_event_report'] = init['release_event_report'] != 0
            else:
              dm_note['release_event_report'] = True

            if init.get('molecule_collision_report'):
              dm_note['molecule_collision_report'] = init['molecule_collision_report'] != 0
            else:
              dm_note['molecule_collision_report'] = False


            # Warnings

            dm_init['warnings'] = {}
            dm_warn = dm_init['warnings']

            if init.get('all_warnings'):
              dm_warn['all_warnings'] = init['all_warnings']
            else:
              dm_warn['all_warnings'] = 'INDIVIDUAL'

            if init.get('degenerate_polygons'):
              dm_warn['degenerate_polygons'] = init['degenerate_polygons']
            else:
              dm_warn['degenerate_polygons'] = 'WARNING'

            if init.get('high_reaction_probability'):
              dm_warn['high_reaction_probability'] = init['high_reaction_probability']
            else:
              dm_warn['high_reaction_probability'] = 'IGNORED'

            if init.get('high_probability_threshold'):
              dm_warn['high_probability_threshold'] = init['high_probability_threshold']
            else:
              dm_warn['high_probability_threshold'] = 1.0

            if init.get('lifetime_too_short'):
              dm_warn['lifetime_too_short'] = init['lifetime_too_short']
            else:
              dm_warn['lifetime_too_short'] = 'WARNING'

            if init.get('lifetime_threshold'):
              dm_warn['lifetime_threshold'] = init['lifetime_threshold']
            else:
              dm_warn['lifetime_threshold'] = 50

            if init.get('missed_reactions'):
              dm_warn['missed_reactions'] = init['missed_reactions']
            else:
              dm_warn['missed_reactions'] = 'WARNING'

            if init.get('missed_reaction_threshold'):
              dm_warn['missed_reaction_threshold'] = init['missed_reaction_threshold']
            else:
              dm_warn['missed_reaction_threshold'] = 0.001

            if init.get('negative_diffusion_constant'):
              dm_warn['negative_diffusion_constant'] = init['negative_diffusion_constant']
            else:
              dm_warn['negative_diffusion_constant'] = 'WARNING'

            if init.get('missing_surface_orientation'):
              dm_warn['missing_surface_orientation'] = init['missing_surface_orientation']
            else:
              dm_warn['missing_surface_orientation'] = 'ERROR'

            if init.get('negative_reaction_rate'):
              dm_warn['negative_reaction_rate'] = init['negative_reaction_rate']
            else:
              dm_warn['negative_reaction_rate'] = 'WARNING'

            if init.get('useless_volume_orientation'):
              dm_warn['useless_volume_orientation'] = init['useless_volume_orientation']
            else:
              dm_warn['useless_volume_orientation'] = 'WARNING'

            print ( "Done initialization" )
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )

          # Partitions

          parts = mcell.get('partitions')
          if parts != None:

            # dm['initialization']['partitions'] = self.partitions.build_data_model_from_properties(context)
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )
            print ( "There are partitions" )
            # There are partitions
            
            # Ensure that there is an initialization section in the data model that's being built
            dm_init = dm.get('initialization')
            if dm_init == None:
              dm['initialization'] = {}
              dm_init = dm['initialization']
            
            dm['initialization']['partitions'] = {}
            dm_parts = dm['initialization']['partitions']

            if parts.get('include'):
              dm_parts['include'] = ( parts['include'] != 0 )
            else:
              dm_parts['include'] = False

            if parts.get('recursion_flag'):
              dm_parts['recursion_flag'] = ( parts['recursion_flag'] != 0 )
            else:
              dm_parts['recursion_flag'] = False

            if parts.get('x_start'):
              dm_parts['x_start'] = parts['x_start']
            else:
              dm_parts['x_start'] = -1

            if parts.get('x_end'):
              dm_parts['x_end'] = parts['x_end']
            else:
              dm_parts['x_end'] = 1

            if parts.get('x_step'):
              dm_parts['x_step'] = parts['x_step']
            else:
              dm_parts['x_step'] = 0.02

            if parts.get('y_start'):
              dm_parts['y_start'] = parts['y_start']
            else:
              dm_parts['y_start'] = -1

            if parts.get('y_end'):
              dm_parts['y_end'] = parts['y_end']
            else:
              dm_parts['y_end'] = 1

            if parts.get('y_step'):
              dm_parts['y_step'] = parts['y_step']
            else:
              dm_parts['y_step'] = 0.02

            if parts.get('z_start'):
              dm_parts['z_start'] = parts['z_start']
            else:
              dm_parts['z_start'] = -1

            if parts.get('z_end'):
              dm_parts['z_end'] = parts['z_end']
            else:
              dm_parts['z_end'] = 1

            if parts.get('z_step'):
              dm_parts['z_step'] = parts['z_step']
            else:
              dm_parts['z_step'] = 0.02

            print ( "Done partitions" )
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )


          # Model Objects

          modobjs = mcell.get('model_objects')
          if modobjs != None:
            # dm['model_objects'] = self.model_objects.build_data_model_from_properties(context)
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )
            print ( "There are model objects" )
            # There are model objects
            dm['model_objects'] = {}
            dm_mo = dm['model_objects']
            mol = modobjs.get('object_list')
            if mol != None:
              print ( "There is a model_object_list" )
              dm_mo['model_object_list'] = []
              dm_ol = dm_mo['model_object_list']
              if len(mol) > 0:
                for o in mol:
                  print ( "Model Object name = " + str(o['name']) )
                  
                  dm_o = {}
                  
                  self.RC3_add_from_ID_string ( dm_o, 'name', o, 'name', "Object" )

                  dm_ol.append ( dm_o )

            print ( "Done model objects" )
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )


          # Molecules

          mols = mcell.get('molecules')
          if mols != None:
            # dm['define_molecules'] = self.molecules.build_data_model_from_properties(context)
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )
            print ( "There are molecules" )
            # There are molecules
            dm['define_molecules'] = {}
            dm_mols = dm['define_molecules']
            ml = mols.get('molecule_list')
            if ml != None:
              dm_mols['molecule_list'] = []
              dm_ml = dm_mols['molecule_list']
              if len(ml) > 0:
                for m in ml:
                  print ( "Mol name = " + str(m['name']) )

                  dm_m = {}

                  self.RC3_add_from_ID_string          ( dm_m, 'mol_name',           m, 'name',               "Molecule" )
                  self.RC3_add_from_ID_enum            ( dm_m, 'mol_type',           m, 'type',               "2D",      ["2D", "3D"] )
                  self.RC3_add_from_ID_boolean         ( dm_m, 'target_only',        m, 'target_only',        False )
                  self.RC3_add_from_ID_boolean         ( dm_m, 'export_viz',         m, 'export_viz',         False )
                  self.RC3_add_from_ID_panel_parameter ( dm_m, 'diffusion_constant', m, 'diffusion_constant', ppl )
                  self.RC3_add_from_ID_panel_parameter ( dm_m, 'custom_space_step',  m, 'custom_space_step',  ppl )
                  self.RC3_add_from_ID_panel_parameter ( dm_m, 'custom_time_step',   m, 'custom_time_step',   ppl )
                  dm_m['maximum_step_length'] = ""

                  dm_ml.append ( dm_m )

            print ( "Done molecules" )
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )


          # Reactions

          reacts = mcell.get('reactions')
          if reacts != None:
            # dm['define_reactions'] = self.reactions.build_data_model_from_properties(context)
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )
            print ( "There are reactions" )
            # There are reactions
            dm['define_reactions'] = {}
            dm_reacts = dm['define_reactions']
            rl = reacts.get('reaction_list')
            if rl != None:
              dm_reacts['reaction_list'] = []
              dm_rl = dm_reacts['reaction_list']
              if len(rl) > 0:
                for r in rl:
                  print ( "React name = " + str(r['name']) )
                  
                  dm_r = {}
                  
                  self.RC3_add_from_ID_string  ( dm_r, 'name',      r, 'name',      "The Reaction" )
                  self.RC3_add_from_ID_string  ( dm_r, 'rxn_name',  r, 'rxn_name',  "" )
                  self.RC3_add_from_ID_string  ( dm_r, 'reactants', r, 'reactants', "" )
                  self.RC3_add_from_ID_string  ( dm_r, 'products',  r, 'products',  "" )

                  self.RC3_add_from_ID_enum    ( dm_r, 'rxn_type',  r, 'type', "irreversible", ["irreversible", "reversible"] )

                  self.RC3_add_from_ID_boolean ( dm_r, 'variable_rate_switch', r, 'variable_rate_switch', False )
                  self.RC3_add_from_ID_string  ( dm_r, 'variable_rate',        r, 'variable_rate',        "" )
                  self.RC3_add_from_ID_boolean ( dm_r, 'variable_rate_valid',  r, 'variable_rate_valid',  False )

                  self.RC3_add_from_ID_panel_parameter ( dm_r, 'fwd_rate',  r, 'fwd_rate',  ppl )
                  self.RC3_add_from_ID_panel_parameter ( dm_r, 'bkwd_rate', r, 'bkwd_rate', ppl )

                  dm_rl.append ( dm_r )

            print ( "Done reactions" )
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )


          # Release Sites

          rels = mcell.get('release_sites')
          if rels != None:
            # dm['release_sites'] = self.release_sites.build_data_model_from_properties(context)
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )
            print ( "There are release sites" )
            # There are release sites
            dm['release_sites'] = {}
            dm_rel = dm['release_sites']
            rsl = rels.get('mol_release_list')
            if rsl != None:
              print ( "There is a mol_release_list" )
              dm_rel['release_site_list'] = []
              dm_rs = dm_rel['release_site_list']
              if len(rsl) > 0:
                for r in rsl:
                  print ( "Release Site name = " + str(r['name']) )
                  
                  dm_r = {}
                  
                  self.RC3_add_from_ID_string  ( dm_r, 'name',     r, 'name',     "Release_Site" )
                  self.RC3_add_from_ID_string  ( dm_r, 'molecule', r, 'molecule', "" )
                  self.RC3_add_from_ID_enum    ( dm_r, 'shape',    r, 'shape',    "CUBIC", ["CUBIC", "SPHERICAL", "SPHERICAL_SHELL", "OBJECT"] )
                  self.RC3_add_from_ID_enum    ( dm_r, 'orient',   r, 'orient',   "\'",    ["\'", ",", ";"] )
                  
                  self.RC3_add_from_ID_string  ( dm_r, 'object_expr', r, 'object_expr', "" )
                  
                  self.RC3_add_from_ID_panel_parameter ( dm_r, 'location_x',  r, 'location_x',  ppl )
                  self.RC3_add_from_ID_panel_parameter ( dm_r, 'location_y',  r, 'location_y',  ppl )
                  self.RC3_add_from_ID_panel_parameter ( dm_r, 'location_z',  r, 'location_z',  ppl )

                  self.RC3_add_from_ID_panel_parameter ( dm_r, 'site_diameter',        r, 'diameter',     ppl )
                  self.RC3_add_from_ID_panel_parameter ( dm_r, 'release_probability',  r, 'probability',  ppl )

                  self.RC3_add_from_ID_enum    ( dm_r, 'quantity_type', r, 'quantity_type', "NUMBER_TO_RELEASE", ["NUMBER_TO_RELEASE", "GAUSSIAN_RELEASE_NUMBER", "DENSITY"] )

                  self.RC3_add_from_ID_panel_parameter ( dm_r, 'quantity', r, 'quantity',  ppl )
                  self.RC3_add_from_ID_panel_parameter ( dm_r, 'stddev',   r, 'stddev',  ppl )

                  self.RC3_add_from_ID_string  ( dm_r, 'pattern', r, 'pattern', "" )

                  dm_rs.append ( dm_r )

            print ( "Done release sites" )
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )


          # Release Patterns

          relps = mcell.get('release_patterns')
          if relps != None:
            # dm['define_release_patterns'] = self.release_patterns.build_data_model_from_properties(context)
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )
            print ( "There are release patterns" )
            # There are release patterns
            dm['define_release_patterns'] = {}
            dm_relps = dm['define_release_patterns']
            rpl = relps.get('release_pattern_list')
            if rpl != None:
              print ( "There is a release_pattern_list" )
              dm_relps['release_pattern_list'] = []
              dm_rpl = dm_relps['release_pattern_list']
              if len(rpl) > 0:
                for r in rpl:
                  print ( "Release Pattern name = " + str(r['name']) )
                  
                  dm_r = {}
                  
                  self.RC3_add_from_ID_string  ( dm_r, 'name',     r, 'name',     "Release_Pattern" )
                  
                  self.RC3_add_from_ID_panel_parameter ( dm_r, 'delay',            r, 'delay',            ppl )
                  self.RC3_add_from_ID_panel_parameter ( dm_r, 'release_interval', r, 'release_interval', ppl )
                  self.RC3_add_from_ID_panel_parameter ( dm_r, 'train_duration',   r, 'train_duration',   ppl )
                  self.RC3_add_from_ID_panel_parameter ( dm_r, 'train_interval',   r, 'train_interval',   ppl )
                  self.RC3_add_from_ID_panel_parameter ( dm_r, 'number_of_trains', r, 'number_of_trains', ppl )

                  dm_rpl.append ( dm_r )

            print ( "Done release patterns" )
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )


          # Surface Class Definitions

          surfcs = mcell.get('surface_classes')
          if surfcs != None:
            # dm['define_surface_classes'] = self.surface_classes.build_data_model_from_properties(context)
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )
            print ( "There are surface class definitions" )
            # There are surface classes
            print ( "surfcs.keys() = " + str(surfcs.keys()) )
            dm['define_surface_classes'] = {}
            dm_surfcs = dm['define_surface_classes']
            scl = surfcs.get('surf_class_list')
            if scl != None:
              print ( "There is a surf_class_list" )
              dm_surfcs['surface_class_list'] = []
              dm_scl = dm_surfcs['surface_class_list']
              print ( "The surf_class_list has " + str(len(scl)) + " surface classes" )
              if len(scl) > 0:
                for sc in scl:
                  print ( "  Surface Class Name = " + str(sc['name']) )
                  dm_sc = {}
                  if 'name' in sc:
                    dm_sc['name'] = sc['name']
                  dm_sc['surface_class_prop_list'] = []
                  dm_scpl = dm_sc['surface_class_prop_list']
                  if 'surf_class_props_list' in sc:
                    scpl = sc.get('surf_class_props_list')
                    for scp in scpl:
                      print ( "    Surface Class Property Name = " + str(scp['name']) )
                      dm_scp = {}
                      self.RC3_add_from_ID_string   ( dm_scp, 'name',     scp, 'name',     "Surf_Class_Property" )
                      self.RC3_add_from_ID_string   ( dm_scp, 'molecule', scp, 'molecule', "" )
                      
                      self.RC3_add_from_ID_enum     ( dm_scp, 'surf_class_orient', scp, 'surf_class_orient', "\'", ['\'', ',', ';'] )
                      self.RC3_add_from_ID_enum     ( dm_scp, 'surf_class_type',   scp, 'surf_class_type',   "ABSORPTIVE", ['ABSORPTIVE', 'TRANSPARENT', 'REFLECTIVE', 'CLAMP_CONCENTRATION'] )
                      
                      self.RC3_add_from_ID_floatstr ( dm_scp, 'clamp_value',       scp, 'clamp_value', "" )
                      
                      dm_scpl.append ( dm_scp )

                  dm_scl.append ( dm_sc )

            print ( "Done surface class definitions" )
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )


          # Surface Region Definitions

          modsrs = mcell.get('mod_surf_regions')
          if modsrs != None:
            # dm['modify_surface_regions'] = self.mod_surf_regions.build_data_model_from_properties(context)
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )
            print ( "There are surface regions" )
            # There are surface regions
            print ( "modsrs.keys() = " + str(modsrs.keys()) )
            dm['modify_surface_regions'] = {}
            dm_modsrs = dm['modify_surface_regions']
            msrl = modsrs.get('mod_surf_regions_list')
            if msrl != None:
              print ( "There is a mod_surf_regions_list" )
              dm_modsrs['modify_surface_regions_list'] = []
              dm_msrl = dm_modsrs['modify_surface_regions_list']
              if len(msrl) > 0:
                print ( "The mod_surf_regions_list has " + str(len(msrl)) + " regions" )
                for msr in msrl:
                  print ( " Modify Region Name = " + str(msr['name']) )
                  print ( "   Surf Class Name = " + str(msr['surf_class_name']) )
                  print ( "   Object Name = " + str(msr['object_name']) )
                  print ( "   Region Name = " + str(msr['region_name']) )
                  
                  dm_msr = {}

                  self.RC3_add_from_ID_string ( dm_msr, 'name',     msr, 'name',     "" )
                  self.RC3_add_from_ID_string ( dm_msr, 'surf_class_name', msr, 'surf_class_name', "" )
                  self.RC3_add_from_ID_string ( dm_msr, 'object_name', msr, 'object_name', "" )
                  self.RC3_add_from_ID_string ( dm_msr, 'region_name', msr, 'region_name', "" )

                  dm_msrl.append ( dm_msr )

            print ( "Done surface regions" )
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )


          # Visualization Output

          vizout = mcell.get('viz_output')
          if vizout != None:
            # dm['viz_output'] = self.viz_output.build_data_model_from_properties(context)
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )
            print ( "There is viz output" )
            # There is viz output
            dm['viz_output'] = {}
            dm_viz = dm['viz_output']
            self.RC3_add_from_ID_boolean ( dm_viz, 'all_iterations', vizout, 'all_iterations', True )
            self.RC3_add_from_ID_int     ( dm_viz, 'start',          vizout, 'start',          0 )
            self.RC3_add_from_ID_int     ( dm_viz, 'end',            vizout, 'end',            1 )
            self.RC3_add_from_ID_int     ( dm_viz, 'step',           vizout, 'step',           1 )
            self.RC3_add_from_ID_boolean ( dm_viz, 'export_all',     vizout, 'export_all',     False )
            print ( "Done viz output" )
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )


          # Reaction Output

          rxnout = mcell.get('rxn_output')
          if rxnout != None:
            # dm['reaction_data_output'] = self.rxn_output.build_data_model_from_properties(context)
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )
            print ( "There is reaction output" )
            # There is reaction output
            dm['reaction_data_output'] = {}
            dm_rxnout = dm['reaction_data_output']

            self.RC3_add_from_ID_boolean ( dm_rxnout, 'combine_seeds', rxnout, 'combine_seeds', True )
            self.RC3_add_from_ID_boolean ( dm_rxnout, 'mol_colors',    rxnout, 'mol_colors',    False )
            self.RC3_add_from_ID_enum    ( dm_rxnout, 'plot_layout',   rxnout, 'plot_layout',   " plot ", [' page ', ' plot ', ' '] )
            self.RC3_add_from_ID_enum    ( dm_rxnout, 'plot_legend',   rxnout, 'plot_legend',   "0", ['x', '0', '1', '2', '3', '4', '6', '7', '8', '9', '10'] )


            print ( "rxnout.keys() = " + str(rxnout.keys()) )
            rxnl = rxnout.get('rxn_output_list')
            if rxnl != None:
              print ( "There is a rxn_output_list" )
              dm_rxnout['reaction_output_list'] = []
              dm_rxnl = dm_rxnout['reaction_output_list']
              if len(rxnl) > 0:
                print ( "The reaction_output_list has " + str(len(rxnl)) + " entries" )
                for rxn in rxnl:
                  dm_rxn = {}

                  self.RC3_add_from_ID_string ( dm_rxn, 'name',            rxn, 'name',            "" )
                  self.RC3_add_from_ID_string ( dm_rxn, 'molecule_name',   rxn, 'molecule_name',   "" )
                  self.RC3_add_from_ID_string ( dm_rxn, 'reaction_name',   rxn, 'reaction_name',   "" )
                  self.RC3_add_from_ID_string ( dm_rxn, 'object_name',     rxn, 'object_name',     "" )
                  self.RC3_add_from_ID_string ( dm_rxn, 'region_name',     rxn, 'region_name',     "" )
                  self.RC3_add_from_ID_enum   ( dm_rxn, 'count_location',  rxn, 'count_location',  "World",    ['World', 'Object', 'Region'] )
                  self.RC3_add_from_ID_enum   ( dm_rxn, 'rxn_or_mol',      rxn, 'rxn_or_mol',      "Molecule", ['Reaction', 'Molecule', 'MDLString'] )

                  dm_rxnl.append ( dm_rxn )

            print ( "Done reaction output" )
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )


          # Viz Data


            """ Use this as a template for mol_viz data

            def build_data_model_from_properties ( self, context ):
                print ( "Building Mol Viz data model from properties" )
                mv_dm = {}
                mv_dm['data_model_version'] = "DM_2015_04_13_1700"

                mv_seed_list = []
                for s in self.mol_viz_seed_list:
                    mv_seed_list.append ( str(s.name) )
                mv_dm['seed_list'] = mv_seed_list

                mv_dm['active_seed_index'] = self.active_mol_viz_seed_index
                mv_dm['file_dir'] = self.mol_file_dir

                mv_file_list = []
                for s in self.mol_file_list:
                    mv_file_list.append ( str(s.name) )
                mv_dm['file_list'] = mv_file_list

                mv_dm['file_num'] = self.mol_file_num
                mv_dm['file_name'] = self.mol_file_name
                mv_dm['file_index'] = self.mol_file_index
                mv_dm['file_start_index'] = self.mol_file_start_index
                mv_dm['file_stop_index'] = self.mol_file_stop_index
                mv_dm['file_step_index'] = self.mol_file_step_index

                mv_viz_list = []
                for s in self.mol_viz_list:
                    mv_viz_list.append ( str(s.name) )
                mv_dm['viz_list'] = mv_viz_list

                mv_dm['render_and_save'] = self.render_and_save
                mv_dm['viz_enable'] = self.mol_viz_enable

                mv_color_list = []
                for c in self.color_list:
                    mv_color = []
                    for i in c.vec:
                        mv_color.append ( i )
                    mv_color_list.append ( mv_color )
                mv_dm['color_list'] = mv_color_list

                mv_dm['color_index'] = self.color_index
                mv_dm['manual_select_viz_dir'] = self.manual_select_viz_dir

                return mv_dm
            """





          """
          geom = mcell.get('geometrical_objects')
          if geom != None:
            # dm['geometrical_objects'] = self.model_objects.build_data_model_geometry_from_mesh(context)
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )
            print ( "There is viz output" )
            print ( "%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%" )
            # There is viz output
          if geometry:
            print ( "Adding Geometry to Data Model" )
            
            dm['materials'] = self.model_objects.build_data_model_materials_from_materials(context)
          """

        print ( "Adding Geometry to Data Model" )
        dm['geometrical_objects'] = self.model_objects.build_data_model_geometry_from_mesh(context)
        dm['materials'] = self.model_objects.build_data_model_materials_from_materials(context)
        # cellblender.data_model.save_data_model_to_file ( dm, "Upgraded_Data_Model.txt" )
        print ( "Removing Geometry from Data Model" )
        dm.pop('geometrical_objects')
        dm.pop('materials')

        #self.print_id_property_tree ( context.scene['mcell'], 'mcell', 0 )

        # Restore the RNA properties overlaying the ID Property 'mcell'
        bpy.types.Scene.mcell = bpy.props.PointerProperty(type=MCellPropertyGroup)

        return dm

