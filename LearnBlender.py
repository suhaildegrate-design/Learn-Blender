bl_info = {
    "name": "Learn Blender",
    "author": "Suhail Abdulrahman",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Learn Blender",
    "description": "Search YouTube tutorials, bookmark, and track learning progress",
    "category": "Interface",
}

import bpy
import webbrowser
import urllib.parse
import urllib.request
import json
import re
from datetime import datetime
from bpy.props import StringProperty, CollectionProperty, BoolProperty, IntProperty
from bpy.types import Panel, Operator, Menu, PropertyGroup


# ==================== PROPERTY GROUPS ====================

class LB_Tutorial(PropertyGroup):
    title: StringProperty()
    url: StringProperty()
    video_id: StringProperty()
    creator: StringProperty()
    creator_url: StringProperty()
    duration: StringProperty()
    views: StringProperty()
    published: StringProperty()


class LB_Bookmark(PropertyGroup):
    title: StringProperty()
    url: StringProperty()
    video_id: StringProperty()
    creator: StringProperty()
    creator_url: StringProperty()
    notes: StringProperty()
    status: StringProperty(default="Saved")
    date: StringProperty()
    topic: StringProperty()


class LB_PathItem(PropertyGroup):
    name: StringProperty()
    completed: BoolProperty(default=False)


class LB_Path(PropertyGroup):
    name: StringProperty()
    items: CollectionProperty(type=LB_PathItem)


class LB_History(PropertyGroup):
    question: StringProperty()
    date: StringProperty()


# ==================== INITIALIZE PATHS ====================

def init_paths(scene):
    if len(scene.lb_paths) == 0:
        p1 = scene.lb_paths.add()
        p1.name = "Beginner's Journey"
        for item in ["Interface & Navigation", "Basic Objects", "Simple Modeling", "Materials", "Lighting", "Camera & Render"]:
            new = p1.items.add()
            new.name = item
        
        p2 = scene.lb_paths.add()
        p2.name = "Modeling Fundamentals"
        for item in ["Mesh Editing", "Extrude Tools", "Subdivision Surface", "Hard Surface", "Organic Modeling", "Boolean Ops"]:
            new = p2.items.add()
            new.name = item
        
        p3 = scene.lb_paths.add()
        p3.name = "Materials & Textures"
        for item in ["Shader Nodes", "Principled BSDF", "Image Textures", "UV Unwrapping", "Procedural Textures", "PBR Setup"]:
            new = p3.items.add()
            new.name = item
        
        p4 = scene.lb_paths.add()
        p4.name = "Animation Basics"
        for item in ["Keyframes", "Timeline", "Graph Editor", "Simple Character", "Camera Animation", "Render Animation"]:
            new = p4.items.add()
            new.name = item


# ==================== YOUTUBE SEARCH ====================

class LB_OT_Search(Operator):
    bl_idname = "lb.search"
    bl_label = "Search YouTube"
    bl_description = "Search YouTube for tutorials"
    query: StringProperty()
    
    def execute(self, context):
        query = self.query or context.scene.lb_question
        if not query.strip():
            self.report({'ERROR'}, "Please enter a search term")
            return {'CANCELLED'}
        
        context.scene.lb_results.clear()
        context.scene.lb_loading = True
        context.scene.lb_current = query
        
        try:
            search = f"blender {query} tutorial"
            encoded = urllib.parse.quote_plus(search)
            url = f"https://www.youtube.com/results?search_query={encoded}&sp=CAI%253D"
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8')
            
            videos = self.parse_html(html)
            for v in videos[:10]:
                new = context.scene.lb_results.add()
                new.title = v.get('title', 'Tutorial')
                new.url = f"https://www.youtube.com/watch?v={v.get('video_id', '')}"
                new.video_id = v.get('video_id', '')
                new.creator = v.get('creator', 'YouTube Creator')
                new.creator_url = f"https://www.youtube.com/channel/{v.get('channel_id', '')}" if v.get('channel_id') else ""
                new.duration = v.get('duration', '')
                new.views = v.get('views', '')
                new.published = v.get('published', '')
            
            if len(context.scene.lb_results) == 0:
                webbrowser.open(f"https://www.youtube.com/results?search_query=blender+{urllib.parse.quote_plus(query)}+tutorial")
            else:
                self.report({'INFO'}, f"Found {len(context.scene.lb_results)} tutorials")
                
        except Exception as e:
            webbrowser.open(f"https://www.youtube.com/results?search_query=blender+{urllib.parse.quote_plus(query)}+tutorial")
        
        context.scene.lb_loading = False
        
        new = context.scene.lb_history.add()
        new.question = query[:50] + ("..." if len(query) > 50 else "")
        new.date = datetime.now().strftime("%Y-%m-%d")
        
        return {'FINISHED'}
    
    def parse_html(self, html):
        videos = []
        match = re.search(r'ytInitialData\s*=\s*({.+?});', html)
        if not match:
            return videos
        
        try:
            data = json.loads(match.group(1))
            contents = data.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', [])
            if contents:
                items = contents[0].get('itemSectionRenderer', {}).get('contents', [])
                for item in items:
                    vr = item.get('videoRenderer')
                    if vr:
                        v = {}
                        v['video_id'] = vr.get('videoId', '')
                        title = vr.get('title', {}).get('runs', [])
                        if title:
                            v['title'] = title[0].get('text', '')
                        owner = vr.get('ownerText', {}).get('runs', [])
                        if owner:
                            v['creator'] = owner[0].get('text', '')
                            nav = owner[0].get('navigationEndpoint', {}).get('browseEndpoint', {})
                            v['channel_id'] = nav.get('browseId', '')
                        length = vr.get('lengthText', {}).get('simpleText', '')
                        if length:
                            v['duration'] = length
                        views = vr.get('viewCountText', {}).get('simpleText', '')
                        if views:
                            v['views'] = views
                        pub = vr.get('publishedTimeText', {}).get('simpleText', '')
                        if pub:
                            v['published'] = pub
                        if v.get('title') and v.get('video_id'):
                            videos.append(v)
        except:
            pass
        return videos


