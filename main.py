# main.py - Advanced Watermark Bot for Telegram (PYROGRAM VERSION)
# FIXED VERSION - 100% MTProto Bypass for strict file names

import os
import shutil
import zipfile
import logging
import html
import time
import re

# 🔴 PYROGRAM IMPORTS (Replaced python-telegram-bot)
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.enums import ParseMode

# API_ID aur API_HASH import kiye gaye hain config se
from config import BOT_TOKEN, API_ID, API_HASH, DOWNLOAD_DIR, OUTPUT_DIR
import keyboards as kb
from watermark import add_watermark_to_pdf, get_pdf_page_count
from pypdf import PdfReader

# ============================================
# LOGGING SETUP
# ============================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 🔴 YEH LINE ADD KARO - Isse Pyrogram ke faltu connect/disconnect logs hide ho jayenge
logging.getLogger("pyrogram").setLevel(logging.WARNING)

logger = logging.getLogger("WatermarkBot")

# ============================================
# PYROGRAM APP INITIALIZATION
# ============================================
app = Client(
    "WatermarkBotSession",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ============================================
# USER SESSION STORAGE
# ============================================
user_data = {}

def get_data(user_id: int) -> dict:
    """Get or create user session data with defaults"""
    if user_id not in user_data:
        user_data[user_id] = {
            'type': 'text',
            'content': '',
            'style': 'diagonal',
            'color': 'grey',
            'opacity': 0.3,
            'fontsize': 48,
            'rotation': 45,
            'imgsize': 150,
            'border_style': 'simple',
            'border_color': 'grey',
            'border_width': 2,
            'links': [],
            'add_metadata': False,
            'author': '',
            'location': '',
            'step': None,
            'temp_link_url': '',
            'temp_link_pos': '',
            'temp_link_text': ''
        }
    return user_data[user_id]

def clear_data(user_id: int):
    """Clear user session"""
    user_data[user_id] = {
        'type': 'text',
        'content': '',
        'style': 'diagonal',
        'color': 'grey',
        'opacity': 0.3,
        'fontsize': 48,
        'rotation': 45,
        'imgsize': 150,
        'border_style': 'simple',
        'border_color': 'grey',
        'border_width': 2,
        'links': [],
        'add_metadata': False,
        'author': '',
        'location': '',
        'step': None,
        'temp_link_url': '',
        'temp_link_pos': '',
        'temp_link_text': ''
    }

# ============================================
# SANITIZE FILENAME
# ============================================
def clean_filename(name: str) -> str:
    """Clean filename - remove invalid characters"""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = ''.join(c for c in name if ord(c) >= 32)
    if len(name) > 180:
        n, e = os.path.splitext(name)
        name = n[:180-len(e)] + e
    return name.strip() or "document.pdf"

# ============================================
# SHOW SUMMARY TO USER
# ============================================
def get_summary_text(data: dict) -> str:
    """Generate summary of what will be added to PDF"""
    lines = ["📋 *PDF ME YE ADD HOGA:*\n"]
    
    # Watermark type
    if data.get('type') == 'text' and data.get('content'):
        text = data['content'][:40]
        lines.append(f"📝 *Text:* `{text}`")
    elif data.get('type') == 'image':
        lines.append("🖼️ *Logo:* Image Watermark")
    
    # Style
    style = data.get('style', 'diagonal')
    lines.append(f"🎨 *Style:* {style.upper()}")
    
    # Border details if border style
    if style == 'border':
        bs = data.get('border_style', 'simple')
        bc = data.get('border_color', 'grey')
        bw = data.get('border_width', 2)
        lines.append(f"   └ Border: {bs.upper()}")
        lines.append(f"   └ Color: {bc.upper()}")
        lines.append(f"   └ Width: {bw}pt")
    
    # Color
    color = data.get('color', 'grey')
    lines.append(f"🌈 *Color:* {color.upper()}")
    
    # Opacity
    try:
        opacity = float(data.get('opacity', 0.3))
        pct = opacity * 100
        lines.append(f"💡 *Opacity:* {pct:.0f}%")
    except:
        lines.append(f"💡 *Opacity:* 30%")
    
    # Font size
    if data.get('type') == 'text':
        try:
            fs = int(data.get('fontsize', 48))
            lines.append(f"🔤 *Font:* {fs}pt")
        except:
            lines.append(f"🔤 *Font:* 48pt")
    
    # Rotation
    try:
        rot = int(data.get('rotation', 45))
        lines.append(f"↩️ *Rotation:* {rot}°")
    except:
        lines.append(f"↩️ *Rotation:* 45°")
    
    # Image size
    if data.get('type') == 'image':
        try:
            imgs = int(data.get('imgsize', 150))
            lines.append(f"📐 *Logo Size:* {imgs}px")
        except:
            lines.append(f"📐 *Logo Size:* 150px")
    
    # Links
    links = data.get('links', [])
    if links:
        lines.append(f"\n🔗 *LINKS ({len(links)}):*")
        for i, link in enumerate(links, 1):
            pos = link.get('position', 'bottomcenter').upper()
            txt = link.get('text', 'LINK')[:20]
            lines.append(f"   {i}. {txt} ({pos})")
    
    # Metadata
    if data.get('add_metadata'):
        lines.append(f"\n🕵️ *Metadata:* YES")
        if data.get('author'):
            lines.append(f"   └ Author: {data['author']}")
    
    return '\n'.join(lines)

# ============================================
# /START COMMAND
# ============================================
@app.on_message(filters.command("start"))
async def cmd_start(client: Client, message: Message):
    """Start command"""
    user_id = message.from_user.id
    clear_data(user_id)
    
    text = (
        "👋 *WATERMARK BOT*\n\n"
        "PDF me watermark add karo!\n\n"
        "✨ *Features:*\n"
        "• 📝 Text Watermark\n"
        "• 🖼 Logo/Image Watermark\n"
        "• 🎨 8 Styles, 12 Colors\n"
        "• 🔲 12 Border Styles\n"
        "• 🔗 Multiple Links\n"
        "• 📦 ZIP Support\n\n"
        "🚀 *Send TEXT or IMAGE to start!*"
    )
    
    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ============================================
# /HELP COMMAND
# ============================================
@app.on_message(filters.command("help"))
async def cmd_help(client: Client, message: Message):
    """Help command"""
    text = (
        "📖 *HOW TO USE*\n\n"
        "1️⃣ Send TEXT or IMAGE\n"
        "2️⃣ Choose STYLE\n"
        "3️⃣ Choose COLOR & OPACITY\n"
        "4️⃣ Add LINKS (optional)\n"
        "5️⃣ Add METADATA (optional)\n"
        "6️⃣ Send PDF/ZIP file\n\n"
        "📝 *Commands:*\n"
        "/start - Begin\n"
        "/reset - Clear settings\n"
        "/settings - View settings"
    )
    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ============================================
# /RESET COMMAND
# ============================================
@app.on_message(filters.command("reset"))
async def cmd_reset(client: Client, message: Message):
    """Reset settings"""
    user_id = message.from_user.id
    clear_data(user_id)
    await message.reply_text("🔄 *Settings cleared!*\n\nSend TEXT or IMAGE to start.", parse_mode=ParseMode.MARKDOWN)

# ============================================
# /SETTINGS COMMAND
# ============================================
@app.on_message(filters.command("settings"))
async def cmd_settings(client: Client, message: Message):
    """Show current settings"""
    user_id = message.from_user.id
    data = get_data(user_id)
    
    if not data.get('content'):
        await message.reply_text("⚠️ No settings. Send /start", parse_mode=ParseMode.MARKDOWN)
        return
    
    text = get_summary_text(data)
    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ============================================
# HANDLE TEXT INPUT
# ============================================
@app.on_message(filters.text & ~filters.command(["start", "help", "reset", "settings"]))
async def handle_text(client: Client, message: Message):
    """Handle text messages"""
    text = message.text
    user_id = message.from_user.id
    data = get_data(user_id)
    
    # Step: Waiting for metadata
    if data.get('step') == 'waiting_metadata':
        parts = text.split(',')
        data['author'] = parts[0].strip()
        data['location'] = parts[1].strip() if len(parts) > 1 else 'India'
        data['add_metadata'] = True
        data['step'] = None
        
        summary = get_summary_text(data)
        await message.reply_text(
            f"✅ *Metadata Saved!*\n\n{summary}\n\n📂 *Send PDF or ZIP file now!*",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Step: Waiting for custom rotation
    if data.get('step') == 'waiting_rotation':
        try:
            angle = int(text.strip())
            if -180 <= angle <= 180:
                data['rotation'] = angle
                data['step'] = None
                await message.reply_text(
                    f"✅ Rotation: {angle}°\n\n🔗 Add clickable links?",
                    reply_markup=kb.get_link_add_skip_keyboard(),
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await message.reply_text("⚠️ Enter angle between -180 and 180", parse_mode=ParseMode.MARKDOWN)
        except:
            await message.reply_text("⚠️ Enter valid number like: 45", parse_mode=ParseMode.MARKDOWN)
        return
    
    # Step: Waiting for link URL
    if data.get('step') == 'waiting_link_url':
        url = text.strip()
        if not url.startswith('http'):
            url = 'https://' + url
        
        data['temp_link_url'] = url
        data['step'] = None
        
        await message.reply_text(
            f"✅ Link URL saved!\n\n📍 Choose position for this link:",
            reply_markup=kb.get_link_position_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Step: Waiting for custom link text
    if data.get('step') == 'waiting_link_text':
        data['temp_link_text'] = text.strip()[:25]
        data['step'] = None
        
        # Add the link
        temp_url = data.get('temp_link_url', '')
        temp_pos = data.get('temp_link_pos', 'bottomcenter')
        temp_txt = data.get('temp_link_text', '🔗 CLICK HERE')
        
        if temp_url:
            data['links'].append({
                'url': temp_url,
                'position': temp_pos,
                'text': temp_txt
            })
            # Cleanup temp
            data['temp_link_url'] = ''
            data['temp_link_pos'] = ''
            data['temp_link_text'] = ''
        
        count = len(data['links'])
        await message.reply_text(
            f"✅ Link added! ({count}/6)\n\nAdd more or continue?",
            reply_markup=kb.get_add_more_link_keyboard(count),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Normal text = Watermark text
    if len(text) > 100:
        await message.reply_text("⚠️ Text too long! Max 100 chars.", parse_mode=ParseMode.MARKDOWN)
        return
    
    data['type'] = 'text'
    data['content'] = text.strip()
    
    # Auto font size based on text length
    if len(text) < 10:
        data['fontsize'] = 60
    elif len(text) < 25:
        data['fontsize'] = 48
    elif len(text) < 50:
        data['fontsize'] = 36
    else:
        data['fontsize'] = 28
    
    await message.reply_text(
        f"✅ Text: `{text}`\n\n🎨 Choose watermark style:",
        reply_markup=kb.get_style_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

# ============================================
# HANDLE PHOTO INPUT
# ============================================
@app.on_message(filters.photo)
async def handle_photo(client: Client, message: Message):
    """Handle photo messages"""
    user_id = message.from_user.id
    data = get_data(user_id)
    
    try:
        path = os.path.join(DOWNLOAD_DIR, f"logo_{user_id}_{int(time.time())}.png")
        # Pyrogram native download
        await message.download(file_name=path)
        
        data['type'] = 'image'
        data['content'] = path
        
        await message.reply_text(
            "✅ Logo saved!\n\n🎨 Choose watermark style:",
            reply_markup=kb.get_style_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Photo error: {e}")
        await message.reply_text("❌ Failed to save image. Try again.", parse_mode=ParseMode.MARKDOWN)

# ============================================
# HANDLE BUTTON CALLBACKS
# ============================================
@app.on_callback_query()
async def handle_callback(client: Client, query: CallbackQuery):
    """Handle all button clicks"""
    await query.answer()
    
    user_id = query.from_user.id
    data = get_data(user_id)
    cb = query.data
    
    try:
        # ========== STYLE SELECTION ==========
        if cb.startswith('style_'):
            style = cb.replace('style_', '')
            data['style'] = style
            
            if style == 'border':
                await query.edit_message_text(
                    "🔲 BORDER selected!\n\nChoose border style:",
                    reply_markup=kb.get_border_style_keyboard()
                )
            elif data.get('type') == 'text':
                await query.edit_message_text(
                    f"✅ Style: {style.upper()}\n\n🌈 Choose color:",
                    reply_markup=kb.get_color_keyboard()
                )
            else:
                await query.edit_message_text(
                    f"✅ Style: {style.upper()}\n\n📐 Choose logo size:",
                    reply_markup=kb.get_imgsize_keyboard()
                )
        
        # ========== BORDER STYLE ==========
        elif cb.startswith('bstyle_'):
            bstyle = cb.replace('bstyle_', '')
            
            if bstyle == 'skip':
                if data.get('type') == 'text':
                    await query.edit_message_text(
                        "🌈 Choose watermark color:",
                        reply_markup=kb.get_color_keyboard()
                    )
                else:
                    await query.edit_message_text(
                        "📐 Choose logo size:",
                        reply_markup=kb.get_imgsize_keyboard()
                    )
            else:
                data['border_style'] = bstyle
                await query.edit_message_text(
                    f"✅ Border: {bstyle.upper()}\n\n🎨 Choose border color:",
                    reply_markup=kb.get_border_color_keyboard()
                )
        
        # ========== BORDER COLOR ==========
        elif cb.startswith('bcolor_'):
            bcolor = cb.replace('bcolor_', '')
            data['border_color'] = bcolor
            
            await query.edit_message_text(
                f"✅ Border Color: {bcolor.upper()}\n\n📏 Choose border width:",
                reply_markup=kb.get_border_width_keyboard()
            )
        
        # ========== BORDER WIDTH ==========
        elif cb.startswith('bwidth_'):
            bwidth = cb.replace('bwidth_', '')
            data['border_width'] = int(bwidth)  # Convert to int
            
            if data.get('type') == 'text':
                await query.edit_message_text(
                    f"✅ Border Width: {bwidth}pt\n\n🌈 Choose text color:",
                    reply_markup=kb.get_color_keyboard()
                )
            else:
                await query.edit_message_text(
                    f"✅ Border Width: {bwidth}pt\n\n📐 Choose logo size:",
                    reply_markup=kb.get_imgsize_keyboard()
                )
        
        # ========== COLOR ==========
        elif cb.startswith('color_'):
            color = cb.replace('color_', '')
            data['color'] = color
            
            await query.edit_message_text(
                f"✅ Color: {color.upper()}\n\n💡 Choose opacity:",
                reply_markup=kb.get_opacity_keyboard()
            )
        
        # ========== OPACITY ==========
        elif cb.startswith('opac_'):
            opacity = cb.replace('opac_', '')
            data['opacity'] = float(opacity)  # Convert to float
            
            if data.get('type') == 'text':
                await query.edit_message_text(
                    f"✅ Opacity: {float(opacity)*100:.0f}%\n\n🔤 Choose font size:",
                    reply_markup=kb.get_fontsize_keyboard()
                )
            else:
                await query.edit_message_text(
                    f"✅ Opacity: {float(opacity)*100:.0f}%\n\n↩️ Choose rotation:",
                    reply_markup=kb.get_rotation_keyboard()
                )
        
        # ========== FONT SIZE ==========
        elif cb.startswith('fsize_'):
            fsize = cb.replace('fsize_', '')
            data['fontsize'] = int(fsize)  # Convert to int
            
            await query.edit_message_text(
                f"✅ Font: {fsize}pt\n\n↩️ Choose rotation:",
                reply_markup=kb.get_rotation_keyboard()
            )
        
        # ========== ROTATION ==========
        elif cb.startswith('rot_'):
            rot = cb.replace('rot_', '')
            
            if rot == 'custom':
                data['step'] = 'waiting_rotation'
                await query.edit_message_text(
                    "🔄 Enter custom angle (-180 to 180):\n_Example: 30 or -45_",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                data['rotation'] = int(rot)  # Convert to int
                await query.edit_message_text(
                    f"✅ Rotation: {rot}°\n\n🔗 Add clickable links?",
                    reply_markup=kb.get_link_add_skip_keyboard()
                )
        
        # ========== IMAGE SIZE ==========
        elif cb.startswith('isize_'):
            isize = cb.replace('isize_', '')
            data['imgsize'] = int(isize)  # Convert to int
            
            await query.edit_message_text(
                f"✅ Logo Size: {isize}px\n\n💡 Choose opacity:",
                reply_markup=kb.get_opacity_keyboard()
            )
        
        # ========== LINK: ADD ==========
        elif cb == 'link_add':
            data['step'] = 'waiting_link_url'
            await query.edit_message_text(
                "🔗 Enter link URL:\n_Example: https://yourwebsite.com_",
                parse_mode=ParseMode.MARKDOWN
            )
        
        # ========== LINK: SKIP ==========
        elif cb == 'link_skip':
            data['links'] = []
            await query.edit_message_text(
                "🕵️ Add hidden metadata to PDF?\n(Author name, location etc.)",
                reply_markup=kb.get_metadata_keyboard()
            )
        
        # ========== LINK: POSITION ==========
        elif cb.startswith('lpos_'):
            lpos = cb.replace('lpos_', '')
            data['temp_link_pos'] = lpos
            
            await query.edit_message_text(
                f"✅ Position: {lpos.upper()}\n\n📝 Choose link button text:",
                reply_markup=kb.get_link_text_keyboard()
            )
        
        # ========== LINK: TEXT ==========
        elif cb.startswith('ltext_'):
            ltext = cb.replace('ltext_', '')
            
            text_styles = {
                'click': '🔗 CLICK HERE',
                'visit': '📱 VISIT US',
                'open': '🌐 OPEN LINK',
                'learn': '✨ LEARN MORE',
                'url': None
            }
            
            if ltext == 'custom':
                data['step'] = 'waiting_link_text'
                await query.edit_message_text(
                    "📝 Enter custom link text (max 25 chars):",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                link_text = text_styles.get(ltext, '🔗 CLICK HERE')
                
                # Use URL as text if 'url' option
                if link_text is None:
                    link_text = data.get('temp_link_url', 'LINK')[:25]
                
                # Add link to list
                temp_url = data.get('temp_link_url', '')
                temp_pos = data.get('temp_link_pos', 'bottomcenter')
                
                if temp_url:
                    data['links'].append({
                        'url': temp_url,
                        'position': temp_pos,
                        'text': link_text
                    })
                    data['temp_link_url'] = ''
                    data['temp_link_pos'] = ''
                
                count = len(data['links'])
                await query.edit_message_text(
                    f"✅ Link added! ({count}/6)\n\nAdd more or continue?",
                    reply_markup=kb.get_add_more_link_keyboard(count)
                )
        
        # ========== LINK: DONE ==========
        elif cb == 'link_done':
            await query.edit_message_text(
                "🕵️ Add hidden metadata to PDF?\n(Author name, location etc.)",
                reply_markup=kb.get_metadata_keyboard()
            )
        
        # ========== LINK: VIEW ==========
        elif cb == 'link_view':
            links = data.get('links', [])
            if not links:
                text = "📋 No links added yet."
            else:
                lines = ["📋 *YOUR LINKS:*\n"]
                for i, link in enumerate(links, 1):
                    lines.append(f"{i}. `{link['text']}` ({link['position']})")
                text = '\n'.join(lines)
            
            await query.edit_message_text(
                text,
                reply_markup=kb.get_link_menu_keyboard(len(links)),
                parse_mode=ParseMode.MARKDOWN
            )
        
        # ========== LINK: CLEAR ==========
        elif cb == 'link_clear':
            data['links'] = []
            await query.edit_message_text(
                "🗑️ All links cleared!\n\nAdd links?",
                reply_markup=kb.get_link_add_skip_keyboard()
            )
        
        # ========== METADATA: YES ==========
        elif cb == 'meta_yes':
            data['step'] = 'waiting_metadata'
            await query.edit_message_text(
                "📝 Enter metadata:\n\n_Format: Author Name, Location_\n_Example: John, Mumbai_",
                parse_mode=ParseMode.MARKDOWN
            )
        
        # ========== METADATA: NO ==========
        elif cb == 'meta_no':
            data['add_metadata'] = False
            
            summary = get_summary_text(data)
            await query.edit_message_text(
                f"{summary}\n\n📂 *Send PDF or ZIP file now!*",
                parse_mode=ParseMode.MARKDOWN
            )
        
        # ========== MENU: TEXT ==========
        elif cb == 'menu_text':
            await query.edit_message_text("📝 Send your watermark text:")
        
        # ========== MENU: IMAGE ==========
        elif cb == 'menu_image':
            await query.edit_message_text("🖼️ Send your logo image:")
        
        # ========== MENU: HELP ==========
        elif cb == 'menu_help':
            await query.edit_message_text(
                "❓ HELP CENTER",
                reply_markup=kb.get_help_keyboard()
            )
        
        # ========== BACK TO MAIN ==========
        elif cb == 'back_main':
            await query.edit_message_text(
                "🏠 MAIN MENU",
                reply_markup=kb.get_main_menu_keyboard()
            )
        
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await query.edit_message_text("❌ Error. Send /start again.")

# ============================================
# HANDLE PDF/ZIP DOCUMENT
# ============================================
@app.on_message(filters.document)
async def handle_document(client: Client, message: Message):
    """Handle PDF or ZIP file"""
    user_id = message.from_user.id
    data = get_data(user_id)
    
    # Check if settings exist
    if not data.get('content'):
        await message.reply_text(
            "⚠️ Configure watermark first!\nSend /start to begin.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    filename = message.document.file_name or "document.pdf"
    mime = message.document.mime_type or ""
    
    # Check if ZIP
    if 'zip' in mime.lower() or filename.lower().endswith('.zip'):
        await process_zip(client, message, data, filename)
    else:
        await process_pdf(client, message, data, filename)

# ============================================
# PROCESS SINGLE PDF (WITH PYROGRAM STRICT RENAME)
# ============================================
async def process_pdf(client: Client, message: Message, data: dict, original_filename: str):
    """Process single PDF with strict Pyrogram force renaming"""
    status = await message.reply_text("⏳ Processing PDF...", parse_mode=ParseMode.MARKDOWN)
    
    user_id = message.from_user.id
    timestamp = int(time.time())
    
    # Task Directory Setup
    task_dir = os.path.join(DOWNLOAD_DIR, f"task_{user_id}_{timestamp}")
    os.makedirs(task_dir, exist_ok=True)
    
    input_path = os.path.join(task_dir, "input_temp.pdf")
    output_path = os.path.join(task_dir, f"output_{timestamp}.pdf")
    
    try:
        # Download file (Pyrogram native)
        await message.download(file_name=input_path)
        
        # Get page count
        pages = get_pdf_page_count(input_path)
        
        # Process
        await status.edit_text("🎨 Adding watermark...", parse_mode=ParseMode.MARKDOWN)
        
        # Engine output path par file banayega
        success = add_watermark_to_pdf(input_path, output_path, data, original_filename)
        
        if success:
            await status.edit_text("⬆️ Uploading...", parse_mode=ParseMode.MARKDOWN)
            
            caption = f"✅ <b>WATERMARK ADDED!</b>\n\n"
            caption += f"📄 <b>File:</b> <code>{html.escape(original_filename)}</code>\n"
            caption += f"📋 <b>Pages:</b> {pages}\n"
            
            if data.get('type') == 'text':
                txt = html.escape(data.get('content', '')[:40])
                caption += f"📝 <b>Text:</b> <code>{txt}</code>\n"
            else:
                caption += f"🖼️ <b>Logo:</b> Image Watermark\n"
            
            caption += f"🎨 <b>Style:</b> {data.get('style', 'diagonal').upper()}\n"
            
            if data.get('add_metadata'):
                caption += f"🕵️ <b>Metadata:</b> Added\n"
            
            # 🔴 PERMANENT FIX: Pyrogram me file_name argument se seedha exact original naam pass ho jayega
            await message.reply_document(
                document=output_path,
                file_name=original_filename,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
            
            await status.delete()
        else:
            await status.edit_text("❌ Failed to process PDF", parse_mode=ParseMode.MARKDOWN)
    
    except Exception as e:
        logger.error(f"PDF error: {e}")
        await status.edit_text(f"❌ Error processing PDF. Please try again.", parse_mode=ParseMode.MARKDOWN)
    
    finally:
        # COMPLETE CLEANUP
        try:
            if os.path.exists(task_dir):
                shutil.rmtree(task_dir)
        except Exception as cleanup_error:
            logger.error(f"Cleanup error: {cleanup_error}")
            
# ============================================
# PROCESS ZIP FILE (WITH PYROGRAM STRICT RENAME)
# ============================================
async def process_zip(client: Client, message: Message, data: dict, filename: str):
    """Process ZIP file with multiple PDFs"""
    status = await message.reply_text("⏳ Processing ZIP...", parse_mode=ParseMode.MARKDOWN)
    
    user_id = message.from_user.id
    timestamp = int(time.time())
    
    task_dir = os.path.join(DOWNLOAD_DIR, f"zip_task_{user_id}_{timestamp}")
    extract_dir = os.path.join(task_dir, "extracted")
    os.makedirs(task_dir, exist_ok=True)
    os.makedirs(extract_dir, exist_ok=True)
    
    zip_path = os.path.join(task_dir, "input.zip")
    
    try:
        # Download (Pyrogram Native)
        await message.download(file_name=zip_path)
        
        # Extract
        await status.edit_text("📂 Extracting...", parse_mode=ParseMode.MARKDOWN)
        
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(extract_dir)
        
        # Find PDFs
        pdfs = []
        for root, dirs, files in os.walk(extract_dir):
            for f in files:
                if f.lower().endswith('.pdf'):
                    pdfs.append(os.path.join(root, f))
        
        if not pdfs:
            await status.edit_text("❌ No PDF files in ZIP", parse_mode=ParseMode.MARKDOWN)
            return
        
        await status.edit_text(f"⚙️ Processing {len(pdfs)} PDFs...", parse_mode=ParseMode.MARKDOWN)
        
        success_count = 0
        
        for i, pdf_path in enumerate(pdfs, 1):
            orig_name = os.path.basename(pdf_path)
            output_path = os.path.join(task_dir, f"out_{i}_{timestamp}.pdf")
            
            pages = get_pdf_page_count(pdf_path)
            
            if add_watermark_to_pdf(pdf_path, output_path, data, orig_name):
                success_count += 1
                
                caption = f"✅ <b>Processed ({i}/{len(pdfs)})</b>\n"
                caption += f"📄 <code>{html.escape(orig_name)}</code>\n"
                caption += f"📋 Pages: {pages}"
                
                # 🔴 Pyrogram force exact file name for ZIP files
                await message.reply_document(
                    document=output_path,
                    file_name=orig_name,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
                
                os.remove(output_path)
        
        await status.delete()
        
        await message.reply_text(
            f"✅ <b>ZIP Complete!</b>\n\n"
            f"✅ Success: {success_count}\n"
            f"📁 Total: {len(pdfs)}",
            parse_mode=ParseMode.HTML
        )
    
    except Exception as e:
        logger.error(f"ZIP error: {e}")
        await status.edit_text(f"❌ Error: {str(e)[:100]}", parse_mode=ParseMode.MARKDOWN)
    
    finally:
        # Cleanup
        try:
            if os.path.exists(task_dir):
                shutil.rmtree(task_dir)
        except Exception as cleanup_error:
            logger.error(f"Cleanup error: {cleanup_error}")

# ============================================
# MAIN ENTRY POINT
# ============================================
if __name__ == '__main__':
    # Create directories
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    logger.info("🚀 Pyrogram Bot Starting...")
    
    # Keep alive
    try:
        from keep_alive import keep_alive
        keep_alive()
    except:
        pass
    
    # Run Pyrogram
    app.run()