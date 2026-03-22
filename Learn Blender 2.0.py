bl_info = {
    "name": "Learn Blender",
    "author": "Your Name",
    "version": (2, 0, 0),
    "blender": (5, 0, 0),
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

class TutorialRecommendation(PropertyGroup):
    title: StringProperty()
    url: StringProperty()
    video_id: StringProperty()
    creator: StringProperty()
    creator_url: StringProperty()
    duration: StringProperty()
    views: StringProperty()
    published: StringProperty()
    thumbnail: StringProperty()


class BookmarkItem(PropertyGroup):
    title: StringProperty()
    url: StringProperty()
    video_id: StringProperty()
    creator: StringProperty()
    creator_url: StringProperty()
    notes: StringProperty()
    status: StringProperty(default="Saved")
    date: StringProperty()
    topic: StringProperty()


class PathItem(PropertyGroup):
    name: StringProperty()
    completed: BoolProperty(default=False)


class PathCategory(PropertyGroup):
    name: StringProperty()
    items: CollectionProperty(type=PathItem)


class HistoryItem(PropertyGroup):
    question: StringProperty()
    date: StringProperty()


# ==================== YOUTUBE SEARCH ====================

class LB_OT_SearchYouTube(Operator):
    bl_idname = "lb.search_youtube"
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
        context.scene.lb_current_question = query
        
        self.search_youtube_real(context, query)
        
        context.scene.lb_loading = False
        
        new_history = context.scene.lb_history.add()
        new_history.question = query[:50] + ("..." if len(query) > 50 else "")
        new_history.date = datetime.now().strftime("%Y-%m-%d")
        
        return {'FINISHED'}
    
    def search_youtube_real(self, context, query):
        try:
            search_query = f"blender {query} tutorial"
            encoded = urllib.parse.quote_plus(search_query)
            # &sp=EgIQAQ%3D%3D filters by relevance, &sp=CAI%253D filters by year
            url = f"https://www.youtube.com/results?search_query={encoded}&sp=CAI%253D"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                html = response.read().decode('utf-8')
            
            videos = self.parse_youtube_html(html)
            
            for video in videos[:10]:
                new = context.scene.lb_results.add()
                new.title = video.get('title', 'Tutorial')
                new.url = f"https://www.youtube.com/watch?v={video.get('video_id', '')}"
                new.video_id = video.get('video_id', '')
                new.creator = video.get('creator', 'YouTube Creator')
                new.creator_url = f"https://www.youtube.com/channel/{video.get('channel_id', '')}" if video.get('channel_id') else ""
                new.duration = video.get('duration', '')
                new.views = video.get('views', '')
                new.published = video.get('published', '')
                new.thumbnail = video.get('thumbnail', '')
            
            if len(context.scene.lb_results) == 0:
                webbrowser.open(f"https://www.youtube.com/results?search_query=blender+{urllib.parse.quote_plus(query)}+tutorial&sp=CAI%253D")
            else:
                self.report({'INFO'}, f"Found {len(context.scene.lb_results)} tutorials")
                
        except Exception as e:
            webbrowser.open(f"https://www.youtube.com/results?search_query=blender+{urllib.parse.quote_plus(query)}+tutorial&sp=CAI%253D")
    
    def parse_youtube_html(self, html):
        videos = []
        
        match = re.search(r'ytInitialData\s*=\s*({.+?});', html)
        if not match:
            return videos
        
        try:
            data = json.loads(match.group(1))
            
            contents = data.get('contents', {})
            two_column = contents.get('twoColumnSearchResultsRenderer', {})
            primary = two_column.get('primaryContents', {})
            section_list = primary.get('sectionListRenderer', {})
            contents_list = section_list.get('contents', [])
            
            if contents_list:
                item_section = contents_list[0].get('itemSectionRenderer', {})
                items = item_section.get('contents', [])
                
                for item in items:
                    video_renderer = item.get('videoRenderer')
                    if video_renderer:
                        video = {}
                        video['video_id'] = video_renderer.get('videoId', '')
                        
                        title_obj = video_renderer.get('title', {})
                        title_runs = title_obj.get('runs', [])
                        if title_runs:
                            video['title'] = title_runs[0].get('text', '')
                        
                        owner_text = video_renderer.get('ownerText', {})
                        owner_runs = owner_text.get('runs', [])
                        if owner_runs:
                            video['creator'] = owner_runs[0].get('text', '')
                            nav = owner_runs[0].get('navigationEndpoint', {})
                            browse = nav.get('browseEndpoint', {})
                            video['channel_id'] = browse.get('browseId', '')
                        
                        length_text = video_renderer.get('lengthText', {})
                        length_simple = length_text.get('simpleText', '')
                        if length_simple:
                            video['duration'] = length_simple
                        
                        view_count = video_renderer.get('viewCountText', {})
                        view_simple = view_count.get('simpleText', '')
                        if view_simple:
                            video['views'] = view_simple
                        
                        published = video_renderer.get('publishedTimeText', {})
                        pub_simple = published.get('simpleText', '')
                        if pub_simple:
                            video['published'] = pub_simple
                        
                        if video.get('title') and video.get('video_id'):
                            videos.append(video)
                            
        except Exception as e:
            print(f"Parse error: {e}")
        
        return videos


# ==================== OTHER OPERATORS ====================

class LB_OT_OpenCreator(Operator):
    bl_idname = "lb.open_creator"
    bl_label = "Visit Channel"
    
    creator_url: StringProperty()
    creator_name: StringProperty()
    
    def execute(self, context):
        if self.creator_url:
            webbrowser.open(self.creator_url)
        elif self.creator_name:
            webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(self.creator_name)}")
        return {'FINISHED'}


