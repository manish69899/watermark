# keyboards.py - Advanced Watermark Bot Keyboards (Pyrogram Version)
# Features: Selected buttons turn GREEN, proper navigation, 2-column auto-layout

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ============================================
# STYLE KEYBOARD - with GREEN selection
# ============================================
def get_style_keyboard(selected: str = None):
    """
    Watermark style selection - selected style turns GREEN
    
    Styles: diagonal, grid, topright, bottomleft, overlay, border, header, footer
    """
    styles = [
        ('📍 Diagonal Center', 'style_diagonal'),
        ('▦ Grid / Tiled', 'style_grid'),
        ('↗️ Top Right Corner', 'style_topright'),
        ('↙️ Bottom Left Corner', 'style_bottomleft'),
        ('⬛ Full Page Overlay', 'style_overlay'),
        ('🔲 Border Frame', 'style_border'),
        ('📄 Header Only', 'style_header'),
        ('📋 Footer Only', 'style_footer')
    ]
    
    keyboard = []
    for name, data in styles:
        # GREEN button if selected
        if selected and data == f'style_{selected}':
            keyboard.append([InlineKeyboardButton(f"✅ {name}", callback_data=data)])
        else:
            keyboard.append([InlineKeyboardButton(name, callback_data=data)])
    
    return InlineKeyboardMarkup(keyboard)


# ============================================
# BORDER STYLE KEYBOARD - 12 Styles
# ============================================
def get_border_style_keyboard(selected: str = None):
    """
    Border style selection - 12 different border styles
    Selected border style turns GREEN
    """
    borders = [
        ('━ Simple Line', 'bstyle_simple'),
        ('═ Double Line', 'bstyle_double'),
        ('▓ Thick Border', 'bstyle_thick'),
        ('░ Dotted Border', 'bstyle_dotted'),
        ('✦ Star Border', 'bstyle_star'),
        ('◆ Diamond Border', 'bstyle_diamond'),
        ('● Circle Border', 'bstyle_circle'),
        ('■ Square Border', 'bstyle_square'),
        ('★ Glitter Border', 'bstyle_glitter'),
        ('◈ Elegant Border', 'bstyle_elegant'),
        ('✿ Flower Border', 'bstyle_flower'),
        ('❖ Corporate Border', 'bstyle_corporate')
    ]
    
    keyboard = []
    for name, data in borders:
        if selected and data == f'bstyle_{selected}':
            keyboard.append([InlineKeyboardButton(f"✅ {name}", callback_data=data)])
        else:
            keyboard.append([InlineKeyboardButton(name, callback_data=data)])
    
    # Add Skip button
    keyboard.append([InlineKeyboardButton("❌ Skip Border Style", callback_data='bstyle_skip')])
    
    return InlineKeyboardMarkup(keyboard)


# ============================================
# BORDER COLOR KEYBOARD
# ============================================
def get_border_color_keyboard(selected: str = None):
    """
    Border color selection - 12 colors
    Selected color turns GREEN
    """
    colors = [
        ('⚫ Grey', 'bcolor_grey'),
        ('🔴 Red', 'bcolor_red'),
        ('🔵 Blue', 'bcolor_blue'),
        ('🟢 Green', 'bcolor_green'),
        ('🟣 Purple', 'bcolor_purple'),
        ('🟠 Orange', 'bcolor_orange'),
        ('🟡 Gold', 'bcolor_gold'),
        ('⚪ Silver', 'bcolor_silver'),
        ('🖤 Black', 'bcolor_black'),
        ('💎 Cyan', 'bcolor_cyan'),
        ('🩷 Pink', 'bcolor_pink'),
        ('🟤 Brown', 'bcolor_brown')
    ]
    
    keyboard = []
    row = []
    for name, data in colors:
        if selected and data == f'bcolor_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:  # 2 buttons per row
            keyboard.append(row)
            row = []
    
    if row:  # Add remaining buttons
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)


# ============================================
# BORDER WIDTH KEYBOARD
# ============================================
def get_border_width_keyboard(selected: str = None):
    """
    Border width/thickness selection
    Selected width turns GREEN
    """
    widths = [
        ('┄ Thin (1pt)', 'bwidth_1'),
        ('─ Normal (2pt)', 'bwidth_2'),
        ('━ Medium (3pt)', 'bwidth_3'),
        ('█ Thick (5pt)', 'bwidth_5'),
        ('▓ Extra Thick (8pt)', 'bwidth_8'),
        ('█ Bold (10pt)', 'bwidth_10')
    ]
    
    keyboard = []
    row = []
    for name, data in widths:
        if selected and data == f'bwidth_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)


