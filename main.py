import os
import shutil # Folder delete karne ke liye
import zipfile # Zip handle karne ke liye
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN, DOWNLOAD_DIR, OUTPUT_DIR
import keyboards as kb
from watermark import add_watermark_to_pdf
from keep_alive import keep_alive
# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- 1. START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "👋 **Advanced Watermark Bot**\n\n"
        "Shuru karne ke liye:\n"
        "👉 Apna **Watermark TEXT** likhein,\n"
        "👉 YA apna **LOGO (Photo)** bhejein."
    )

# --- 2. INPUT HANDLERS (Text/Photo/URL) ---
async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    # CASE A: Metadata Wait
    if context.user_data.get('step') == 'waiting_for_metadata':
        if "," in text:
            parts = text.split(',')
            context.user_data['author'] = parts[0].strip()
            context.user_data['location'] = parts[1].strip()
        else:
            context.user_data['author'] = text
            context.user_data['location'] = "India"
        context.user_data['add_metadata'] = True
        context.user_data['step'] = 'done'
        await update.message.reply_text("✅ Metadata Saved!\n\n📂 **Ab PDF ya ZIP file bhejein.**")
        return

    # CASE B: URL Handling
    if text.startswith('http') or 'www.' in text:
        url = text
        if not url.startswith('http'): url = 'https://' + url
        context.user_data['url'] = url
        await update.message.reply_text(
            f"🔗 Link Set: {url}\n\nLink kahan lagana hai? **Upar (Top)** ya **Niche (Bottom)**?",
            reply_markup=kb.get_position_keyboard()
        )
        return

    # CASE C: Normal Watermark Text
    context.user_data['type'] = 'text'
    context.user_data['content'] = text
    await update.message.reply_text(f"📝 Text Saved: **{text}**\n\nAb **Style** choose karein:", reply_markup=kb.get_style_keyboard())

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    path = os.path.join(DOWNLOAD_DIR, f"logo_{update.effective_user.id}.jpg")
    await photo_file.download_to_drive(path)
    context.user_data['type'] = 'image'
    context.user_data['content'] = path
    await update.message.reply_text("🖼 Logo Saved. **Style** choose karein:", reply_markup=kb.get_style_keyboard())

# --- 3. BUTTON HANDLER ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith('style_'):
        context.user_data['style'] = data.split('_')[1]
        if context.user_data.get('type') == 'text':
            await query.edit_message_text("🎨 **Color** choose karein:", reply_markup=kb.get_color_keyboard())
        else:
            await query.edit_message_text("💡 **Opacity** choose karein:", reply_markup=kb.get_opacity_keyboard())

    elif data.startswith('color_'):
        context.user_data['color'] = data.split('_')[1]
        await query.edit_message_text("💡 **Opacity** choose karein:", reply_markup=kb.get_opacity_keyboard())

    elif data.startswith('opacity_'):
        context.user_data['opacity'] = data.split('_')[1]
        await query.edit_message_text("🔗 **Link Add karna hai?**\nURL likhein ya Skip karein.", reply_markup=kb.get_link_skip_keyboard())
    
    elif data == 'skip_link':
        context.user_data['url'] = None
        await query.edit_message_text("🕵️ **Hidden Metadata add karna hai?**", reply_markup=kb.get_metadata_ask_keyboard())

    elif data.startswith('pos_'):
        context.user_data['position'] = data.split('_')[1]
        await query.edit_message_text("🕵️ **Hidden Metadata add karna hai?**", reply_markup=kb.get_metadata_ask_keyboard())

    elif data == 'meta_yes':
        context.user_data['step'] = 'waiting_for_metadata'
        await query.edit_message_text("📝 **Author Name, Location** likh kar bhejein.")
    
    elif data == 'meta_no':
        context.user_data['add_metadata'] = False
        await query.edit_message_text("❌ Metadata Skipped.\n\n📂 **Ab PDF ya ZIP file bhejein.**")