class LB_OT_OpenCreator(Operator):
    bl_idname = "lb.open_creator"
    bl_label = "Visit Channel"
    bl_description = "Open creator's YouTube channel"
    url: StringProperty()
    name: StringProperty()
    
    def execute(self, context):
        if self.url:
            webbrowser.open(self.url)
        elif self.name:
            webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(self.name)}")
        return {'FINISHED'}


class LB_OT_Watch(Operator):
    bl_idname = "lb.watch"
    bl_label = "Watch"
    bl_description = "Watch this tutorial"
    url: StringProperty()
    
    def execute(self, context):
        if self.url:
            webbrowser.open(self.url)
        return {'FINISHED'}


class LB_OT_Save(Operator):
    bl_idname = "lb.save"
    bl_label = "Save"
    bl_description = "Save tutorial to bookmarks"
    title: StringProperty()
    url: StringProperty()
    video_id: StringProperty()
    creator: StringProperty()
    creator_url: StringProperty()
    
    def execute(self, context):
        new = context.scene.lb_bookmarks.add()
        new.title = self.title
        new.url = self.url
        new.video_id = self.video_id
        new.creator = self.creator
        new.creator_url = self.creator_url
        new.notes = ""
        new.status = "Saved"
        new.date = datetime.now().strftime("%Y-%m-%d")
        self.report({'INFO'}, f"Saved: {self.title}")
        return {'FINISHED'}


class LB_OT_Remove(Operator):
    bl_idname = "lb.remove"
    bl_label = "Remove"
    bl_description = "Remove from bookmarks"
    idx: IntProperty()
    
    def execute(self, context):
        context.scene.lb_bookmarks.remove(self.idx)
        return {'FINISHED'}


class LB_OT_UpdateStatus(Operator):
    bl_idname = "lb.update_status"
    bl_label = "Update Status"
    bl_description = "Update learning status"
    idx: IntProperty()
    status: StringProperty()
    
    def execute(self, context):
        context.scene.lb_bookmarks[self.idx].status = self.status
        return {'FINISHED'}


class LB_OT_ClearHistory(Operator):
    bl_idname = "lb.clear_history"
    bl_label = "Clear History"
    bl_description = "Clear search history"
    
    def execute(self, context):
        context.scene.lb_history.clear()
        return {'FINISHED'}


class LB_OT_ClearBookmarks(Operator):
    bl_idname = "lb.clear_bookmarks"
    bl_label = "Clear All Bookmarks"
    bl_description = "Remove all bookmarks"
    
    def execute(self, context):
        context.scene.lb_bookmarks.clear()
        return {'FINISHED'}


class LB_OT_TogglePath(Operator):
    bl_idname = "lb.toggle_path"
    bl_label = "Toggle"
    bl_description = "Toggle topic completion"
    path_idx: IntProperty()
    item_idx: IntProperty()
    
    def execute(self, context):
        path = context.scene.lb_paths[self.path_idx]
        path.items[self.item_idx].completed = not path.items[self.item_idx].completed
        return {'FINISHED'}


class LB_OT_ResetPath(Operator):
    bl_idname = "lb.reset_path"
    bl_label = "Reset Path"
    bl_description = "Reset all topics in this path"
    path_idx: IntProperty()
    
    def execute(self, context):
        path = context.scene.lb_paths[self.path_idx]
        for item in path.items:
            item.completed = False
        return {'FINISHED'}


# ==================== MAIN PANEL ====================

