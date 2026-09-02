#!/usr/bin/env python3
import os
import sys
import shutil

# Add local bundled vendor
VENDOR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")
if os.path.exists(VENDOR_PATH):
    sys.path.insert(0, VENDOR_PATH)

os.environ["PYSDL2_DLL_PATH"] = "/usr/trimui/lib"

try:
    import sdl2
    import sdl2.ext
    import sdl2.sdlttf as sdlttf
    import sdl2.sdlimage as sdlimage
except ImportError as e:
    sys.stderr.write("Cannot load SDL2. Error: " + str(e))
    sys.exit(1)

FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "font.ttf")

# File manager visual tokens — shared with Calendar's warm retro palette.
FM_BG = (245, 241, 230)                 # #F5F1E6
FM_PANEL = (237, 232, 220)              # #EDE8DC
FM_TEXT = (51, 48, 43)                  # #33302B
FM_SECONDARY = (111, 106, 96)           # #6F6A60
FM_FOLDER = (107, 91, 149)              # #6B5B95
FM_FILE = (88, 112, 128)                # #587080
FM_SELECTED_BG = (229, 235, 241)        # #E5EBF1
FM_SELECTED_BORDER = (102, 137, 181)    # #6689B5
FM_WARNING = (182, 92, 92)              # #B65C5C
FM_GRID = (221, 215, 200)               # #DDD7C8

BG_COLOR = sdl2.ext.Color(*FM_BG)
TEXT_COLOR = sdl2.SDL_Color(*FM_TEXT, 255)
TEXT_DIM = sdl2.SDL_Color(*FM_SECONDARY, 255)
SEL_BG = sdl2.ext.Color(*FM_SELECTED_BG)
SEL_BORDER = sdl2.ext.Color(*FM_SELECTED_BORDER)
EDITOR_SEL_BG = sdl2.ext.Color(*FM_PANEL)
POPUP_BG = sdl2.ext.Color(*FM_PANEL)
HEADER_BG = sdl2.ext.Color(*FM_PANEL)

def draw_folder_icon(renderer, x, y):
    """Draw a compact monochrome folder without relying on emoji glyph support."""
    color = sdl2.ext.Color(*FM_FOLDER)
    renderer.fill((x + 2, y, 12, 5), color)
    renderer.fill((x, y + 4, 22, 15), color)

def draw_file_icon(renderer, x, y):
    """Draw a compact monochrome document icon for regular files."""
    color = sdl2.ext.Color(*FM_FILE)
    renderer.fill((x + 3, y, 14, 19), color)
    renderer.fill((x + 6, y + 4, 8, 2), BG_COLOR)
    renderer.fill((x + 6, y + 9, 8, 2), BG_COLOR)

# States
STATE_BROWSE = 0
STATE_OPTIONS = 1
STATE_CONFIRM_DELETE = 2
STATE_RENAME = 3
STATE_EDITOR = 4
STATE_QUIT_CONFIRM = 5

clipboard = None # {'path': str, 'action': 'copy' | 'move', 'name': str}

def get_directory_contents(path):
    try:
        items = os.listdir(path)
        folders = []
        files = []
        for item in items:
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                folders.append(item)
            else:
                files.append(item)
        folders.sort(key=str.lower)
        files.sort(key=str.lower)
        return folders, files
    except Exception as e:
        return [], []