# --- 4. ZIP FILE PROCESSING (NEW LOGIC) ---
async def handle_zip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'content' not in context.user_data:
        await update.message.reply_text("⚠️ Pehle settings set karein (/start).")
        return

    msg = await update.message.reply_text("⏳ **ZIP File Download ho rahi hai...**")
    user_id = update.effective_user.id
    
    # Paths Setup
    zip_filename = f"{user_id}_input.zip"
    zip_path = os.path.join(DOWNLOAD_DIR, zip_filename)
    extract_folder = os.path.join(DOWNLOAD_DIR, f"{user_id}_extracted")
    
    try:
        # 1. Download Zip
        file = await update.message.document.get_file()
        await file.download_to_drive(zip_path)
        
        # 2. Extract Zip
        await msg.edit_text("📂 **Unzipping & Processing files...**")
        if os.path.exists(extract_folder): shutil.rmtree(extract_folder) # Clean old junk
        os.makedirs(extract_folder, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_folder)

        # 3. Find and Process PDFs
        pdf_files = []
        # Walk through all folders inside zip
        for root, dirs, files in os.walk(extract_folder):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        
        if not pdf_files:
            await msg.edit_text("❌ ZIP mein koi PDF nahi mili.")
            return

        await msg.edit_text(f"⚙️ **Processing {len(pdf_files)} PDFs...**\nEk-ek karke bhej raha hoon.")

        # 4. Loop Logic
        count = 0
        for input_pdf_path in pdf_files:
            original_filename = os.path.basename(input_pdf_path)
            output_pdf_path = os.path.join(OUTPUT_DIR, f"WM_{original_filename}")
            
            # Watermark Function Call
            success = add_watermark_to_pdf(input_pdf_path, output_pdf_path, context.user_data, filename=original_filename)
            
            if success:
                count += 1
                with open(output_pdf_path, 'rb') as f:
                    # Caption sirf pehli file par ya simple rakh sakte hain
                    caption = f"✅ File {count}/{len(pdf_files)}: {original_filename}"
                    await update.message.reply_document(f, caption=caption)
                
                # Output delete karo space bachane ke liye
                os.remove(output_pdf_path)
        
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
        await update.message.reply_text("✅ **All Files Processed Successfully!**")

    except Exception as e:
        print(f"Zip Error: {e}")
        await msg.edit_text("❌ Error processing ZIP file.")
    
    finally:
        # Cleanup: Zip aur Extracted folder delete karo
        if os.path.exists(zip_path): os.remove(zip_path)
        if os.path.exists(extract_folder): shutil.rmtree(extract_folder)

# --- 5. SINGLE PDF PROCESSING ---
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if ZIP
    mime_type = update.message.document.mime_type
    file_name = update.message.document.file_name
    
    # Agar Zip hai to Zip Handler ko bhejo
    if 'zip' in mime_type or file_name.endswith('.zip'):
        await handle_zip(update, context)
        return

    # Baaki Normal PDF Logic
    if 'content' not in context.user_data:
        await update.message.reply_text("⚠️ Start se shuru karein (/start).")
        return

    msg = await update.message.reply_text("⏳ Processing...")
    user_id = update.effective_user.id
    input_path = os.path.join(DOWNLOAD_DIR, f"{user_id}_{file_name}")
    output_path = os.path.join(OUTPUT_DIR, f"{file_name}")

    try:
        file = await update.message.document.get_file()
        await file.download_to_drive(input_path)
        
        success = add_watermark_to_pdf(input_path, output_path, context.user_data, filename=file_name)

        if success:
            await msg.edit_text("⬆️ Uploading...")
            with open(output_path, 'rb') as f:
                caption = "✅ **Watermark Added!**"
                if context.user_data.get('add_metadata'): caption += "\n🕵️ Metadata Added."
                await update.message.reply_document(f, caption=caption)
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
        else:
            await msg.edit_text("❌ Error processing file.")
    except Exception as e:
        print(e)
        await msg.edit_text("❌ Failed.")
    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

if __name__ == '__main__':
    # Bot builder setup
    app = ApplicationBuilder().token(BOT_TOKEN).connect_timeout(30).read_timeout(30).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("Bot Running with ZIP Support...")
    
    # YAHAN KEEP ALIVE SERVER START KAREIN
    keep_alive()
    
    # Aur uske baad bot ki polling start karein
    app.run_polling()