# ============================================
# COLOR KEYBOARD - For Watermark Text
# ============================================
def get_color_keyboard(selected: str = None):
    """
    Watermark text color selection - 12 colors
    Selected color turns GREEN
    """
    colors = [
        ('⚫ Grey', 'color_grey'),
        ('🔴 Red', 'color_red'),
        ('🔵 Blue', 'color_blue'),
        ('🟢 Green', 'color_green'),
        ('🟣 Purple', 'color_purple'),
        ('🟠 Orange', 'color_orange'),
        ('🟡 Yellow', 'color_yellow'),
        ('⚪ White', 'color_white'),
        ('🖤 Black', 'color_black'),
        ('💎 Cyan', 'color_cyan'),
        ('🩷 Pink', 'color_pink'),
        ('🟤 Brown', 'color_brown')
    ]
    
    keyboard = []
    row = []
    for name, data in colors:
        if selected and data == f'color_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)


# ============================================
# OPACITY KEYBOARD
# ============================================
def get_opacity_keyboard(selected: str = None):
    """
    Opacity selection - 8 levels
    Selected opacity turns GREEN
    """
    opacities = [
        ('☁️ Very Light (5%)', 'opac_0.05'),
        ('🌤 Light (10%)', 'opac_0.1'),
        ('⛅ Normal (20%)', 'opac_0.2'),
        ('🌤 Medium (30%)', 'opac_0.3'),
        ('🌥 Semi (50%)', 'opac_0.5'),
        ('🌩 Dark (70%)', 'opac_0.7'),
        ('🌧 Bold (85%)', 'opac_0.85'),
        ('⛈ Solid (95%)', 'opac_0.95')
    ]
    
    keyboard = []
    row = []
    for name, data in opacities:
        if selected and data == f'opac_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)


# ============================================
# FONT SIZE KEYBOARD
# ============================================
def get_fontsize_keyboard(selected: str = None):
    """
    Font size selection - 8 sizes
    Selected size turns GREEN
    """
    sizes = [
        ('🔍 XS (20pt)', 'fsize_20'),
        ('📝 Small (30pt)', 'fsize_30'),
        ('📰 Medium (40pt)', 'fsize_40'),
        ('📢 Large (50pt)', 'fsize_50'),
        ('📖 XL (60pt)', 'fsize_60'),
        ('🏛️ XXL (72pt)', 'fsize_72'),
        ('🔥 Huge (84pt)', 'fsize_84'),
        ('👑 Giant (96pt)', 'fsize_96')
    ]
    
    keyboard = []
    row = []
    for name, data in sizes:
        if selected and data == f'fsize_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)


# ============================================
# ROTATION KEYBOARD
# ============================================
def get_rotation_keyboard(selected: str = None):
    """
    Rotation angle selection
    Selected angle turns GREEN
    """
    rotations = [
        ('↗️ 45° Diagonal', 'rot_45'),
        ('➡️ 0° Horizontal', 'rot_0'),
        ('↙️ -45° Reverse', 'rot_-45'),
        ('⬇️ 90° Vertical', 'rot_90'),
        ('↖️ -90° Vertical', 'rot_-90'),
        ('🔄 Custom Angle', 'rot_custom')
    ]
    
    keyboard = []
    row = []
    for name, data in rotations:
        if selected and data == f'rot_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)


# ============================================
# IMAGE SIZE KEYBOARD (For Logo)
# ============================================
def get_imgsize_keyboard(selected: str = None):
    """
    Logo image size selection
    Selected size turns GREEN
    """
    sizes = [
        ('🔹 Small (60px)', 'isize_60'),
        ('🔸 Medium (100px)', 'isize_100'),
        ('🔶 Large (150px)', 'isize_150'),
        ('⭐ XL (200px)', 'isize_200'),
        ('📖 XXL (250px)', 'isize_250'),
        ('🏛️ Huge (300px)', 'isize_300')
    ]
    
    keyboard = []
    row = []
    for name, data in sizes:
        if selected and data == f'isize_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)


# ============================================
# LINK MENU KEYBOARD
# ============================================
def get_link_menu_keyboard(links_count: int = 0):
    """
    Link management menu
    Shows how many links are added
    """
    keyboard = []
    
    if links_count < 6:
        keyboard.append([InlineKeyboardButton("➕ Add New Link", callback_data='link_add')])
    
    if links_count > 0:
        keyboard.append([InlineKeyboardButton(f"📋 View Links ({links_count})", callback_data='link_view')])
        keyboard.append([InlineKeyboardButton("🗑️ Clear All Links", callback_data='link_clear')])
    
    keyboard.append([InlineKeyboardButton(f"✅ Done - Continue ({links_count} links)", callback_data='link_done')])
    
    return InlineKeyboardMarkup(keyboard)


# ============================================
# ADD OR SKIP LINK KEYBOARD
# ============================================
def get_link_add_skip_keyboard():
    """Initial link: Add or Skip"""
    keyboard = [
        [InlineKeyboardButton("➕ Add Link", callback_data='link_add')],
        [InlineKeyboardButton("❌ Skip (No Links)", callback_data='link_skip')]
    ]
    return InlineKeyboardMarkup(keyboard)