def main():
    global clipboard
    sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_JOYSTICK | sdl2.SDL_INIT_GAMECONTROLLER)
    sdlttf.TTF_Init()

    controllers = []
    for i in range(sdl2.SDL_NumJoysticks()):
        if sdl2.SDL_IsGameController(i):
            c = sdl2.SDL_GameControllerOpen(i)
            if c:
                controllers.append(c)

    window = sdl2.ext.Window("FileManager", size=(1024, 768), flags=sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP)
    window.show()
    renderer = sdl2.ext.Renderer(window)

    font_path = FONT_PATH.encode('utf-8')
    if not os.path.exists(FONT_PATH):
        sys.exit(1)
        
    font_large = sdlttf.TTF_OpenFont(font_path, 48)
    font_medium = sdlttf.TTF_OpenFont(font_path, 32)
    font_small = sdlttf.TTF_OpenFont(font_path, 24)

    def render_text(text, font, color):
        tsurf = sdlttf.TTF_RenderUTF8_Blended(font, text.encode('utf-8'), color)
        if tsurf:
            ttex = sdl2.SDL_CreateTextureFromSurface(renderer.sdlrenderer, tsurf)
            w, h = tsurf.contents.w, tsurf.contents.h
            sdl2.SDL_FreeSurface(tsurf)
            return ttex, w, h
        return None, 0, 0

    current_path = "/mnt/SDCARD"
    folders, files = get_directory_contents(current_path)
    
    list_items = []
    def refresh_list():
        nonlocal folders, files, list_items
        folders, files = get_directory_contents(current_path)
        list_items = [{"name": f, "is_dir": True} for f in folders] + [{"name": f, "is_dir": False} for f in files]
        
    refresh_list()
    
    state = STATE_BROWSE
    state_before_quit = STATE_BROWSE
    
    # Browse state
    sel_index = 0
    scroll_y = 0
    item_height = 50
    visible_items = 12
    
    # Options state
    options_menu = []
    opt_index = 0
    
    # Rename state
    osk_keys_lower = [
        ['q','w','e','r','t','y','u','i','o','p','1','2','3'],
        ['a','s','d','f','g','h','j','k','l','-','4','5','6'],
        ['z','x','c','v','b','n','m','.','_','@','7','8','9'],
        ['SPACE', 'CLEAR', 'OK', 'CANCEL']
    ]
    osk_keys_upper = [
        ['Q','W','E','R','T','Y','U','I','O','P','1','2','3'],
        ['A','S','D','F','G','H','J','K','L','-','4','5','6'],
        ['Z','X','C','V','B','N','M','.','_','@','7','8','9'],
        ['SPACE', 'CLEAR', 'OK', 'CANCEL']
    ]
    osk_keys_symbols = [
        ['!','@','#','$','%','^','&','*','(',')','-','+','='],
        ['{','}','[',']','|','\\',':',';','"','\'','<','>','?'],
        ['0','1','2','3','4','5','6','7','8','9','/','`','~'],
        ['SPACE', 'CLEAR', 'OK', 'CANCEL']
    ]
    osk_x, osk_y = 0, 0
    osk_mode = 0 # 0: lower, 1: upper, 2: symbols
    rename_text = ""
    rename_cursor = 0
    rename_undo_stack = []
    rename_redo_stack = []
    
    target_item = None # Item being operated on
    
    dpad_up_held = False
    dpad_down_held = False
    dpad_left_held = False
    dpad_right_held = False
    dpad_timer = 0
    dpad_horiz_timer = 0
    
    preview_path = None
    preview_tex = None
    preview_w, preview_h = 0, 0
    
    editor_lines = []
    editor_cx, editor_cy = 0, 0
    editor_scroll_x, editor_scroll_y = 0, 0
    editor_mode = 'NAV'
    l2_pressed = False
    r2_pressed = False

    running = True
    while running:
        needs_redraw = True
        
        # Poll Joystick Axes
        axis_up = False
        axis_down = False
        axis_left = False
        axis_right = False
        for c in controllers:
            lx = sdl2.SDL_GameControllerGetAxis(c, sdl2.SDL_CONTROLLER_AXIS_LEFTX)
            ly = sdl2.SDL_GameControllerGetAxis(c, sdl2.SDL_CONTROLLER_AXIS_LEFTY)
            rx = sdl2.SDL_GameControllerGetAxis(c, sdl2.SDL_CONTROLLER_AXIS_RIGHTX)
            ry = sdl2.SDL_GameControllerGetAxis(c, sdl2.SDL_CONTROLLER_AXIS_RIGHTY)
            ax = lx if abs(lx) >= abs(rx) else rx
            ay = ly if abs(ly) >= abs(ry) else ry
            if ay < -15000: axis_up = True
            elif ay > 15000: axis_down = True
            if ax < -15000: axis_left = True
            elif ax > 15000: axis_right = True

        is_up = dpad_up_held or axis_up
        is_down = dpad_down_held or axis_down
        is_left = dpad_left_held or axis_left
        is_right = dpad_right_held or axis_right
        events = sdl2.ext.get_events()
        if len(events) > 0:
            needs_redraw = True
            
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
            elif event.type == sdl2.SDL_KEYDOWN:
                key = event.key.keysym.sym
                if key == sdl2.SDLK_ESCAPE:
                    running = False
                elif key == sdl2.SDLK_e:
                    if state == STATE_RENAME:
                        rename_cursor = max(0, rename_cursor - 1)
                elif key == sdl2.SDLK_t:
                    if state == STATE_RENAME:
                        rename_cursor = min(len(rename_text), rename_cursor + 1)
            elif event.type == sdl2.SDL_CONTROLLERAXISMOTION:
                axis = event.caxis.axis
                val = event.caxis.value
                if axis == sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT:
                    if val > 16000 and not l2_pressed:
                        l2_pressed = True
                        if state == STATE_RENAME:
                            rename_cursor = max(0, rename_cursor - 1)
                    elif val <= 16000:
                        l2_pressed = False
                elif axis == sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT:
                    if val > 16000 and not r2_pressed:
                        r2_pressed = True
                        if state == STATE_RENAME:
                            rename_cursor = min(len(rename_text), rename_cursor + 1)
                    elif val <= 16000:
                        r2_pressed = False
            elif event.type == sdl2.SDL_CONTROLLERBUTTONUP:
                btn = event.cbutton.button
                if btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP:
                    dpad_up_held = False
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN:
                    dpad_down_held = False
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT:
                    dpad_left_held = False
                elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT:
                    dpad_right_held = False
            elif event.type == sdl2.SDL_CONTROLLERBUTTONDOWN:
                btn = event.cbutton.button
                
                if btn == sdl2.SDL_CONTROLLER_BUTTON_START:
                    state_before_quit = state
                    state = STATE_QUIT_CONFIRM
                    
                if state == STATE_BROWSE:
                    if btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP:
                        dpad_up_held = True
                        dpad_timer = 0
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN:
                        dpad_down_held = True
                        dpad_timer = 0
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT:
                        dpad_left_held = True
                        dpad_horiz_timer = 0
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT:
                        dpad_right_held = True
                        dpad_horiz_timer = 0
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER: # Page Up
                        sel_index = max(0, sel_index - visible_items)
                        scroll_y = max(0, scroll_y - visible_items)
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER: # Page Down
                        sel_index = min(len(list_items) - 1, sel_index + visible_items)
                        scroll_y = min(max(0, len(list_items) - visible_items), scroll_y + visible_items)
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_A: # Physical B - Back
                        if current_path != "/":
                            current_path = os.path.dirname(current_path)
                            refresh_list()
                            sel_index = 0
                            scroll_y = 0
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_B: # Physical A - Enter
                        if len(list_items) > 0:
                            item = list_items[sel_index]
                            if item["is_dir"]:
                                current_path = os.path.join(current_path, item["name"])
                                refresh_list()
                                sel_index = 0
                                scroll_y = 0
                            elif item["name"].lower().endswith(('.txt', '.json', '.sh', '.md', '.py', '.cfg', '.ini')):
                                target_item = item
                                try:
                                    with open(os.path.join(current_path, item["name"]), 'r', encoding='utf-8') as f:
                                        editor_lines = f.read().split('\n')
                                except Exception:
                                    editor_lines = [""]
                                if len(editor_lines) == 0: editor_lines = [""]
                                editor_cx, editor_cy = 0, 0
                                editor_scroll_x, editor_scroll_y = 0, 0
                                editor_mode = 'NAV'
                                osk_x, osk_y = 0, 0
                                osk_mode = 0
                                undo_stack = []
                                state = STATE_EDITOR
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_BACK: # SELECT Button
                        if len(list_items) > 0:
                            target_item = list_items[sel_index]
                            options_menu = ["Rename", "Delete", "Move", "Copy"]
                            opt_index = 0
                            state = STATE_OPTIONS
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_X or btn == sdl2.SDL_CONTROLLER_BUTTON_Y:
                        if clipboard:
                            dest = os.path.join(current_path, clipboard['name'])
                            try:
                                if clipboard['action'] == 'move':
                                    shutil.move(clipboard['path'], dest)
                                    clipboard = None
                                else:
                                    if os.path.isdir(clipboard['path']):
                                        shutil.copytree(clipboard['path'], dest)
                                    else:
                                        shutil.copy2(clipboard['path'], dest)
                            except Exception:
                                pass
                            refresh_list()
                            
                elif state == STATE_OPTIONS:
                    if btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP:
                        opt_index = (opt_index - 1) % len(options_menu)
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN:
                        opt_index = (opt_index + 1) % len(options_menu)
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_A: # Back
                        state = STATE_BROWSE
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_B: # Select
                        opt = options_menu[opt_index]
                        full_target = os.path.join(current_path, target_item["name"])
                        if opt == "Rename":
                            rename_text = target_item["name"]
                            rename_cursor = len(rename_text)
                            rename_undo_stack = []
                            rename_redo_stack = []
                            osk_x, osk_y = 0, 0
                            osk_mode = 0
                            state = STATE_RENAME
                        elif opt == "Delete":
                            state = STATE_CONFIRM_DELETE
                        elif opt == "Move":
                            clipboard = {'path': full_target, 'action': 'move', 'name': target_item["name"]}
                            state = STATE_BROWSE
                        elif opt == "Copy":
                            clipboard = {'path': full_target, 'action': 'copy', 'name': target_item["name"]}
                            state = STATE_BROWSE
                            
                elif state == STATE_CONFIRM_DELETE:
                    if btn == sdl2.SDL_CONTROLLER_BUTTON_A: # Physical B - Cancel
                        state = STATE_BROWSE
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_B: # Confirm
                        full_target = os.path.join(current_path, target_item["name"])
                        try:
                            if target_item["is_dir"]: shutil.rmtree(full_target)
                            else: os.remove(full_target)
                        except:
                            pass
                        refresh_list()
                        sel_index = min(sel_index, max(0, len(list_items) - 1))
                        state = STATE_BROWSE
                        
                elif state == STATE_QUIT_CONFIRM:
                    if btn == sdl2.SDL_CONTROLLER_BUTTON_B: # Physical A - Confirm
                        running = False
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_A: # Physical B - Cancel
                        state = state_before_quit
                        
                elif state == STATE_RENAME:
                    current_keys = osk_keys_lower if osk_mode == 0 else (osk_keys_upper if osk_mode == 1 else osk_keys_symbols)
                    if btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP:
                        osk_y = (osk_y - 1) % 4
                        osk_x = min(osk_x, len(current_keys[osk_y]) - 1)
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN:
                        osk_y = (osk_y + 1) % 4
                        osk_x = min(osk_x, len(current_keys[osk_y]) - 1)
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT:
                        osk_x = (osk_x - 1) % len(current_keys[osk_y])
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT:
                        osk_x = (osk_x + 1) % len(current_keys[osk_y])
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER:
                        osk_mode = (osk_mode - 1) % 3
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER:
                        osk_mode = (osk_mode + 1) % 3
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_X: # Physical Y on TrimUI
                        if rename_undo_stack:
                            rename_redo_stack.append((rename_text, rename_cursor))
                            rename_text, rename_cursor = rename_undo_stack.pop()
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_Y: # Physical X on TrimUI
                        if rename_redo_stack:
                            rename_undo_stack.append((rename_text, rename_cursor))
                            rename_text, rename_cursor = rename_redo_stack.pop()
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_LEFTSTICK:
                        rename_cursor = max(0, rename_cursor - 1)
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_RIGHTSTICK:
                        rename_cursor = min(len(rename_text), rename_cursor + 1)
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_A: # Physical B on TrimUI - Delete char
                        if rename_cursor > 0:
                            rename_undo_stack.append((rename_text, rename_cursor))
                            rename_redo_stack.clear()
                            rename_text = rename_text[:rename_cursor-1] + rename_text[rename_cursor:]
                            rename_cursor -= 1
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_BACK: # SELECT to cancel
                        state = STATE_BROWSE
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_B: # Physical A - Select Key
                        key_val = current_keys[osk_y][osk_x]
                        if key_val == 'SPACE':
                            rename_undo_stack.append((rename_text, rename_cursor))
                            rename_redo_stack.clear()
                            rename_text = rename_text[:rename_cursor] + ' ' + rename_text[rename_cursor:]
                            rename_cursor += 1
                        elif key_val == 'CLEAR':
                            rename_undo_stack.append((rename_text, rename_cursor))
                            rename_redo_stack.clear()
                            rename_text = ""
                            rename_cursor = 0
                        elif key_val == 'CANCEL':
                            state = STATE_BROWSE
                        elif key_val == 'OK':
                            old_path = os.path.join(current_path, target_item["name"])
                            new_path = os.path.join(current_path, rename_text)
                            try:
                                os.rename(old_path, new_path)
                            except:
                                pass
                            refresh_list()
                            state = STATE_BROWSE
                        elif key_val != '':
                            rename_undo_stack.append((rename_text, rename_cursor))
                            rename_redo_stack.clear()
                            rename_text = rename_text[:rename_cursor] + key_val + rename_text[rename_cursor:]
                            rename_cursor += 1
                elif state == STATE_EDITOR:
                    current_keys = osk_keys_lower if osk_mode == 0 else (osk_keys_upper if osk_mode == 1 else osk_keys_symbols)
                    if btn == sdl2.SDL_CONTROLLER_BUTTON_BACK: # SELECT: Save and quit
                        try:
                            with open(os.path.join(current_path, target_item["name"]), 'w', encoding='utf-8') as f:
                                f.write('\n'.join(editor_lines))
                        except: pass
                        state = STATE_BROWSE
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_Y: # Physical X (Top) -> Toggle mode
                        editor_mode = 'OSK' if editor_mode == 'NAV' else 'NAV'
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_X: # Physical Y (Left) -> Undo
                        if undo_stack:
                            editor_lines, editor_cx, editor_cy = undo_stack.pop()
                    elif btn == sdl2.SDL_CONTROLLER_BUTTON_A: # Delete
                        line = editor_lines[editor_cy]
                        if editor_cx > 0:
                            undo_stack.append((editor_lines[:], editor_cx, editor_cy))
                            editor_lines[editor_cy] = line[:editor_cx-1] + line[editor_cx:]
                            editor_cx -= 1
                        elif editor_cy > 0:
                            undo_stack.append((editor_lines[:], editor_cx, editor_cy))
                            prev_line = editor_lines[editor_cy-1]
                            editor_cx = len(prev_line)
                            editor_lines[editor_cy-1] = prev_line + line
                            editor_lines.pop(editor_cy)
                            editor_cy -= 1
                    elif editor_mode == 'NAV':
                        if btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP:
                            editor_cy = max(0, editor_cy - 1)
                            editor_cx = min(editor_cx, len(editor_lines[editor_cy]))
                        elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN:
                            editor_cy = min(len(editor_lines) - 1, editor_cy + 1)
                            editor_cx = min(editor_cx, len(editor_lines[editor_cy]))
                        elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT:
                            editor_cx = max(0, editor_cx - 1)
                        elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT:
                            editor_cx = min(len(editor_lines[editor_cy]), editor_cx + 1)
                    elif editor_mode == 'OSK':
                        if btn == sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER:
                            osk_mode = (osk_mode - 1) % 3
                        elif btn == sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER:
                            osk_mode = (osk_mode + 1) % 3
                        elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP:
                            osk_y = (osk_y - 1) % 4
                            osk_x = min(osk_x, len(current_keys[osk_y]) - 1)
                        elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN:
                            osk_y = (osk_y + 1) % 4
                            osk_x = min(osk_x, len(current_keys[osk_y]) - 1)
                        elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT:
                            osk_x = (osk_x - 1) % len(current_keys[osk_y])
                        elif btn == sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT:
                            osk_x = (osk_x + 1) % len(current_keys[osk_y])
                        elif btn == sdl2.SDL_CONTROLLER_BUTTON_B:
                            key_val = current_keys[osk_y][osk_x]
                            line = editor_lines[editor_cy]
                            if key_val == 'SPACE':
                                undo_stack.append((editor_lines[:], editor_cx, editor_cy))
                                editor_lines[editor_cy] = line[:editor_cx] + ' ' + line[editor_cx:]
                                editor_cx += 1
                            elif key_val == 'OK' or key_val == 'ENTER':
                                undo_stack.append((editor_lines[:], editor_cx, editor_cy))
                                editor_lines[editor_cy] = line[:editor_cx]
                                editor_lines.insert(editor_cy + 1, line[editor_cx:])
                                editor_cy += 1
                                editor_cx = 0
                            elif key_val == 'CLEAR':
                                undo_stack.append((editor_lines[:], editor_cx, editor_cy))
                                editor_lines[editor_cy] = ""
                                editor_cx = 0
                            elif key_val == 'CANCEL':
                                state = STATE_BROWSE # Cancel without saving
                            elif key_val != '':
                                undo_stack.append((editor_lines[:], editor_cx, editor_cy))
                                editor_lines[editor_cy] = line[:editor_cx] + key_val + line[editor_cx:]
                                editor_cx += 1

        # Key repeat logic outside events
        if state == STATE_BROWSE:
            if is_up:
                if dpad_timer == 0 or (dpad_timer > 15 and dpad_timer % 3 == 0):
                    if len(list_items) > 0:
                        if sel_index == 0:
                            sel_index = len(list_items) - 1
                            scroll_y = max(0, len(list_items) - visible_items)
                        else:
                            sel_index -= 1
                            if sel_index < scroll_y: scroll_y = sel_index
                    needs_redraw = True
                dpad_timer += 1
            elif is_down:
                if dpad_timer == 0 or (dpad_timer > 15 and dpad_timer % 3 == 0):
                    if len(list_items) > 0:
                        if sel_index == len(list_items) - 1:
                            sel_index = 0
                            scroll_y = 0
                        else:
                            sel_index += 1
                            if sel_index >= scroll_y + visible_items: scroll_y = sel_index - visible_items + 1
                    needs_redraw = True
                dpad_timer += 1
            else:
                dpad_timer = 0

            if is_left:
                if dpad_horiz_timer == 0 or (dpad_horiz_timer > 15 and dpad_horiz_timer % 4 == 0):
                    sel_index = max(0, sel_index - visible_items)
                    scroll_y = max(0, scroll_y - visible_items)
                    needs_redraw = True
                dpad_horiz_timer += 1
            elif is_right:
                if dpad_horiz_timer == 0 or (dpad_horiz_timer > 15 and dpad_horiz_timer % 4 == 0):
                    sel_index = min(len(list_items) - 1, sel_index + visible_items)
                    scroll_y = min(max(0, len(list_items) - visible_items), scroll_y + visible_items)
                    needs_redraw = True
                dpad_horiz_timer += 1
            else:
                dpad_horiz_timer = 0

        elif state == STATE_OPTIONS:
            if is_up:
                if dpad_timer == 0 or (dpad_timer > 15 and dpad_timer % 4 == 0):
                    opt_index = (opt_index - 1) % len(options_menu)
                    needs_redraw = True
                dpad_timer += 1
            elif is_down:
                if dpad_timer == 0 or (dpad_timer > 15 and dpad_timer % 4 == 0):
                    opt_index = (opt_index + 1) % len(options_menu)
                    needs_redraw = True
                dpad_timer += 1
            else:
                dpad_timer = 0

        elif state == STATE_RENAME:
            current_keys = osk_keys_lower if osk_mode == 0 else (osk_keys_upper if osk_mode == 1 else osk_keys_symbols)
            if is_up:
                if dpad_timer == 0 or (dpad_timer > 15 and dpad_timer % 4 == 0):
                    osk_y = (osk_y - 1) % 4
                    osk_x = min(osk_x, len(current_keys[osk_y]) - 1)
                    needs_redraw = True
                dpad_timer += 1
            elif is_down:
                if dpad_timer == 0 or (dpad_timer > 15 and dpad_timer % 4 == 0):
                    osk_y = (osk_y + 1) % 4
                    osk_x = min(osk_x, len(current_keys[osk_y]) - 1)
                    needs_redraw = True
                dpad_timer += 1
            else:
                dpad_timer = 0

            if is_left:
                if dpad_horiz_timer == 0 or (dpad_horiz_timer > 15 and dpad_horiz_timer % 4 == 0):
                    osk_x = (osk_x - 1) % len(current_keys[osk_y])
                    needs_redraw = True
                dpad_horiz_timer += 1
            elif is_right:
                if dpad_horiz_timer == 0 or (dpad_horiz_timer > 15 and dpad_horiz_timer % 4 == 0):
                    osk_x = (osk_x + 1) % len(current_keys[osk_y])
                    needs_redraw = True
                dpad_horiz_timer += 1
            else:
                dpad_horiz_timer = 0

        elif state == STATE_EDITOR:
            if editor_mode == 'NAV':
                if is_up:
                    if dpad_timer == 0 or (dpad_timer > 15 and dpad_timer % 3 == 0):
                        editor_cy = max(0, editor_cy - 1)
                        editor_cx = min(editor_cx, len(editor_lines[editor_cy]))
                        needs_redraw = True
                    dpad_timer += 1
                elif is_down:
                    if dpad_timer == 0 or (dpad_timer > 15 and dpad_timer % 3 == 0):
                        editor_cy = min(len(editor_lines) - 1, editor_cy + 1)
                        editor_cx = min(editor_cx, len(editor_lines[editor_cy]))
                        needs_redraw = True
                    dpad_timer += 1
                else:
                    dpad_timer = 0

                if is_left:
                    if dpad_horiz_timer == 0 or (dpad_horiz_timer > 15 and dpad_horiz_timer % 3 == 0):
                        editor_cx = max(0, editor_cx - 1)
                        needs_redraw = True
                    dpad_horiz_timer += 1
                elif is_right:
                    if dpad_horiz_timer == 0 or (dpad_horiz_timer > 15 and dpad_horiz_timer % 3 == 0):
                        editor_cx = min(len(editor_lines[editor_cy]), editor_cx + 1)
                        needs_redraw = True
                    dpad_horiz_timer += 1
                else:
                    dpad_horiz_timer = 0
            elif editor_mode == 'OSK':
                current_keys = osk_keys_lower if osk_mode == 0 else (osk_keys_upper if osk_mode == 1 else osk_keys_symbols)
                if is_up:
                    if dpad_timer == 0 or (dpad_timer > 15 and dpad_timer % 4 == 0):
                        osk_y = (osk_y - 1) % 4
                        osk_x = min(osk_x, len(current_keys[osk_y]) - 1)
                        needs_redraw = True
                    dpad_timer += 1
                elif is_down:
                    if dpad_timer == 0 or (dpad_timer > 15 and dpad_timer % 4 == 0):
                        osk_y = (osk_y + 1) % 4
                        osk_x = min(osk_x, len(current_keys[osk_y]) - 1)
                        needs_redraw = True
                    dpad_timer += 1
                else:
                    dpad_timer = 0

                if is_left:
                    if dpad_horiz_timer == 0 or (dpad_horiz_timer > 15 and dpad_horiz_timer % 4 == 0):
                        osk_x = (osk_x - 1) % len(current_keys[osk_y])
                        needs_redraw = True
                    dpad_horiz_timer += 1
                elif is_right:
                    if dpad_horiz_timer == 0 or (dpad_horiz_timer > 15 and dpad_horiz_timer % 4 == 0):
                        osk_x = (osk_x + 1) % len(current_keys[osk_y])
                        needs_redraw = True
                    dpad_horiz_timer += 1
                else:
                    dpad_horiz_timer = 0
                
        if state == STATE_EDITOR:
            if editor_cy < editor_scroll_y:
                editor_scroll_y = editor_cy
                needs_redraw = True
            elif editor_cy >= editor_scroll_y + 10:
                editor_scroll_y = editor_cy - 9
                needs_redraw = True

        if needs_redraw:
            # Draw
            renderer.clear(BG_COLOR)
        w_w, w_h = 1024, 768
        
        # Header
        renderer.fill((0, 0, w_w, 80), HEADER_BG)
        renderer.fill((0, 78, w_w, 2), sdl2.ext.Color(*FM_GRID))
        tex, tw, th = render_text(current_path, font_medium, TEXT_COLOR)
        if tex:
            # clip path if too long
            if tw > w_w - 40:
                renderer.set_clip_rect((20, 20, w_w - 40, th))
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(w_w - 20 - tw, 25, tw, th))
                renderer.set_clip_rect(None)
            else:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(20, 25, tw, th))
            sdl2.SDL_DestroyTexture(tex)
            
        # File List
        list_y = 100
        if len(list_items) == 0:
            tex, tw, th = render_text("(Empty Directory)", font_medium, TEXT_DIM)
            if tex:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(40, list_y, tw, th))
                sdl2.SDL_DestroyTexture(tex)
        else:
            for i in range(scroll_y, min(scroll_y + visible_items, len(list_items))):
                item = list_items[i]
                iy = list_y + (i - scroll_y) * item_height

                # Directory type remains filesystem metadata; the visible name is never altered.
                tex, tw, th = render_text(item["name"], font_medium, TEXT_COLOR)
                if tex:
                    if i == sel_index and state == STATE_BROWSE:
                        row_x, row_y, row_w, row_h = 20, iy + 2, w_w - 40, item_height - 4
                        renderer.fill((row_x, row_y, row_w, row_h), SEL_BORDER)
                        renderer.fill((row_x + 2, row_y + 2, row_w - 4, row_h - 4), SEL_BG)

                    icon_y = iy + (item_height - 19)//2
                    if item["is_dir"]:
                        draw_folder_icon(renderer, 34, icon_y)
                    else:
                        draw_file_icon(renderer, 34, icon_y)

                    render_w = min(tw, w_w - 90)
                    src_rect = sdl2.SDL_Rect(0, 0, render_w, th)
                    dst_rect = sdl2.SDL_Rect(66, iy + (item_height - th)//2, render_w, th)
                    sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, src_rect, dst_rect)
                    sdl2.SDL_DestroyTexture(tex)

        # Image Preview
        if state == STATE_BROWSE and len(list_items) > 0:
            sel_item = list_items[sel_index]
            if not sel_item["is_dir"] and sel_item["name"].lower().endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(current_path, sel_item["name"])
                if img_path != preview_path:
                    if preview_tex:
                        sdl2.SDL_DestroyTexture(preview_tex)
                        preview_tex = None
                    try:
                        surf = sdlimage.IMG_Load(img_path.encode('utf-8'))
                        if surf:
                            preview_w, preview_h = surf.contents.w, surf.contents.h
                            preview_tex = sdl2.SDL_CreateTextureFromSurface(renderer.sdlrenderer, surf)
                            sdl2.SDL_FreeSurface(surf)
                    except Exception:
                        pass
                    preview_path = img_path
                    
                if preview_tex:
                    # Draw scaled image on the right side
                    max_pw, max_ph = 400, 400
                    scale = min(max_pw / preview_w, max_ph / preview_h)
                    if scale > 1: scale = 1 # Don't upscale
                    
                    pw = int(preview_w * scale)
                    ph = int(preview_h * scale)
                    px = w_w - pw - 40
                    py = 150
                    
                    renderer.fill((px-2, py-2, pw+4, ph+4), sdl2.ext.Color(*FM_GRID))
                    sdl2.SDL_RenderCopy(renderer.sdlrenderer, preview_tex, None, sdl2.SDL_Rect(px, py, pw, ph))
            else:
                if preview_tex:
                    sdl2.SDL_DestroyTexture(preview_tex)
                    preview_tex = None
                    preview_path = None

        # Draw Overlays
        if state == STATE_OPTIONS:
            # Dim background
            sdl2.SDL_SetRenderDrawBlendMode(renderer.sdlrenderer, sdl2.SDL_BLENDMODE_BLEND)
            sdl2.SDL_SetRenderDrawColor(renderer.sdlrenderer, *FM_TEXT, 110)
            sdl2.SDL_RenderFillRect(renderer.sdlrenderer, sdl2.SDL_Rect(0, 0, w_w, w_h))
            
            pop_w, pop_h = 600, len(options_menu) * 60 + 40
            pop_x, pop_y = (w_w - pop_w)//2, (w_h - pop_h)//2
            renderer.fill((pop_x, pop_y, pop_w, pop_h), POPUP_BG)
            renderer.fill((pop_x, pop_y, pop_w, 2), sdl2.ext.Color(*FM_GRID))
            
            for i, opt in enumerate(options_menu):
                oy = pop_y + 20 + i * 60
                if i == opt_index:
                    renderer.fill((pop_x + 10, oy, pop_w - 20, 60), SEL_BORDER)
                    renderer.fill((pop_x + 12, oy + 2, pop_w - 24, 56), SEL_BG)
                tex, tw, th = render_text(opt, font_medium, TEXT_COLOR)
                if tex:
                    sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(pop_x + 30, oy + 15, tw, th))
                    sdl2.SDL_DestroyTexture(tex)
                    
        elif state == STATE_CONFIRM_DELETE:
            sdl2.SDL_SetRenderDrawBlendMode(renderer.sdlrenderer, sdl2.SDL_BLENDMODE_BLEND)
            sdl2.SDL_SetRenderDrawColor(renderer.sdlrenderer, *FM_TEXT, 110)
            sdl2.SDL_RenderFillRect(renderer.sdlrenderer, sdl2.SDL_Rect(0, 0, w_w, w_h))
            
            pop_w, pop_h = 700, 200
            pop_x, pop_y = (w_w - pop_w)//2, (w_h - pop_h)//2
            renderer.fill((pop_x, pop_y, pop_w, pop_h), POPUP_BG)
            renderer.fill((pop_x, pop_y, pop_w, 2), sdl2.ext.Color(*FM_WARNING))
            
            tex, tw, th = render_text(f"Delete '{target_item['name']}'?", font_medium, TEXT_COLOR)
            if tex:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(pop_x + pop_w//2 - tw//2, pop_y + 50, tw, th))
                sdl2.SDL_DestroyTexture(tex)
                
            tex, tw, th = render_text("A: Confirm   B: Cancel", font_small, TEXT_DIM)
            if tex:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(pop_x + pop_w//2 - tw//2, pop_y + 120, tw, th))
                sdl2.SDL_DestroyTexture(tex)
                
        elif state == STATE_QUIT_CONFIRM:
            sdl2.SDL_SetRenderDrawBlendMode(renderer.sdlrenderer, sdl2.SDL_BLENDMODE_BLEND)
            sdl2.SDL_SetRenderDrawColor(renderer.sdlrenderer, *FM_TEXT, 110)
            sdl2.SDL_RenderFillRect(renderer.sdlrenderer, sdl2.SDL_Rect(0, 0, w_w, w_h))
            
            pop_w, pop_h = 600, 200
            pop_x, pop_y = (w_w - pop_w)//2, (w_h - pop_h)//2
            renderer.fill((pop_x, pop_y, pop_w, pop_h), POPUP_BG)
            renderer.fill((pop_x, pop_y, pop_w, 2), sdl2.ext.Color(*FM_GRID))
            
            tex, tw, th = render_text("Exit Files?", font_large, TEXT_COLOR)
            if tex:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(pop_x + pop_w//2 - tw//2, pop_y + 40, tw, th))
                sdl2.SDL_DestroyTexture(tex)
                
            tex, tw, th = render_text("A: Confirm   B: Cancel", font_medium, TEXT_DIM)
            if tex:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(pop_x + pop_w//2 - tw//2, pop_y + 120, tw, th))
                sdl2.SDL_DestroyTexture(tex)
                
        elif state == STATE_RENAME:
            sdl2.SDL_SetRenderDrawBlendMode(renderer.sdlrenderer, sdl2.SDL_BLENDMODE_BLEND)
            sdl2.SDL_SetRenderDrawColor(renderer.sdlrenderer, *FM_TEXT, 120)
            sdl2.SDL_RenderFillRect(renderer.sdlrenderer, sdl2.SDL_Rect(0, 0, w_w, w_h))
            
            pop_w, pop_h = w_w - 100, 210
            pop_x, pop_y = 50, 110
            field_x, field_y = pop_x + 24, pop_y + 92
            field_w, field_h = pop_w - 48, 58

            renderer.fill((pop_x, pop_y, pop_w, pop_h), POPUP_BG)
            renderer.fill((pop_x, pop_y, pop_w, 2), sdl2.ext.Color(*FM_GRID))
            renderer.fill((field_x - 2, field_y - 2, field_w + 4, field_h + 4), SEL_BORDER)
            renderer.fill((field_x, field_y, field_w, field_h), BG_COLOR)

            tex, tw, th = render_text("New name", font_medium, TEXT_COLOR)
            if tex:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(pop_x + 24, pop_y + 30, tw, th))
                sdl2.SDL_DestroyTexture(tex)

            display_text = rename_text[:rename_cursor] + "|" + rename_text[rename_cursor:]
            tex, tw, th = render_text(display_text if display_text else "|", font_medium, TEXT_COLOR)
            if tex:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(field_x + 16, field_y + (field_h - th)//2, min(tw, field_w - 32), th))
                sdl2.SDL_DestroyTexture(tex)
                
        elif state == STATE_EDITOR:
            renderer.fill((0, 0, w_w, 420), BG_COLOR)
            y_start = 10
            for i in range(editor_scroll_y, min(editor_scroll_y + 10, len(editor_lines))):
                line = editor_lines[i]
                iy = y_start + (i - editor_scroll_y) * 40
                if i == editor_cy:
                    renderer.fill((0, iy, w_w, 40), EDITOR_SEL_BG)
                tex, tw, th = render_text(line if line else " ", font_small, TEXT_COLOR)
                if tex:
                    src_rect = sdl2.SDL_Rect(editor_scroll_x, 0, min(tw, w_w - 20), th)
                    dst_rect = sdl2.SDL_Rect(10, iy + (40-th)//2, src_rect.w, th)
                    if src_rect.w > 0:
                        sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, src_rect, dst_rect)
                    sdl2.SDL_DestroyTexture(tex)
                if i == editor_cy:
                    prefix = line[:editor_cx]
                    ptex, ptw, pth = render_text(prefix if prefix else " ", font_small, TEXT_COLOR)
                    cx_px = 10 + (ptw if prefix else 0) - editor_scroll_x
                    if ptex: sdl2.SDL_DestroyTexture(ptex)
                    # Keep the two editor modes easy to distinguish and blink the active cursor.
                    if (sdl2.SDL_GetTicks() // 500) % 2 == 0:
                        c_color = sdl2.ext.Color(*FM_WARNING) if editor_mode == 'OSK' else sdl2.ext.Color(76, 139, 92)
                        renderer.fill((cx_px, iy+5, 2, 30), c_color)
                    
        if state == STATE_RENAME or state == STATE_EDITOR:
            # Draw OSK
            current_keys = osk_keys_lower if osk_mode == 0 else (osk_keys_upper if osk_mode == 1 else osk_keys_symbols)
            osk_start_y = 420
            kh = 65
            pad = 10
            for r in range(4):
                row_len = len(current_keys[r])
                if row_len == 13:
                    kw = 65
                    total_w = 13 * kw + 12 * pad
                    start_x = (w_w - total_w) // 2
                    pad_x = pad
                else: # bottom row (4 keys)
                    total_w = 13 * 65 + 12 * pad # match width of upper rows
                    pad_x = 20
                    kw = (total_w - (row_len - 1) * pad_x) // row_len
                    start_x = (w_w - total_w) // 2
                    
                for c in range(row_len):
                    key_val = current_keys[r][c]
                    kx = start_x + c * (kw + pad_x)
                    ky = osk_start_y + r * (kh + pad)
                    
                    b_color = POPUP_BG
                    if r == osk_y and c == osk_x:
                        b_color = SEL_BG
                        renderer.fill((kx-3, ky-3, kw+6, kh+6), SEL_BORDER)
                        
                    renderer.fill((kx, ky, kw, kh), b_color)
                    
                    font_to_use = font_small if len(key_val) > 1 else font_medium
                    tex, tw, th = render_text(key_val, font_to_use, TEXT_COLOR)
                    if tex:
                        sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(kx + kw//2 - tw//2, ky + kh//2 - th//2, tw, th))
                        sdl2.SDL_DestroyTexture(tex)

        # Footer hints
        if state == STATE_BROWSE:
            paste_hint = "| X/Y: Paste " if clipboard else ""
            footer = f"D-PAD: Navigate | A: Enter | B: Back | SELECT: Options {paste_hint}| START: Exit"
            tex, tw, th = render_text(footer, font_small, TEXT_COLOR)
            if tex:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(20, w_h - 40, tw, th))
                sdl2.SDL_DestroyTexture(tex)
        elif state == STATE_RENAME:
            footer = "L/R: Caps/Sym | A: Enter | B: Del | L2/R2: Cursor | X: Redo | Y: Undo | SEL: Cancel"
            tex, tw, th = render_text(footer, font_small, TEXT_COLOR)
            if tex:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(20, w_h - 40, tw, th))
                sdl2.SDL_DestroyTexture(tex)
        elif state == STATE_EDITOR:
            mode_str = "[OSK]" if editor_mode == 'OSK' else "[NAV]"
            footer = f"X: {mode_str} | Y: Undo | L/R: Caps | SELECT: Save&Quit | B: Del"
            tex, tw, th = render_text(footer, font_small, TEXT_COLOR)
            if tex:
                sdl2.SDL_RenderCopy(renderer.sdlrenderer, tex, None, sdl2.SDL_Rect(20, w_h - 40, tw, th))
                sdl2.SDL_DestroyTexture(tex)

        renderer.present()
        needs_redraw = False
            
        sdl2.SDL_Delay(16)

    if preview_tex:
        sdl2.SDL_DestroyTexture(preview_tex)
    sdlttf.TTF_CloseFont(font_large)
    sdlttf.TTF_CloseFont(font_medium)
    sdlttf.TTF_CloseFont(font_small)
    sdlttf.TTF_Quit()
    sdlimage.IMG_Quit()
    sdl2.SDL_Quit()

if __name__ == "__main__":
    main()
