bl_info = {
    "name": "Learn Blender",
    "author": "Your Name",
    "version": (3, 1),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Learn Blender",
    "description": "Find the latest Blender tutorials on YouTube",
    "category": "Interface",
}

import bpy
import webbrowser
import urllib.parse
from datetime import datetime
from bpy.props import StringProperty, CollectionProperty
from bpy.types import Panel, Operator, Menu, PropertyGroup

# Store search history
class LearnBlenderHistory(PropertyGroup):
    text: StringProperty(name="Search Text")

# Search operator
class LEARNBLENDER_OT_Search(Operator):
    bl_idname = "learnblender.search"
    bl_label = "Search YouTube"
    
    query: StringProperty()
    
    def execute(self, context):
        if not self.query:
            self.query = "learn blender"
        
        current_year = datetime.now().year
        search_query = f"{self.query} {current_year}"
        encoded = urllib.parse.quote_plus(search_query)
        url = f"https://www.youtube.com/results?search_query={encoded}&sp=CAI%253D"
        
        webbrowser.open(url)
        
        # Save to history
        exists = False
        for item in context.scene.learnblender_history:
            if item.text == self.query:
                exists = True
                break
        
        if not exists:
            if len(context.scene.learnblender_history) >= 8:
                context.scene.learnblender_history.remove(0)
            new = context.scene.learnblender_history.add()
            new.text = self.query
        
        return {'FINISHED'}

# Category operator with ADVANCED search terms (the good ones!)
class LEARNBLENDER_OT_Category(Operator):
    bl_idname = "learnblender.category"
    bl_label = "Category Search"
    
    category_type: StringProperty()
    
    def execute(self, context):
        current_year = datetime.now().year
        
        # ADVANCED search terms - these work great!
        search_terms = {
            "absolute_beginner": f"blender absolute beginner tutorial interface basics first steps {current_year}",
            "modeling": f"blender 3d modeling hard surface organic techniques {current_year}",
            "materials": f"blender materials shader nodes principled pbr {current_year}",
            "textures": f"blender texture painting uv mapping image textures {current_year}",
            "animation": f"blender animation keyframes timeline graph editor fcurve {current_year}",
            "rigging": f"blender rigging armature bones weight paint constraints {current_year}",
            "sculpting": f"blender sculpting dynotopo multires brushes details {current_year}",
            "lighting": f"blender lighting hdri 3 point studio setup {current_year}",
            "rendering": f"blender rendering cycles eevee settings optimization {current_year}",
            "geometry_nodes": f"blender geometry nodes procedural generative fields {current_year}",
            "compositing": f"blender compositing nodes post processing vfx {current_year}",
            "simulation": f"blender physics simulation cloth fluid smoke rigid body {current_year}",
            "uv_mapping": f"blender uv mapping unwrapping seams packing islands {current_year}",
            "grease_pencil": f"blender grease pencil 2d animation storyboard {current_year}",
            "most_viewed": f"blender tutorial most viewed popular all time",
            "new": f"blender tutorial new uploads this week {current_year}",
            "complete_course": f"blender complete course tutorial in depth",
            "quick_tips": f"blender quick tips shortcuts tricks"
        }
        
        query = search_terms.get(self.category_type, f"blender {self.category_type} tutorial {current_year}")
        
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.youtube.com/results?search_query={encoded}&sp=CAI%253D"
        webbrowser.open(url)
        
        return {'FINISHED'}

# Clear history
class LEARNBLENDER_OT_ClearHistory(Operator):
    bl_idname = "learnblender.clear_history"
    bl_label = "Clear History"
    
    def execute(self, context):
        context.scene.learnblender_history.clear()
        self.report({'INFO'}, "History cleared")
        return {'FINISHED'}