class LB_OT_Watch(Operator):
    bl_idname = "lb.watch"
    bl_label = "Watch"
    url: StringProperty()
    title: StringProperty()
    
    def execute(self, context):
        if self.url:
            webbrowser.open(self.url)
        return {'FINISHED'}


class LB_OT_Save(Operator):
    bl_idname = "lb.save"
    bl_label = "Save"
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
    index: IntProperty()
    
    def execute(self, context):
        context.scene.lb_bookmarks.remove(self.index)
        return {'FINISHED'}


class LB_OT_UpdateStatus(Operator):
    bl_idname = "lb.update_status"
    bl_label = "Update"
    index: IntProperty()
    status: StringProperty()
    
    def execute(self, context):
        context.scene.lb_bookmarks[self.index].status = self.status
        return {'FINISHED'}


class LB_OT_UpdateNotes(Operator):
    bl_idname = "lb.update_notes"
    bl_label = "Update"
    index: IntProperty()
    notes: StringProperty()
    
    def execute(self, context):
        context.scene.lb_bookmarks[self.index].notes = self.notes
        return {'FINISHED'}


class LB_OT_ClearHistory(Operator):
    bl_idname = "lb.clear_history"
    bl_label = "Clear"
    
    def execute(self, context):
        context.scene.lb_history.clear()
        return {'FINISHED'}


class LB_OT_ClearBookmarks(Operator):
    bl_idname = "lb.clear_bookmarks"
    bl_label = "Clear All"
    
    def execute(self, context):
        context.scene.lb_bookmarks.clear()
        return {'FINISHED'}


class LB_OT_TogglePath(Operator):
    bl_idname = "lb.toggle_path"
    bl_label = "Toggle"
    path_index: IntProperty()
    item_index: IntProperty()
    
    def execute(self, context):
        path = context.scene.lb_paths[self.path_index]
        path.items[self.item_index].completed = not path.items[self.item_index].completed
        return {'FINISHED'}