class LB_PT_Main(Panel):
    bl_label = "Learn Blender"
    bl_idname = "LB_PT_Main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Learn Blender"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        row = layout.row(align=True)
        row.prop(scene, "lb_tab", expand=True)
        layout.separator()
        
        if scene.lb_tab == 'SEARCH':
            self.draw_search(context)
        elif scene.lb_tab == 'BOOKMARKS':
            self.draw_bookmarks(context)
        elif scene.lb_tab == 'PATHS':
            self.draw_paths(context)
    
    def draw_search(self, context):
        layout = self.layout
        scene = context.scene
        
        box = layout.box()
        box.label(text="Search YouTube Tutorials", icon='PLAY')
        
        text = scene.lb_question
        lines = max(text.count('\n') + 1 if text else 1, 2)
        rows = min(lines, 4)
        
        col = box.column(align=True)
        col.scale_y = rows * 0.6
        col.prop(scene, "lb_question", text="")
        
        row = box.row(align=True)
        row.operator("lb.search", text="Search", icon='VIEWZOOM')
        
        row = box.row(align=True)
        row.label(text="Try:")
        row.operator("lb.search", text="Beginner", icon='FILE_NEW').query = "blender for absolute beginners"
        row.operator("lb.search", text="Modeling", icon='MESH_CUBE').query = "3d modeling"
        row.operator("lb.search", text="Animation", icon='ARMATURE_DATA').query = "character animation"
        
        if scene.lb_loading:
            box = layout.box()
            box.label(text="Searching YouTube...", icon='INFO')
        
        if scene.lb_current and len(scene.lb_results) > 0:
            box = layout.box()
            short = scene.lb_current[:40] + ("..." if len(scene.lb_current) > 40 else "")
            box.label(text=f"Results for: {short}", icon='FILE_TICK')
            
            for rec in scene.lb_results:
                rec_box = box.box()
                
                row = rec_box.row(align=True)
                row.label(text=rec.title, icon='PLAY')
                if rec.duration:
                    row.label(text=f"[{rec.duration}]")
                
                row = rec_box.row(align=True)
                row.label(text=rec.creator, icon='USER')
                if rec.creator_url:
                    op = row.operator("lb.open_creator", text="Channel", icon='USER')
                    op.url = rec.creator_url
                    op.name = rec.creator
                
                row = rec_box.row()
                if rec.views:
                    row.label(text=f"Views: {rec.views}")
                if rec.published:
                    row.label(text=f"Uploaded: {rec.published}")
                
                row = rec_box.row(align=True)
                op = row.operator("lb.watch", text="Watch", icon='PLAY')
                op.url = rec.url
                
                op = row.operator("lb.save", text="Save", icon='BOOKMARKS')
                op.title = rec.title
                op.url = rec.url
                op.video_id = rec.video_id
                op.creator = rec.creator
                op.creator_url = rec.creator_url
        
        if len(scene.lb_history) > 0:
            box = layout.box()
            row = box.row()
            row.label(text="Recent Searches", icon='TIME')
            row.operator("lb.clear_history", text="", icon='X')
            for item in reversed(scene.lb_history[-5:]):
                op = box.operator("lb.search", text=item.question, icon='FILE_TICK')
                op.query = item.question
    
    def draw_bookmarks(self, context):
        layout = self.layout
        scene = context.scene
        
        row = layout.row(align=True)
        row.operator("lb.clear_bookmarks", text="Clear All", icon='X')
        layout.separator()
        
        total = len(scene.lb_bookmarks)
        if total > 0:
            saved = sum(1 for b in scene.lb_bookmarks if b.status == "Saved")
            prog = sum(1 for b in scene.lb_bookmarks if b.status == "In Progress")
            done = sum(1 for b in scene.lb_bookmarks if b.status == "Completed")
            row = layout.row(align=True)
            row.label(text=f"Total: {total}", icon='BOOKMARKS')
            row.label(text=f"Saved: {saved}", icon='PINNED')
            row.label(text=f"In Progress: {prog}", icon='TIME')
            row.label(text=f"Completed: {done}", icon='CHECKMARK')
            layout.separator()
        
        for idx, b in enumerate(scene.lb_bookmarks):
            box = layout.box()
            
            row = box.row(align=True)
            if b.status == "Completed":
                row.label(text="✓", icon='CHECKMARK')
            elif b.status == "In Progress":
                row.label(text="→", icon='TIME')
            else:
                row.label(text="📌", icon='PINNED')
            row.label(text=b.title, icon='PLAY')
            op = row.operator("lb.watch", text="", icon='PLAY')
            op.url = b.url
            op = row.operator("lb.remove", text="", icon='X')
            op.idx = idx
            
            row = box.row(align=True)
            row.label(text=b.creator, icon='USER')
            if b.creator_url:
                op = row.operator("lb.open_creator", text="Channel", icon='USER')
                op.url = b.creator_url
                op.name = b.creator
            
            row = box.row(align=True)
            row.label(text="Status:")
            if b.status == "Completed":
                op = row.operator("lb.update_status", text="Saved", icon='PINNED')
            elif b.status == "In Progress":
                op = row.operator("lb.update_status", text="Done", icon='CHECKMARK')
            else:
                op = row.operator("lb.update_status", text="Start", icon='TIME')
            op.idx = idx
            op.status = "In Progress" if b.status == "Saved" else ("Completed" if b.status == "In Progress" else "Saved")
            
            notes_box = box.box()
            notes_box.label(text="Notes:", icon='TEXT')
            col = notes_box.column(align=True)
            col.scale_y = 3.0
            col.prop(b, "notes", text="")
            row = notes_box.row()
            row.label(text="💡 Press Enter for new line", icon='INFO')
            
            row = box.row()
            row.label(text=f"Added: {b.date}", icon='TIME')
    
    def draw_paths(self, context):
        layout = self.layout
        scene = context.scene
        
        if len(scene.lb_paths) == 0:
            init_paths(scene)
        
        if len(scene.lb_paths) == 0:
            box = layout.box()
            box.label(text="No learning paths found.", icon='INFO')
            return
        
        for p_idx, path in enumerate(scene.lb_paths):
            box = layout.box()
            completed = sum(1 for i in path.items if i.completed)
            total = len(path.items)
            
            row = box.row(align=True)
            row.label(text=path.name, icon='BOOKMARKS')
            row.label(text=f"({completed}/{total})")
            row.operator("lb.reset_path", text="Reset", icon='LOOP_BACK').path_idx = p_idx
            
            if total > 0:
                pct = int((completed / total) * 100)
                row = box.row()
                row.scale_y = 0.5
                filled = pct // 5
                empty = 20 - filled
                row.label(text="█" * filled + "░" * empty)
            
            for i_idx, item in enumerate(path.items):
                row = box.row(align=True)
                if item.completed:
                    row.label(text="✓", icon='CHECKBOX_HLT')
                    row.label(text=item.name)
                else:
                    op = row.operator("lb.toggle_path", text="", icon='CHECKBOX_DEHLT', emboss=False)
                    op.path_idx = p_idx
                    op.item_idx = i_idx
                    row.label(text=item.name)
            
            layout.separator()