# Main panel
class LEARNBLENDER_PT_MainPanel(Panel):
    bl_label = "Learn Blender"
    bl_idname = "LEARNBLENDER_PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Learn Blender"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        current_year = datetime.now().year
        
        # Header
        box = layout.box()
        box.label(text=f"Learn Blender {current_year}", icon='URL')
        box.label(text="Find the latest tutorials", icon='INFO')
        
        # Search box
        box = layout.box()
        box.label(text="Search:", icon='VIEWZOOM')
        row = box.row(align=True)
        row.prop(scene, "learnblender_search", text="")
        op = row.operator("learnblender.search", text="Go", icon='PLAY')
        op.query = scene.learnblender_search or "learn blender"
        
        # History
        if len(scene.learnblender_history) > 0:
            box = layout.box()
            row = box.row()
            row.label(text="Recent:", icon='TIME')
            row.operator("learnblender.clear_history", text="", icon='X')
            
            col = box.column(align=True)
            for item in reversed(scene.learnblender_history[-5:]):
                op = col.operator("learnblender.search", text=item.text, icon='HISTORY')
                op.query = item.text
        
        layout.separator()
        
        # Topics - Simple labels but using the advanced search terms
        box = layout.box()
        box.label(text="Topics:", icon='FILE_FOLDER')
        
        # Row 1
        row = box.row(align=True)
        op = row.operator("learnblender.category", text="Absolute Beginners", icon='FILE_NEW')
        op.category_type = "absolute_beginner"
        op = row.operator("learnblender.category", text="Modeling", icon='MESH_CUBE')
        op.category_type = "modeling"
        
        # Row 2
        row = box.row(align=True)
        op = row.operator("learnblender.category", text="Materials", icon='MATERIAL')
        op.category_type = "materials"
        op = row.operator("learnblender.category", text="Textures", icon='TEXTURE')
        op.category_type = "textures"
        
        # Row 3
        row = box.row(align=True)
        op = row.operator("learnblender.category", text="Animation", icon='ARMATURE_DATA')
        op.category_type = "animation"
        op = row.operator("learnblender.category", text="Rigging", icon='CONSTRAINT_BONE')
        op.category_type = "rigging"
        
        # Row 4
        row = box.row(align=True)
        op = row.operator("learnblender.category", text="Sculpting", icon='SCULPTMODE_HLT')
        op.category_type = "sculpting"
        op = row.operator("learnblender.category", text="Lighting", icon='LIGHT')
        op.category_type = "lighting"
        
        # Row 5
        row = box.row(align=True)
        op = row.operator("learnblender.category", text="Rendering", icon='RENDER_STILL')
        op.category_type = "rendering"
        op = row.operator("learnblender.category", text="Geo Nodes", icon='GEOMETRY_NODES')
        op.category_type = "geometry_nodes"
        
        # Row 6
        row = box.row(align=True)
        op = row.operator("learnblender.category", text="Compositing", icon='NODE_COMPOSITING')
        op.category_type = "compositing"
        op = row.operator("learnblender.category", text="Simulation", icon='PHYSICS')
        op.category_type = "simulation"
        
        # Row 7
        row = box.row(align=True)
        op = row.operator("learnblender.category", text="UV Mapping", icon='UV_DATA')
        op.category_type = "uv_mapping"
        op = row.operator("learnblender.category", text="Grease Pencil", icon='GREASEPENCIL')
        op.category_type = "grease_pencil"
        
        layout.separator()
        
        # Special searches
        box = layout.box()
        box.label(text="Collections:", icon='SETTINGS')
        
        col = box.column(align=True)
        row = col.row(align=True)
        op = row.operator("learnblender.category", text="Most Popular", icon='SOLO_ON')
        op.category_type = "most_viewed"
        op = row.operator("learnblender.category", text="New This Week", icon='FILE_NEW')
        op.category_type = "new"
        
        row = col.row(align=True)
        op = row.operator("learnblender.category", text="Complete Courses", icon='LIBRARY_DATA_DIRECT')
        op.category_type = "complete_course"
        op = row.operator("learnblender.category", text="Quick Tips", icon='TIME')
        op.category_type = "quick_tips"

# Menu in header
class LEARNBLENDER_MT_Menu(Menu):
    bl_label = "Learn Blender"
    bl_idname = "LEARNBLENDER_MT_menu"
    
    def draw(self, context):
        layout = self.layout
        current_year = datetime.now().year
        
        layout.label(text=f"Learn Blender {current_year}", icon='URL')
        layout.separator()
        
        op = layout.operator("learnblender.category", text="Absolute Beginners", icon='FILE_NEW')
        op.category_type = "absolute_beginner"
        op = layout.operator("learnblender.category", text="Modeling", icon='MESH_CUBE')
        op.category_type = "modeling"
        op = layout.operator("learnblender.category", text="Materials", icon='MATERIAL')
        op.category_type = "materials"
        op = layout.operator("learnblender.category", text="Animation", icon='ARMATURE_DATA')
        op.category_type = "animation"
        op = layout.operator("learnblender.category", text="Rigging", icon='CONSTRAINT_BONE')
        op.category_type = "rigging"
        op = layout.operator("learnblender.category", text="Sculpting", icon='SCULPTMODE_HLT')
        op.category_type = "sculpting"

# Add to header
def menu_func(self, context):
    self.layout.menu("LEARNBLENDER_MT_menu", icon='TUTORIAL_DATA')

# Registration
classes = [
    LearnBlenderHistory,
    LEARNBLENDER_OT_Search,
    LEARNBLENDER_OT_Category,
    LEARNBLENDER_OT_ClearHistory,
    LEARNBLENDER_PT_MainPanel,
    LEARNBLENDER_MT_Menu,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.learnblender_search = StringProperty(
        name="",
        description="Search YouTube for tutorials",
        default=""
    )
    
    bpy.types.Scene.learnblender_history = CollectionProperty(type=LearnBlenderHistory)
    
    bpy.types.VIEW3D_MT_editor_menus.append(menu_func)

def unregister():
    bpy.types.VIEW3D_MT_editor_menus.remove(menu_func)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.learnblender_search
    del bpy.types.Scene.learnblender_history

if __name__ == "__main__":
    register()