class LB_OT_ResetPath(Operator):
    bl_idname = "lb.reset_path"
    bl_label = "Reset Path"
    path_name: StringProperty()
    
    def execute(self, context):
        for path in context.scene.lb_paths:
            if path.name == self.path_name:
                for item in path.items:
                    item.completed = False
                break
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
            self.draw_search_tab(context)
        elif scene.lb_tab == 'BOOKMARKS':
            self.draw_bookmarks_tab(context)
        elif scene.lb_tab == 'PATHS':
            self.draw_paths_tab(context)
    
    def draw_search_tab(self, context):
        layout = self.layout
        scene = context.scene
        
        box = layout.box()
        box.label(text="Search YouTube Tutorials", icon='VIEWZOOM')
        
        text = scene.lb_question
        lines = max(text.count('\n') + 1 if text else 1, 2)
        rows = min(lines, 4)
        
        col = box.column(align=True)
        col.scale_y = rows * 0.6
        col.prop(scene, "lb_question", text="")
        
        row = box.row(align=True)
        row.operator("lb.search_youtube", text="Search", icon='PLAY')
        
        row = box.row(align=True)
        row.label(text="Try:")
        row.operator("lb.search_youtube", text="Beginner", icon='FILE_NEW').query = "blender for absolute beginners"
        row.operator("lb.search_youtube", text="Modeling", icon='MESH_CUBE').query = "3d modeling"
        row.operator("lb.search_youtube", text="Animation", icon='ARMATURE_DATA').query = "character animation"
        
        if scene.lb_loading:
            box = layout.box()
            box.label(text="Searching YouTube...", icon='INFO')
        
        if scene.lb_current_question and len(scene.lb_results) > 0:
            box = layout.box()
            short_q = scene.lb_current_question[:40] + ("..." if len(scene.lb_current_question) > 40 else "")
            box.label(text=f"Results for: {short_q}", icon='FILE_TICK')
            
            for rec in scene.lb_results:
                rec_box = box.box()
                
                row = rec_box.row(align=True)
                row.label(text=rec.title, icon='URL')
                if rec.duration:
                    row.label(text=f"[{rec.duration}]")
                
                row = rec_box.row(align=True)
                row.label(text=f"Channel: {rec.creator}", icon='USER')
                if rec.creator_url:
                    op = row.operator("lb.open_creator", text="Visit Channel", icon='WORLD')
                    op.creator_url = rec.creator_url
                    op.creator_name = rec.creator
                
                row = rec_box.row()
                if rec.views:
                    row.label(text=f"Views: {rec.views}")
                if rec.published:
                    row.label(text=f"Uploaded: {rec.published}")
                
                row = rec_box.row(align=True)
                op = row.operator("lb.watch", text="Watch", icon='PLAY')
                op.url = rec.url
                op.title = rec.title
                
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
                op = box.operator("lb.search_youtube", text=item.question, icon='FILE_TICK')
                op.query = item.question
    
    def draw_bookmarks_tab(self, context):
        layout = self.layout
        scene = context.scene
        
        row = layout.row(align=True)
        row.operator("lb.clear_bookmarks", text="Clear All", icon='X')
        layout.separator()
        
        total = len(scene.lb_bookmarks)
        if total > 0:
            saved = sum(1 for b in scene.lb_bookmarks if b.status == "Saved")
            progress = sum(1 for b in scene.lb_bookmarks if b.status == "In Progress")
            done = sum(1 for b in scene.lb_bookmarks if b.status == "Completed")
            row = layout.row(align=True)
            row.label(text=f"Total: {total}", icon='BOOKMARKS')
            row.label(text=f"Saved: {saved}", icon='PINNED')
            row.label(text=f"In Progress: {progress}", icon='TIME')
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
            row.label(text=b.title, icon='URL')
            op = row.operator("lb.watch", text="", icon='PLAY')
            op.url = b.url
            op.title = b.title
            op = row.operator("lb.remove", text="", icon='X')
            op.index = idx
            
            row = box.row(align=True)
            row.label(text=f"Channel: {b.creator}", icon='USER')
            if b.creator_url:
                op = row.operator("lb.open_creator", text="Visit Channel", icon='WORLD')
                op.creator_url = b.creator_url
                op.creator_name = b.creator
            
            row = box.row(align=True)
            row.label(text="Status:")
            if b.status == "Completed":
                op = row.operator("lb.update_status", text="Mark Saved", icon='PINNED')
            elif b.status == "In Progress":
                op = row.operator("lb.update_status", text="Mark Done", icon='CHECKMARK')
            else:
                op = row.operator("lb.update_status", text="Start Learning", icon='TIME')
            op.index = idx
            op.status = "In Progress" if b.status == "Saved" else ("Completed" if b.status == "In Progress" else "Saved")
            
            row = box.row(align=True)
            row.prop(b, "notes", text="Notes")
            row = box.row()
            row.label(text=f"Added: {b.date}", icon='TIME')
    
    def draw_paths_tab(self, context):
        layout = self.layout
        scene = context.scene
        
        if len(scene.lb_paths) == 0:
            beginner = scene.lb_paths.add()
            beginner.name = "Beginner's Journey"
            for item in ["Interface & Navigation", "Basic Objects", "Simple Modeling", "Materials", "Lighting", "Camera & Render"]:
                new_item = beginner.items.add()
                new_item.name = item
            
            modeling = scene.lb_paths.add()
            modeling.name = "Modeling Fundamentals"
            for item in ["Mesh Editing Basics", "Extrude Tools", "Subdivision Surface", "Hard Surface", "Organic Modeling", "Boolean Operations"]:
                new_item = modeling.items.add()
                new_item.name = item
            
            materials = scene.lb_paths.add()
            materials.name = "Materials & Textures"
            for item in ["Shader Nodes", "Principled BSDF", "Image Textures", "UV Unwrapping", "Procedural Textures", "PBR Setup"]:
                new_item = materials.items.add()
                new_item.name = item
            
            animation = scene.lb_paths.add()
            animation.name = "Animation Basics"
            for item in ["Keyframes", "Timeline & Dopesheet", "Graph Editor", "Simple Character Animation", "Camera Animation", "Render Animation"]:
                new_item = animation.items.add()
                new_item.name = item
        
        for path_idx, path in enumerate(scene.lb_paths):
            box = layout.box()
            completed = sum(1 for i in path.items if i.completed)
            total = len(path.items)
            
            row = box.row(align=True)
            row.label(text=f"{path.name}", icon='BOOKMARKS')
            row.label(text=f"({completed}/{total})")
            if path.name == "Beginner's Journey":
                row.operator("lb.reset_path", text="Reset", icon='LOOP_BACK').path_name = path.name
            
            if total > 0:
                pct = int((completed / total) * 100)
                row = box.row()
                row.scale_y = 0.5
                filled = pct // 5
                empty = 20 - filled
                row.label(text="█" * filled + "░" * empty)
            
            for item_idx, item in enumerate(path.items):
                row = box.row(align=True)
                if item.completed:
                    row.label(text="✓", icon='CHECKBOX_HLT')
                    row.label(text=item.name)
                else:
                    op = row.operator("lb.toggle_path", text="", icon='CHECKBOX_DEHLT', emboss=False)
                    op.path_index = path_idx
                    op.item_index = item_idx
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
        layout.operator("lb.search_youtube", text="Search").query = "blender tutorial"