# ==================== HEADER MENU ====================

class LB_MT_Menu(Menu):
    bl_label = "Learn Blender"
    bl_idname = "LB_MT_Menu"
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Learn Blender", icon='URL')
        layout.separator()
        layout.operator("lb.search", text="Search").query = "blender tutorial"


def menu_func(self, context):
    self.layout.menu("LB_MT_Menu", icon='TUTORIAL_DATA')


# ==================== REGISTRATION ====================

classes = [
    LB_Tutorial,
    LB_Bookmark,
    LB_PathItem,
    LB_Path,
    LB_History,
    LB_OT_Search,
    LB_OT_OpenCreator,
    LB_OT_Watch,
    LB_OT_Save,
    LB_OT_Remove,
    LB_OT_UpdateStatus,
    LB_OT_ClearHistory,
    LB_OT_ClearBookmarks,
    LB_OT_TogglePath,
    LB_OT_ResetPath,
    LB_PT_Main,
    LB_MT_Menu,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.lb_question = StringProperty(
        name="",
        description="Search YouTube for Blender tutorials",
        default=""
    )
    bpy.types.Scene.lb_current = StringProperty(default="")
    bpy.types.Scene.lb_loading = BoolProperty(default=False)
    bpy.types.Scene.lb_results = CollectionProperty(type=LB_Tutorial)
    bpy.types.Scene.lb_bookmarks = CollectionProperty(type=LB_Bookmark)
    bpy.types.Scene.lb_paths = CollectionProperty(type=LB_Path)
    bpy.types.Scene.lb_history = CollectionProperty(type=LB_History)
    
    bpy.types.Scene.lb_tab = bpy.props.EnumProperty(
        name="Tab",
        items=[
            ('SEARCH', "Search", "Search YouTube", 'VIEWZOOM', 0),
            ('BOOKMARKS', "Bookmarks", "Saved tutorials", 'BOOKMARKS', 1),
            ('PATHS', "Paths", "Learning paths", 'FILE_FOLDER', 2),
        ],
        default='SEARCH'
    )
    
    bpy.types.VIEW3D_MT_editor_menus.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_editor_menus.remove(menu_func)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.lb_question
    del bpy.types.Scene.lb_current
    del bpy.types.Scene.lb_loading
    del bpy.types.Scene.lb_results
    del bpy.types.Scene.lb_bookmarks
    del bpy.types.Scene.lb_paths
    del bpy.types.Scene.lb_history
    del bpy.types.Scene.lb_tab


if __name__ == "__main__":
    register()