# ============================================
# LINK POSITION KEYBOARD
# ============================================
def get_link_position_keyboard(selected: str = None):
    """
    Link position selection - 6 positions
    Selected position turns GREEN
    """
    positions = [
        ('⬆️ Top Left', 'lpos_topleft'),
        ('⬆️ Top Center', 'lpos_topcenter'),
        ('⬆️ Top Right', 'lpos_topright'),
        ('⬇️ Bottom Left', 'lpos_bottomleft'),
        ('⬇️ Bottom Center', 'lpos_bottomcenter'),
        ('⬇️ Bottom Right', 'lpos_bottomright')
    ]
    
    keyboard = []
    row = []
    for name, data in positions:
        if selected and data == f'lpos_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)


# ============================================
# LINK TEXT STYLE KEYBOARD
# ============================================
def get_link_text_keyboard(selected: str = None):
    """
    Link button text style
    Selected style turns GREEN
    """
    styles = [
        ('🔗 CLICK HERE', 'ltext_click'),
        ('📱 VISIT US', 'ltext_visit'),
        ('🌐 OPEN LINK', 'ltext_open'),
        ('✨ LEARN MORE', 'ltext_learn'),
        ('📝 Custom Text', 'ltext_custom'),
        ('⚡ Show URL', 'ltext_url')
    ]
    
    keyboard = []
    row = []
    for name, data in styles:
        if selected and data == f'ltext_{selected}':
            row.append(InlineKeyboardButton(f"✅ {name}", callback_data=data))
        else:
            row.append(InlineKeyboardButton(name, callback_data=data))
        
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)


# ============================================
# ADD MORE LINK KEYBOARD
# ============================================
def get_add_more_link_keyboard(links_count: int = 0):
    """Ask if user wants to add more links"""
    keyboard = []
    
    if links_count < 6:
        keyboard.append([InlineKeyboardButton("➕ Add Another Link", callback_data='link_add')])
    
    keyboard.append([InlineKeyboardButton(f"✅ Done ({links_count} links added)", callback_data='link_done')])
    
    return InlineKeyboardMarkup(keyboard)


# ============================================
# METADATA KEYBOARD
# ============================================
def get_metadata_keyboard(selected: str = None):
    """
    Metadata: Yes or No
    Selected option turns GREEN
    """
    keyboard = []
    
    if selected == 'yes':
        keyboard.append([InlineKeyboardButton("✅ Yes (Add Metadata)", callback_data='meta_yes')])
    else:
        keyboard.append([InlineKeyboardButton("✅ Yes (Add Metadata)", callback_data='meta_yes')])
    
    if selected == 'no':
        keyboard.append([InlineKeyboardButton("✅ No (Skip)", callback_data='meta_no')])
    else:
        keyboard.append([InlineKeyboardButton("❌ No (Skip)", callback_data='meta_no')])
    
    return InlineKeyboardMarkup(keyboard)


# ============================================
# CONFIRMATION KEYBOARD
# ============================================
def get_confirm_keyboard():
    """Final confirmation before processing"""
    keyboard = [
        [InlineKeyboardButton("✅ Confirm & Process PDF", callback_data='confirm_yes')],
        [InlineKeyboardButton("🔄 Change Settings", callback_data='confirm_change')],
        [InlineKeyboardButton("❌ Cancel", callback_data='confirm_cancel')]
    ]
    return InlineKeyboardMarkup(keyboard)


# ============================================
# MAIN MENU KEYBOARD
# ============================================
def get_main_menu_keyboard():
    """Main menu at start"""
    keyboard = [
        [InlineKeyboardButton("📝 Text Watermark", callback_data='menu_text')],
        [InlineKeyboardButton("🖼️ Image/Logo Watermark", callback_data='menu_image')],
        [InlineKeyboardButton("❓ Help", callback_data='menu_help')]
    ]
    return InlineKeyboardMarkup(keyboard)


# ============================================
# SETTINGS KEYBOARD
# ============================================
def get_settings_keyboard():
    """Settings menu to change options"""
    keyboard = [
        [InlineKeyboardButton("🎨 Change Style", callback_data='set_style')],
        [InlineKeyboardButton("🌈 Change Color", callback_data='set_color')],
        [InlineKeyboardButton("💡 Change Opacity", callback_data='set_opacity')],
        [InlineKeyboardButton("🔤 Change Font Size", callback_data='set_fontsize')],
        [InlineKeyboardButton("🔲 Change Border", callback_data='set_border')],
        [InlineKeyboardButton("🔗 Manage Links", callback_data='set_links')],
        [InlineKeyboardButton("↩️ Back", callback_data='back_main')]
    ]
    return InlineKeyboardMarkup(keyboard)


# ============================================
# HELP KEYBOARD
# ============================================
def get_help_keyboard():
    """Help navigation"""
    keyboard = [
        [InlineKeyboardButton("📖 How to Use", callback_data='help_use')],
        [InlineKeyboardButton("🎨 Styles Guide", callback_data='help_styles')],
        [InlineKeyboardButton("🔗 Links Guide", callback_data='help_links')],
        [InlineKeyboardButton("↩️ Back", callback_data='back_main')]
    ]
    return InlineKeyboardMarkup(keyboard)