def menu_func(self, context):
    self.layout.menu("LB_MT_Menu", icon='TUTORIAL_DATA')


# ==================== REGISTRATION ====================

classes = [
    TutorialRecommendation,
    BookmarkItem,
    PathItem,
    PathCategory,
    HistoryItem,
    LB_OT_SearchYouTube,
    LB_OT_OpenCreator,
    LB_OT_Watch,
    LB_OT_Save,
    LB_OT_Remove,
    LB_OT_UpdateStatus,
    LB_OT_UpdateNotes,
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
    bpy.types.Scene.lb_current_question = StringProperty(default="")
    bpy.types.Scene.lb_loading = BoolProperty(default=False)
    bpy.types.Scene.lb_results = CollectionProperty(type=TutorialRecommendation)
    bpy.types.Scene.lb_bookmarks = CollectionProperty(type=BookmarkItem)
    bpy.types.Scene.lb_paths = CollectionProperty(type=PathCategory)
    bpy.types.Scene.lb_history = CollectionProperty(type=HistoryItem)
    
    bpy.types.Scene.lb_tab = bpy.props.EnumProperty(
        name="Tab",
        items=[
            ('SEARCH', "Search", "Search YouTube tutorials"),
            ('BOOKMARKS', "Bookmarks", "Saved tutorials"),
            ('PATHS', "Paths", "Learning paths"),
        ],
        default='SEARCH'
    )
    
    bpy.types.VIEW3D_MT_editor_menus.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_editor_menus.remove(menu_func)
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.lb_question
    del bpy.types.Scene.lb_current_question
    del bpy.types.Scene.lb_loading
    del bpy.types.Scene.lb_results
    del bpy.types.Scene.lb_bookmarks
    del bpy.types.Scene.lb_paths
    del bpy.types.Scene.lb_history
    del bpy.types.Scene.lb_tab


if __name__ == "__main__":
    register()