# keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_style_keyboard():
    keyboard = [
        [InlineKeyboardButton("📍 Diagonal Center", callback_data='style_diagonal')],
        [InlineKeyboardButton("▦ Grid / Tiled", callback_data='style_grid')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_color_keyboard():
    keyboard = [
        [InlineKeyboardButton("⚫ Grey", callback_data='color_grey'), 
         InlineKeyboardButton("🔴 Red", callback_data='color_red')],
        [InlineKeyboardButton("🔵 Blue", callback_data='color_blue')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_opacity_keyboard():
    keyboard = [
        [InlineKeyboardButton("☁️ Light (10%)", callback_data='opacity_0.1')],
        [InlineKeyboardButton("⛅ Normal (30%)", callback_data='opacity_0.3')],
        [InlineKeyboardButton("🌩 Dark (60%)", callback_data='opacity_0.6')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_link_skip_keyboard():
    keyboard = [[InlineKeyboardButton("❌ No Link (Skip)", callback_data='skip_link')]]
    return InlineKeyboardMarkup(keyboard)

def get_position_keyboard():
    keyboard = [
        [InlineKeyboardButton("⬆️ Top", callback_data='pos_top'),
         InlineKeyboardButton("⬇️ Bottom", callback_data='pos_bottom')]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- NAYA KEYBOARD ---
def get_metadata_ask_keyboard():
    keyboard = [
        [InlineKeyboardButton("✅ Yes (Add Details)", callback_data='meta_yes')],
        [InlineKeyboardButton("❌ No (Skip)", callback_data='meta_no')]
    ]
    return InlineKeyboardMarkup(keyboard)