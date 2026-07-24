import asyncio
import logging
import json
import os
import random
import string
import aiohttp
import psutil
import platform
import time
import urllib.parse
from datetime import datetime, date, timedelta
from typing import Dict, Any, Tuple, Optional, List
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
)
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8630078554:AAHZdh21I3D__fObqDOvco5ge8zFkb6yg54"

BOT_NAME = "KING OSINT"
BOT_VERSION = "28.0.0"
BOT_START_TIME = time.time()

MAINTENANCE_MODE = False
MAINTENANCE_MESSAGE = "🔧 Bot is under maintenance. Please try again later!\n\n👑 Developer: @KINGGKAI"

MONGO_URI = "mongodb+srv://king:kai@cluster0.pv2q7id.mongodb.net/?appName=Cluster0"
MONGO_DB_NAME = "OSINT_DB"

OWNER_IDS = [1451422178]
ADMIN_USERNAMES = []

SUPPORT_USERNAME = "KINGGKAI"
DEVELOPER_USERNAME = "KINGGKAI"
DEVELOPER_LINK = "https://t.me/KINGGKAI"
SUPPORT_GROUP_LINK = "https://t.me/+zeKnIiKAGnk3ZGE1"
UPI_ID = "@kinggkai"

# Mandatory Channel Configuration
MANDATORY_CHANNEL_ENABLED = False
MANDATORY_CHANNEL_TYPE = "public"
MANDATORY_CHANNEL_ID = None
MANDATORY_CHANNEL_USERNAME = ""
MANDATORY_CHANNEL_LINK = ""
MANDATORY_CHANNEL_CHECK_INTERVAL = 30

# Group Approval Configuration
APPROVED_GROUPS = {}
PENDING_APPROVALS = {}

# Broadcast tracking
BROADCAST_ACTIVE = False
BROADCAST_STOP = False
BROADCAST_STATS = {"sent": 0, "failed": 0, "blocked": 0, "total": 0}
BROADCAST_MSG_ID = None
BROADCAST_CHAT_ID = None

# API Configuration
DEFAULT_APIS = {
    "num": "https://anon-num-info.vercel.app/num?key=numt0605&num=",
    "aadhar": "https://anon-num-info.vercel.app/aadhar?key=tempad705&id=",
    "pak_num": "https://anon-pak-info.vercel.app/num?key=temp1004&q=",
    "pak_cnic": "https://anon-pak-info.vercel.app/cnic?key=temp1004&q=",
    "pak_police": "https://anon-pak-info.vercel.app/police?key=temp1004&num=",
    "gst_billing": "https://anon-gst-info.vercel.app/advanced/gstin?key=temp25gst&gstin=",
    "pan_gst": "https://anon-gst-info.vercel.app/advanced/pan?key=temp25gst&pan=",
    "aadhar_family": "https://anon-family-info.vercel.app/aadhar?key=temp123&q=",
    "tg_info": "https://telegram-to-num-gray.vercel.app/sms?key=PRIME&term="
}

DAILY_FREE_LIMIT = 15
DEFAULT_REFERRAL_COINS = 10

# Conversation states
ASKING_NUMBER = 1
ASKING_AADHAR = 2
ASKING_PAK_NUM = 3
ASKING_PAK_CNIC = 4
ASKING_PAK_POLICE = 5
ASKING_GST_BILLING = 6
ASKING_PAN_GST = 7
ASKING_AADHAR_FAMILY = 8
ASKING_BROADCAST = 10
ASKING_BLOCK_NUMBER = 11
ASKING_UNBLOCK_NUMBER = 12
ASKING_REFERRAL_AMOUNT = 13
ASKING_ADD_ADMIN = 14
ASKING_REMOVE_ADMIN = 15
ASKING_ADD_COINS_USER = 16
ASKING_ADD_COINS_AMOUNT = 17
ASKING_API_UPDATE = 18
ASKING_API_SELECT = 19
ASKING_SET_DAILY_LIMIT = 20
ASKING_REDEEM_KEY = 21
ASKING_REVOKE_KEY = 25
ASKING_REVOKE_KEY_ID = 26
ASKING_BLOCK_USER = 27
ASKING_MAINTENANCE_MSG = 28
ASKING_SET_CHANNEL = 29
ASKING_RESET_CREDITS = 30
ASKING_DETECT_COINS_USER = 31
ASKING_TG_USERNAME = 33
ASKING_MAINTENANCE_CONFIRM = 34

API_SERVICES = {
    "num": {"name": "Indian Number", "emoji": "🔢"},
    "aadhar": {"name": "Indian Aadhar", "emoji": "🆔"},
    "pak_num": {"name": "Pakistan Number", "emoji": "🇵🇰"},
    "pak_cnic": {"name": "Pakistan CNIC", "emoji": "🪪"},
    "pak_police": {"name": "Pakistan Police", "emoji": "🚔"},
    "gst_billing": {"name": "GST Billing", "emoji": "💰"},
    "pan_gst": {"name": "PAN to GST", "emoji": "📇"},
    "aadhar_family": {"name": "Aadhar Family", "emoji": "👨‍👩‍👧"},
    "tg_info": {"name": "TG Info", "emoji": "📱"}
}

# ==================== SETUP ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

DATA_DIR = "bot_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def escape_text(text: str) -> str:
    if not text:
        return ""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


async def get_network_speed() -> Dict[str, Any]:
    try:
        start_time = time.time()
        async with aiohttp.ClientSession() as session:
            await session.get("https://www.google.com", timeout=aiohttp.ClientTimeout(total=5))
            ping_ms = round((time.time() - start_time) * 1000)

        if ping_ms < 100:
            speed_status = "🟢 EXCELLENT"
            speed_emoji = "🚀"
            speed_desc = "Very Fast"
        elif ping_ms < 200:
            speed_status = "🟡 GOOD"
            speed_emoji = "⚡"
            speed_desc = "Good"
        elif ping_ms < 500:
            speed_status = "🟠 SLOW"
            speed_emoji = "🐢"
            speed_desc = "Slow"
        else:
            speed_status = "🔴 POOR"
            speed_emoji = "⚠️"
            speed_desc = "Very Poor"

        return {"ping_ms": ping_ms, "status": speed_status, "emoji": speed_emoji, "description": speed_desc}
    except Exception:
        return {"ping_ms": 999, "status": "🔴 OFFLINE", "emoji": "❌", "description": "Connection Failed"}


# ==================== MAINTENANCE MODE ====================
def is_maintenance_mode() -> bool:
    global MAINTENANCE_MODE
    return MAINTENANCE_MODE


def set_maintenance_mode(enabled: bool, message: str = None):
    global MAINTENANCE_MODE, MAINTENANCE_MESSAGE
    MAINTENANCE_MODE = enabled
    if message is not None:
        MAINTENANCE_MESSAGE = message
    mongo.save_setting("maintenance_mode", enabled)
    mongo.save_setting("maintenance_message", MAINTENANCE_MESSAGE)
    logger.info(f"🔧 Maintenance Mode: {enabled}, Message: {MAINTENANCE_MESSAGE[:50]}...")


async def check_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if is_maintenance_mode():
        if update and update.effective_user:
            user_id = update.effective_user.id
            if is_admin(user_id):
                return False
        if update and update.effective_message:
            await update.effective_message.reply_text(
                MAINTENANCE_MESSAGE, 
                parse_mode=ParseMode.MARKDOWN
            )
        return True
    return False


async def set_maintenance_message_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start maintenance message set process"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admins can do this!")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "📝 *Set Maintenance Message*\n\n"
        "Send your new maintenance message below.\n\n"
        "After sending, you'll get options to Confirm, Edit, or Cancel.\n\n"
        f"📌 *Current Message:*\n{MAINTENANCE_MESSAGE}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_cancel_keyboard()
    )
    return ASKING_MAINTENANCE_MSG


async def handle_maintenance_message_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle maintenance message input"""
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    
    text = update.message.text.strip()
    if text == "❌ Cancel":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_admin_keyboard())
        return ConversationHandler.END
    
    # Store temporary message in context
    context.user_data["temp_maintenance_msg"] = text
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm", callback_data="maint_confirm")],
        [InlineKeyboardButton("✏️ Edit", callback_data="maint_edit")],
        [InlineKeyboardButton("❌ Cancel", callback_data="maint_cancel")]
    ])
    
    await update.message.reply_text(
        f"📝 *Preview Maintenance Message*\n\n"
        f"{text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Select an option:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )
    return ASKING_MAINTENANCE_CONFIRM


async def handle_maintenance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle maintenance message callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if not is_admin(user_id):
        await query.edit_message_text("❌ Only admins can do this!")
        return
    
    data = query.data
    temp_msg = context.user_data.get("temp_maintenance_msg", "")
    
    if data == "maint_confirm":
        set_maintenance_mode(MAINTENANCE_MODE, temp_msg)
        await query.edit_message_text(
            f"✅ *Maintenance message updated!*\n\n"
            f"📝 *New Message:*\n{temp_msg}\n\n"
            f"🔧 *Status:* {'🟢 ENABLED' if MAINTENANCE_MODE else '🔴 DISABLED'}\n\n"
            f"👑 *Developer:* @{DEVELOPER_USERNAME}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="close")]])
        )
        context.user_data.pop("temp_maintenance_msg", None)
        
    elif data == "maint_edit":
        await query.edit_message_text(
            "✏️ *Edit Message*\n\n"
            "Send your new maintenance message:",
            parse_mode=ParseMode.MARKDOWN
        )
        return ASKING_MAINTENANCE_MSG
        
    elif data == "maint_cancel":
        await query.edit_message_text(
            "❌ *Cancelled*\n\n"
            "Maintenance message unchanged.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="close")]])
        )
        context.user_data.pop("temp_maintenance_msg", None)


# ==================== GROUP APPROVAL ====================
def load_approvals():
    global APPROVED_GROUPS, PENDING_APPROVALS
    try:
        approved = mongo.get_setting("approved_groups", {})
        if approved:
            APPROVED_GROUPS = approved
        pending = mongo.get_setting("pending_approvals", {})
        if pending:
            PENDING_APPROVALS = pending
        logger.info(f"✅ Loaded {len(APPROVED_GROUPS)} approved groups, {len(PENDING_APPROVALS)} pending approvals")
    except Exception as e:
        logger.error(f"Error loading approvals: {e}")


def save_approvals():
    try:
        mongo.save_setting("approved_groups", APPROVED_GROUPS)
        mongo.save_setting("pending_approvals", PENDING_APPROVALS)
        logger.info(f"💾 Saved {len(APPROVED_GROUPS)} approved groups, {len(PENDING_APPROVALS)} pending approvals")
    except Exception as e:
        logger.error(f"Error saving approvals: {e}")


def is_group_approved(group_id: int) -> bool:
    return str(group_id) in APPROVED_GROUPS


def approve_group(group_id: int, approved_by: int, group_username: str = None) -> bool:
    if is_group_approved(group_id):
        return False
    
    APPROVED_GROUPS[str(group_id)] = {
        "approved_by": approved_by,
        "approved_at": datetime.now().isoformat(),
        "group_username": group_username
    }
    
    if str(group_id) in PENDING_APPROVALS:
        del PENDING_APPROVALS[str(group_id)]
    
    save_approvals()
    return True


def reject_group(group_id: int) -> bool:
    if str(group_id) in PENDING_APPROVALS:
        del PENDING_APPROVALS[str(group_id)]
        save_approvals()
        return True
    return False


def add_pending_approval(group_id: int, user_id: int, username: str = None, group_username: str = None) -> bool:
    if is_group_approved(group_id):
        return False
    
    PENDING_APPROVALS[str(group_id)] = {
        "user_id": user_id,
        "username": username,
        "group_username": group_username,
        "requested_at": datetime.now().isoformat()
    }
    
    save_approvals()
    return True


def is_group_approval_required(update: Update) -> bool:
    if not update.effective_chat or update.effective_chat.type not in ["group", "supergroup"]:
        return False
    
    chat_id = update.effective_chat.id
    
    if update.effective_user and is_admin(update.effective_user.id):
        return False
    
    if is_group_approved(chat_id):
        return False
    
    return True


async def check_group_approval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not is_group_approval_required(update):
        return True
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username or "None"
    group_username = update.effective_chat.username or None
    group_name = update.effective_chat.title or "Unknown Group"
    
    if str(chat_id) in PENDING_APPROVALS:
        pending = PENDING_APPROVALS[str(chat_id)]
        pending_time = datetime.fromisoformat(pending.get("requested_at", datetime.now().isoformat()))
        
        if (datetime.now() - pending_time).seconds < 300:
            await update.effective_message.reply_text(
                f"⏳ *APPROVAL REQUEST ALREADY PENDING!*\n\n"
                f"📌 Group: `{group_name}`\n"
                f"🆔 Group ID: `{chat_id}`\n\n"
                f"Please wait for @{SUPPORT_USERNAME} to approve your group.\n\n"
                f"👑 *Developer:* @{DEVELOPER_USERNAME}",
                parse_mode=ParseMode.MARKDOWN
            )
            return False
    
    add_pending_approval(chat_id, user_id, username, group_username)
    
    await update.effective_message.reply_text(
        f"⚠️ *UNAUTHORIZED ACCESS DETECTED!*\n\n"
        f"❌ You are trying to use this bot in `{group_name}` without approval.\n\n"
        f"📌 *Steps to get approval:*\n"
        f"1️⃣ Send your Chat ID using `/id` in this group\n"
        f"2️⃣ Contact @{SUPPORT_USERNAME} with your Chat ID\n"
        f"3️⃣ Wait for approval confirmation\n\n"
        f"🆔 *Group Chat ID:* `{chat_id}`\n"
        f"👤 *Your User ID:* `{user_id}`\n\n"
        f"_Once approved, you can use all bot features!_\n\n"
        f"👑 *Developer:* @{DEVELOPER_USERNAME}",
        parse_mode=ParseMode.MARKDOWN
    )
    
    notification_text = f"""🔔 *NEW GROUP APPROVAL REQUEST!*

📌 *Group:* {group_name}
🆔 *Group ID:* `{chat_id}`
👤 *Requested By:* @{username or 'None'} (`{user_id}`)
📅 *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

To approve: `/approve {chat_id}`
To reject: `/reject {chat_id}`

👑 *Developer:* @{DEVELOPER_USERNAME}"""
    
    for owner_id in OWNER_IDS:
        try:
            await context.bot.send_message(owner_id, notification_text, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Failed to send approval notification to {owner_id}: {e}")
    
    all_users = mongo.get_all_users()
    for user in all_users:
        if user.get("is_admin", False) and user["user_id"] not in OWNER_IDS:
            try:
                await context.bot.send_message(user["user_id"], notification_text, parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                logger.error(f"Failed to send approval notification to {user['user_id']}: {e}")
    
    return False


async def approve_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admins can approve groups!")
        return
    
    args = context.args
    if not args:
        await update.message.reply_text(
            "📝 *APPROVE GROUP*\n\n"
            "Usage: `/approve <group_id>`\n"
            "Example: `/approve -1001234567890`\n\n"
            "To get group ID, type `/id` in the group.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        group_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid Group ID! Must be a number.", parse_mode=ParseMode.MARKDOWN)
        return
    
    if is_group_approved(group_id):
        await update.message.reply_text(f"ℹ️ Group `{group_id}` is already approved.", parse_mode=ParseMode.MARKDOWN)
        return
    
    group_username = None
    try:
        chat = await context.bot.get_chat(group_id)
        group_username = chat.username
    except:
        pass
    
    approve_group(group_id, update.effective_user.id, group_username)
    
    await update.message.reply_text(
        f"✅ *GROUP APPROVED!*\n\n"
        f"🆔 Group ID: `{group_id}`\n"
        f"📌 Approved by: @{update.effective_user.username or 'Admin'}\n"
        f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"🎉 Group can now use the bot!",
        parse_mode=ParseMode.MARKDOWN
    )
    
    try:
        await context.bot.send_message(
            group_id,
            f"✅ *GROUP APPROVED!*\n\n"
            f"🎉 This group has been approved to use the bot.\n\n"
            f"Click /start to begin using all features!\n\n"
            f"👑 *Developer:* @{DEVELOPER_USERNAME}",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        pass


async def reject_group_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admins can reject groups!")
        return
    
    args = context.args
    if not args:
        await update.message.reply_text(
            "📝 *REJECT GROUP*\n\n"
            "Usage: `/reject <group_id>`\n"
            "Example: `/reject -1001234567890`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        group_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid Group ID! Must be a number.", parse_mode=ParseMode.MARKDOWN)
        return
    
    if reject_group(group_id):
        await update.message.reply_text(
            f"✅ *GROUP REJECTED!*\n\n"
            f"🆔 Group ID: `{group_id}`\n"
            f"📌 Rejected by: @{update.effective_user.username or 'Admin'}\n\n"
            f"🗑️ Approval request removed.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            await context.bot.send_message(
                group_id,
                f"❌ *GROUP APPROVAL REJECTED!*\n\n"
                f"Your group approval request has been rejected.\n\n"
                f"Contact @{SUPPORT_USERNAME} for more information.\n\n"
                f"👑 *Developer:* @{DEVELOPER_USERNAME}",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass
    else:
        await update.message.reply_text(f"❌ No pending approval found for `{group_id}`", parse_mode=ParseMode.MARKDOWN)


async def show_pending_approvals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admins can view pending approvals!")
        return
    
    if not PENDING_APPROVALS:
        await update.message.reply_text("📋 *No pending approvals*", parse_mode=ParseMode.MARKDOWN)
        return
    
    text = "📋 *PENDING GROUP APPROVALS*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for group_id, data in PENDING_APPROVALS.items():
        group_username = data.get("group_username", "Unknown")
        username = data.get("username", "Unknown")
        requested_at = data.get("requested_at", "Unknown")
        
        text += f"🆔 Group ID: `{group_id}`\n"
        text += f"📌 Group: @{group_username if group_username else 'Unknown'}\n"
        text += f"👤 Requested By: @{username}\n"
        text += f"📅 Requested: {requested_at[:16] if requested_at != 'Unknown' else 'Unknown'}\n"
        text += f"🔄 `/approve {group_id}` | `/reject {group_id}`\n"
        text += "─" * 35 + "\n\n"
    
    await send_long_message(update, text)
    await update.message.reply_text("✅ Done", reply_markup=get_admin_keyboard())


async def show_approved_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admins can view approved groups!")
        return
    
    if not APPROVED_GROUPS:
        await update.message.reply_text("📋 *No approved groups*", parse_mode=ParseMode.MARKDOWN)
        return
    
    text = "✅ *APPROVED GROUPS*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for group_id, data in APPROVED_GROUPS.items():
        group_username = data.get("group_username", "Unknown")
        approved_by = data.get("approved_by", "Unknown")
        approved_at = data.get("approved_at", "Unknown")
        
        text += f"🆔 Group ID: `{group_id}`\n"
        text += f"📌 Group: @{group_username if group_username else 'Unknown'}\n"
        text += f"👑 Approved By: `{approved_by}`\n"
        text += f"📅 Approved: {approved_at[:16] if approved_at != 'Unknown' else 'Unknown'}\n"
        text += f"🔄 `/revoke_approval {group_id}`\n"
        text += "─" * 35 + "\n\n"
    
    await send_long_message(update, text)
    await update.message.reply_text("✅ Done", reply_markup=get_admin_keyboard())


async def revoke_approval_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admins can revoke approvals!")
        return
    
    args = context.args
    if not args:
        await update.message.reply_text(
            "📝 *REVOKE APPROVAL*\n\n"
            "Usage: `/revoke_approval <group_id>`\n"
            "Example: `/revoke_approval -1001234567890`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    try:
        group_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid Group ID! Must be a number.", parse_mode=ParseMode.MARKDOWN)
        return
    
    if str(group_id) in APPROVED_GROUPS:
        del APPROVED_GROUPS[str(group_id)]
        save_approvals()
        
        await update.message.reply_text(
            f"✅ *APPROVAL REVOKED!*\n\n"
            f"🆔 Group ID: `{group_id}`\n"
            f"📌 Revoked by: @{update.effective_user.username or 'Admin'}\n\n"
            f"🗑️ Group approval removed.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            await context.bot.send_message(
                group_id,
                f"❌ *GROUP APPROVAL REVOKED!*\n\n"
                f"Your group approval has been revoked.\n\n"
                f"Contact @{SUPPORT_USERNAME} for more information.\n\n"
                f"👑 *Developer:* @{DEVELOPER_USERNAME}",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass
    else:
        await update.message.reply_text(f"❌ Group `{group_id}` is not approved.", parse_mode=ParseMode.MARKDOWN)


async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type
    
    text = f"📋 *YOUR ID INFO*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += f"👤 *Your User ID:* `{user_id}`\n"
    text += f"💬 *Chat ID:* `{chat_id}`\n"
    text += f"📌 *Chat Type:* `{chat_type}`\n"
    
    if chat_type in ["group", "supergroup"]:
        group_name = update.effective_chat.title or "Unknown"
        text += f"🏠 *Group Name:* {group_name}\n"
        is_approved = is_group_approved(chat_id)
        text += f"✅ *Group Approved:* {'🟢 YES' if is_approved else '🔴 NO'}\n"
        
        if not is_approved and str(chat_id) in PENDING_APPROVALS:
            text += f"⏳ *Approval Status:* PENDING\n"
    
    text += f"\n👑 *Developer:* @{DEVELOPER_USERNAME}"
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ==================== MANDATORY CHANNEL ====================
def is_mandatory_channel_enabled() -> bool:
    global MANDATORY_CHANNEL_ENABLED
    return MANDATORY_CHANNEL_ENABLED


def set_mandatory_channel_enabled(enabled: bool):
    global MANDATORY_CHANNEL_ENABLED
    MANDATORY_CHANNEL_ENABLED = enabled
    mongo.save_setting("mandatory_channel_enabled", enabled)


def get_mandatory_channel_type() -> str:
    global MANDATORY_CHANNEL_TYPE
    return MANDATORY_CHANNEL_TYPE


def set_mandatory_channel_type(channel_type: str):
    global MANDATORY_CHANNEL_TYPE
    MANDATORY_CHANNEL_TYPE = channel_type
    mongo.save_setting("mandatory_channel_type", channel_type)


def get_mandatory_channel_config() -> dict:
    global MANDATORY_CHANNEL_ID, MANDATORY_CHANNEL_USERNAME, MANDATORY_CHANNEL_LINK, MANDATORY_CHANNEL_TYPE
    return {
        "channel_id": MANDATORY_CHANNEL_ID,
        "username": MANDATORY_CHANNEL_USERNAME,
        "link": MANDATORY_CHANNEL_LINK,
        "enabled": MANDATORY_CHANNEL_ENABLED,
        "channel_type": MANDATORY_CHANNEL_TYPE
    }


def set_mandatory_channel(channel_id: int = None, username: str = None, link: str = None):
    global MANDATORY_CHANNEL_ID, MANDATORY_CHANNEL_USERNAME, MANDATORY_CHANNEL_LINK
    if channel_id is not None:
        MANDATORY_CHANNEL_ID = channel_id
        mongo.save_setting("mandatory_channel_id", channel_id)
    if username is not None:
        MANDATORY_CHANNEL_USERNAME = username
        mongo.save_setting("mandatory_channel_username", username)
    if link is not None:
        MANDATORY_CHANNEL_LINK = link
        mongo.save_setting("mandatory_channel_link", link)


async def generate_channel_invite_link(context: ContextTypes.DEFAULT_TYPE, channel_id: int) -> str:
    try:
        invite_link = await context.bot.create_chat_invite_link(
            chat_id=channel_id,
            member_limit=1,
            expire_date=datetime.now() + timedelta(hours=1)
        )
        return invite_link.invite_link
    except Exception as e:
        logger.error(f"Error creating invite link: {e}")
        return None


async def get_channel_id_from_username(context: ContextTypes.DEFAULT_TYPE, username: str) -> Optional[int]:
    try:
        chat = await context.bot.get_chat(f"@{username.lstrip('@')}")
        return chat.id
    except Exception as e:
        logger.error(f"Error getting channel ID: {e}")
        return None


async def check_mandatory_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not is_mandatory_channel_enabled():
        return True

    user_id = update.effective_user.id
    if is_admin(user_id):
        return True

    config = get_mandatory_channel_config()
    if not config["channel_id"] and not config["username"]:
        return True

    user = get_user(user_id)
    if user.get("channel_verified", False):
        last_verified = user.get("channel_verified_at")
        if last_verified:
            verified_date = datetime.fromisoformat(last_verified)
            if (datetime.now() - verified_date).days < MANDATORY_CHANNEL_CHECK_INTERVAL:
                return True

    channel_id = config["channel_id"]
    channel_username = config["username"].lstrip('@') if config["username"] else None

    if not channel_id and channel_username:
        channel_id = await get_channel_id_from_username(context, channel_username)
        if channel_id:
            set_mandatory_channel(channel_id=channel_id)

    if not channel_id and not channel_username:
        return True

    if channel_id:
        try:
            chat_member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if chat_member.status in ["member", "administrator", "creator"]:
                user["channel_verified"] = True
                user["channel_verified_at"] = datetime.now().isoformat()
                mongo.save_user(user)
                return True
        except Exception as e:
            logger.error(f"Error checking membership: {e}")

    invite_link = config["link"]
    if not invite_link and channel_id:
        invite_link = await generate_channel_invite_link(context, channel_id)
        if invite_link:
            set_mandatory_channel(link=invite_link)

    if not invite_link and channel_username:
        invite_link = f"https://t.me/{channel_username}"
    elif not invite_link:
        invite_link = "#"

    channel_type = config.get("channel_type", "public")
    channel_display = "Private Channel" if channel_type == "private" else f"@{channel_username}" if channel_username else "Channel"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 JOIN CHANNEL", url=invite_link)],
        [InlineKeyboardButton("✅ I HAVE JOINED", callback_data="check_join")]
    ])

    await update.effective_message.reply_text(
        f"⚠️ *MANDATORY TO JOIN CHANNEL!*\n\n"
        f"❌ You cannot use this bot until you join our channel.\n\n"
        f"🔗 *Channel:* {channel_display}\n\n"
        f"📌 *Steps to Verify:*\n"
        f"1️⃣ Click the 'JOIN CHANNEL' button below\n"
        f"2️⃣ Join the channel\n"
        f"3️⃣ Come back and click 'I HAVE JOINED'\n\n"
        f"✅ *After verification, you can use all bot features!*\n\n"
        f"👑 *Developer:* @{DEVELOPER_USERNAME}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )
    return False


async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    config = get_mandatory_channel_config()

    channel_username = config["username"].lstrip('@') if config["username"] else None
    channel_id = config["channel_id"]

    if not channel_id and not channel_username:
        await query.edit_message_text("❌ Channel not configured! Please contact admin.")
        return

    await query.edit_message_text(
        "🔄 *Verifying your membership...*\n\nPlease wait...",
        parse_mode=ParseMode.MARKDOWN
    )

    if not channel_id and channel_username:
        channel_id = await get_channel_id_from_username(context, channel_username)
        if channel_id:
            set_mandatory_channel(channel_id=channel_id)

    try:
        if channel_id:
            chat_member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if chat_member.status in ["member", "administrator", "creator"]:
                user = get_user(user_id)
                user["channel_verified"] = True
                user["channel_verified_at"] = datetime.now().isoformat()
                mongo.save_user(user)

                await query.edit_message_text(
                    "✅ *VERIFICATION SUCCESSFUL!*\n\n"
                    "You have been verified. You can now use the bot.\n\n"
                    "Click /start to begin using the bot!",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
    except Exception as e:
        logger.error(f"Check join error: {e}")

    invite_link = config["link"]
    if not invite_link and channel_id:
        invite_link = await generate_channel_invite_link(context, channel_id)
        if invite_link:
            set_mandatory_channel(link=invite_link)

    if not invite_link and channel_username:
        invite_link = f"https://t.me/{channel_username}"
    elif not invite_link:
        invite_link = "#"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 JOIN CHANNEL", url=invite_link)],
        [InlineKeyboardButton("✅ I HAVE JOINED", callback_data="check_join")]
    ])

    await query.edit_message_text(
        f"❌ *NOT VERIFIED!*\n\n"
        f"You have not joined {channel_username or 'the channel'} yet!\n\n"
        f"📌 *Please follow these steps:*\n"
        f"1️⃣ Click 'JOIN CHANNEL' below\n"
        f"2️⃣ Join the channel\n"
        f"3️⃣ Click 'I HAVE JOINED' again\n\n"
        f"👑 *Developer:* @{DEVELOPER_USERNAME}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )


# ==================== MONGODB MANAGER ====================
class MongoDBManager:
    def __init__(self, uri: str, db_name: str):
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None
        self.is_connected = False
        self._retry_count = 3
        if uri:
            self.connect()

    def connect(self):
        try:
            self.client = MongoClient(
                self.uri, 
                serverSelectionTimeoutMS=10000, 
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
                tlsAllowInvalidCertificates=True, 
                tlsAllowInvalidHostnames=True
            )
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.is_connected = True
            logger.info("✅ MongoDB connected!")
            self._create_indexes()
            return True
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            self.client = None
            self.db = None
            self.is_connected = False
            return False

    def _create_indexes(self):
        try:
            if self.db is not None:
                users_col = self.db["users"]
                users_col.create_index("user_id", unique=True)
                users_col.create_index("last_active")

                keys_col = self.db["generated_keys"]
                keys_col.create_index("key", unique=True)
                keys_col.create_index("is_used")

                history_col = self.db["search_history"]
                history_col.create_index("user_id")
                history_col.create_index("timestamp")

                settings_col = self.db["settings"]
                settings_col.create_index("key", unique=True)

                logger.info("✅ MongoDB indexes created")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")

    def is_available(self) -> bool:
        if not self.is_connected:
            return False
        try:
            self.client.admin.command('ping')
            return True
        except:
            self.is_connected = False
            return False

    def get_collection(self, name: str):
        if self.is_available() and self.db is not None:
            return self.db[name]
        return None

    def save_user(self, user_data: dict):
        collection = self.get_collection("users")
        if collection is not None:
            try:
                user_data.pop("_id", None)
                collection.update_one({"user_id": user_data["user_id"]}, {"$set": user_data}, upsert=True)
                return True
            except Exception as e:
                logger.error(f"Error saving user to MongoDB: {e}")
        return self._save_user_file(user_data)

    def _save_user_file(self, user_data: dict):
        users_file = f"{DATA_DIR}/users.json"
        try:
            users = {}
            if os.path.exists(users_file):
                with open(users_file, 'r', encoding='utf-8') as f:
                    users = json.load(f)
            users[str(user_data["user_id"])] = user_data
            with open(users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving user to file: {e}")
            return False

    def get_user(self, user_id: int) -> Optional[dict]:
        collection = self.get_collection("users")
        if collection is not None:
            try:
                user = collection.find_one({"user_id": user_id})
                if user:
                    user.pop("_id", None)
                    return user
            except Exception as e:
                logger.error(f"Error getting user from MongoDB: {e}")
        return self._get_user_file(user_id)

    def _get_user_file(self, user_id: int) -> Optional[dict]:
        users_file = f"{DATA_DIR}/users.json"
        try:
            if os.path.exists(users_file):
                with open(users_file, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                return users.get(str(user_id))
        except Exception as e:
            logger.error(f"Error getting user from file: {e}")
        return None

    def get_all_users(self) -> List[dict]:
        collection = self.get_collection("users")
        if collection is not None:
            try:
                users = list(collection.find({}))
                for user in users:
                    user.pop("_id", None)
                return users
            except Exception as e:
                logger.error(f"Error getting users from MongoDB: {e}")
        return self._get_all_users_file()

    def _get_all_users_file(self) -> List[dict]:
        users_file = f"{DATA_DIR}/users.json"
        try:
            if os.path.exists(users_file):
                with open(users_file, 'r', encoding='utf-8') as f:
                    users_dict = json.load(f)
                return list(users_dict.values())
        except Exception as e:
            logger.error(f"Error getting users from file: {e}")
        return []

    def save_setting(self, key: str, value: any):
        collection = self.get_collection("settings")
        if collection is not None:
            try:
                collection.update_one({"key": key}, {"$set": {"value": value, "updated_at": datetime.now()}}, upsert=True)
                return True
            except Exception as e:
                logger.error(f"Error saving setting to MongoDB: {e}")
        return self._save_setting_file(key, value)

    def _save_setting_file(self, key: str, value: any):
        settings_file = f"{DATA_DIR}/settings.json"
        try:
            settings = {}
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            settings[key] = value
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving setting to file: {e}")
            return False

    def get_setting(self, key: str, default: any = None) -> any:
        collection = self.get_collection("settings")
        if collection is not None:
            try:
                setting = collection.find_one({"key": key})
                if setting:
                    return setting.get("value", default)
            except Exception as e:
                logger.error(f"Error getting setting from MongoDB: {e}")
        return self._get_setting_file(key, default)

    def _get_setting_file(self, key: str, default: any = None) -> any:
        settings_file = f"{DATA_DIR}/settings.json"
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                return settings.get(key, default)
        except Exception as e:
            logger.error(f"Error getting setting from file: {e}")
        return default

    def save_api_setting(self, service: str, data: dict):
        collection = self.get_collection("api_settings")
        if collection is not None:
            try:
                collection.update_one({"service": service}, {"$set": data}, upsert=True)
                return True
            except Exception as e:
                logger.error(f"Error saving API setting: {e}")
        return self._save_api_setting_file(service, data)

    def _save_api_setting_file(self, service: str, data: dict):
        api_file = f"{DATA_DIR}/api_settings.json"
        try:
            api_settings = {}
            if os.path.exists(api_file):
                with open(api_file, 'r', encoding='utf-8') as f:
                    api_settings = json.load(f)
            api_settings[service] = data
            with open(api_file, 'w', encoding='utf-8') as f:
                json.dump(api_settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving API setting to file: {e}")
            return False

    def get_api_setting(self, service: str) -> Optional[dict]:
        collection = self.get_collection("api_settings")
        if collection is not None:
            try:
                setting = collection.find_one({"service": service})
                if setting:
                    setting.pop("_id", None)
                    return setting
            except Exception as e:
                logger.error(f"Error getting API setting from MongoDB: {e}")
        return self._get_api_setting_file(service)

    def _get_api_setting_file(self, service: str) -> Optional[dict]:
        api_file = f"{DATA_DIR}/api_settings.json"
        try:
            if os.path.exists(api_file):
                with open(api_file, 'r', encoding='utf-8') as f:
                    api_settings = json.load(f)
                return api_settings.get(service)
        except Exception as e:
            logger.error(f"Error getting API setting from file: {e}")
        return None

    def save_key(self, key: str, data: dict):
        collection = self.get_collection("generated_keys")
        if collection is not None:
            try:
                data.pop("_id", None)
                collection.update_one({"key": key}, {"$set": data}, upsert=True)
                logger.info(f"✅ Key saved to MongoDB: {key}")
                return True
            except Exception as e:
                logger.error(f"Error saving key to MongoDB: {e}")
        return self._save_key_file(key, data)

    def _save_key_file(self, key: str, data: dict):
        keys_file = f"{DATA_DIR}/generated_keys.json"
        try:
            keys = {}
            if os.path.exists(keys_file):
                with open(keys_file, 'r', encoding='utf-8') as f:
                    keys = json.load(f)
            keys[key] = data
            with open(keys_file, 'w', encoding='utf-8') as f:
                json.dump(keys, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Key saved to file: {key}")
            return True
        except Exception as e:
            logger.error(f"Error saving key to file: {e}")
            return False

    def get_key(self, key: str) -> Optional[dict]:
        collection = self.get_collection("generated_keys")
        if collection is not None:
            try:
                key_data = collection.find_one({"key": key})
                if key_data:
                    key_data.pop("_id", None)
                    return key_data
            except Exception as e:
                logger.error(f"Error getting key from MongoDB: {e}")
        return self._get_key_file(key)

    def _get_key_file(self, key: str) -> Optional[dict]:
        keys_file = f"{DATA_DIR}/generated_keys.json"
        try:
            if os.path.exists(keys_file):
                with open(keys_file, 'r', encoding='utf-8') as f:
                    keys = json.load(f)
                return keys.get(key)
        except Exception as e:
            logger.error(f"Error getting key from file: {e}")
        return None

    def get_all_keys(self) -> List[dict]:
        collection = self.get_collection("generated_keys")
        if collection is not None:
            try:
                keys = list(collection.find({}))
                for key in keys:
                    key.pop("_id", None)
                return keys
            except Exception as e:
                logger.error(f"Error getting keys from MongoDB: {e}")
        return self._get_all_keys_file()

    def _get_all_keys_file(self) -> List[dict]:
        keys_file = f"{DATA_DIR}/generated_keys.json"
        try:
            if os.path.exists(keys_file):
                with open(keys_file, 'r', encoding='utf-8') as f:
                    keys_dict = json.load(f)
                return list(keys_dict.values())
        except Exception as e:
            logger.error(f"Error getting keys from file: {e}")
        return []

    def delete_key(self, key: str) -> bool:
        collection = self.get_collection("generated_keys")
        if collection is not None:
            try:
                result = collection.delete_one({"key": key})
                return result.deleted_count > 0
            except Exception as e:
                logger.error(f"Error deleting key from MongoDB: {e}")
        return self._delete_key_file(key)

    def _delete_key_file(self, key: str) -> bool:
        keys_file = f"{DATA_DIR}/generated_keys.json"
        try:
            if os.path.exists(keys_file):
                with open(keys_file, 'r', encoding='utf-8') as f:
                    keys = json.load(f)
                if key in keys:
                    del keys[key]
                    with open(keys_file, 'w', encoding='utf-8') as f:
                        json.dump(keys, f, indent=2, ensure_ascii=False)
                    return True
        except Exception as e:
            logger.error(f"Error deleting key from file: {e}")
        return False

    def delete_unused_keys(self, key_type: str = None) -> int:
        collection = self.get_collection("generated_keys")
        if collection is not None:
            try:
                query = {"is_used": False}
                if key_type and key_type != "all":
                    query["key_type"] = key_type
                result = collection.delete_many(query)
                return result.deleted_count
            except Exception as e:
                logger.error(f"Error deleting unused keys from MongoDB: {e}")
        return self._delete_unused_keys_file(key_type)

    def _delete_unused_keys_file(self, key_type: str = None) -> int:
        keys_file = f"{DATA_DIR}/generated_keys.json"
        try:
            if os.path.exists(keys_file):
                with open(keys_file, 'r', encoding='utf-8') as f:
                    keys = json.load(f)
                to_delete = []
                for k, data in keys.items():
                    if not data.get("is_used", False):
                        if not key_type or key_type == "all" or data.get("key_type") == key_type:
                            to_delete.append(k)
                for k in to_delete:
                    del keys[k]
                with open(keys_file, 'w', encoding='utf-8') as f:
                    json.dump(keys, f, indent=2, ensure_ascii=False)
                return len(to_delete)
        except Exception as e:
            logger.error(f"Error deleting unused keys from file: {e}")
        return 0

    def save_search_result(self, user_id: int, search_type: str, query: str, result: dict):
        collection = self.get_collection("search_history")
        if collection is not None:
            try:
                collection.insert_one({
                    "user_id": user_id, 
                    "search_type": search_type, 
                    "query": query, 
                    "result": result, 
                    "timestamp": datetime.now()
                })
                return True
            except Exception as e:
                logger.error(f"Error saving search result: {e}")
        return False

    def get_search_history(self, user_id: int, limit: int = 50) -> List[dict]:
        collection = self.get_collection("search_history")
        if collection is not None:
            try:
                history = list(collection.find({"user_id": user_id}).sort("timestamp", -1).limit(limit))
                for h in history:
                    h.pop("_id", None)
                return history
            except Exception as e:
                logger.error(f"Error getting search history: {e}")
        return []

    def get_global_search_stats(self) -> dict:
        collection = self.get_collection("search_history")
        if collection is not None:
            try:
                total_searches = collection.count_documents({})

                pipeline_type = [
                    {"$group": {"_id": "$search_type", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}
                ]
                type_stats = list(collection.aggregate(pipeline_type))

                pipeline_users = [
                    {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 10}
                ]
                top_users = list(collection.aggregate(pipeline_users))

                yesterday = datetime.now() - timedelta(days=1)
                daily_searches = collection.count_documents({"timestamp": {"$gte": yesterday}})

                week_ago = datetime.now() - timedelta(days=7)
                weekly_searches = collection.count_documents({"timestamp": {"$gte": week_ago}})

                month_ago = datetime.now() - timedelta(days=30)
                monthly_searches = collection.count_documents({"timestamp": {"$gte": month_ago}})

                return {
                    "total": total_searches,
                    "daily": daily_searches,
                    "weekly": weekly_searches,
                    "monthly": monthly_searches,
                    "by_type": type_stats,
                    "top_users": top_users
                }
            except Exception as e:
                logger.error(f"Error getting global stats: {e}")
        return {"total": 0, "daily": 0, "weekly": 0, "monthly": 0, "by_type": [], "top_users": []}

    def get_daily_weekly_monthly_users(self) -> dict:
        collection = self.get_collection("users")
        if collection is not None:
            try:
                today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                week_start = datetime.now() - timedelta(days=7)
                month_start = datetime.now() - timedelta(days=30)

                daily_active = collection.count_documents({"last_active": {"$gte": today_start.isoformat()}})
                weekly_active = collection.count_documents({"last_active": {"$gte": week_start.isoformat()}})
                monthly_active = collection.count_documents({"last_active": {"$gte": month_start.isoformat()}})
                total_users = collection.count_documents({})

                return {
                    "daily": daily_active,
                    "weekly": weekly_active,
                    "monthly": monthly_active,
                    "total": total_users
                }
            except Exception as e:
                logger.error(f"Error getting user stats: {e}")
        return {"daily": 0, "weekly": 0, "monthly": 0, "total": 0}

    def save_blocked_number(self, number: str, data: dict):
        collection = self.get_collection("blocked_numbers")
        if collection is not None:
            try:
                collection.update_one({"number": number}, {"$set": data}, upsert=True)
                return True
            except Exception as e:
                logger.error(f"Error saving blocked number: {e}")
        return self._save_blocked_number_file(number, data)

    def _save_blocked_number_file(self, number: str, data: dict):
        blocked_file = f"{DATA_DIR}/blocked.json"
        try:
            blocked = {}
            if os.path.exists(blocked_file):
                with open(blocked_file, 'r', encoding='utf-8') as f:
                    blocked = json.load(f)
            blocked[number] = data
            with open(blocked_file, 'w', encoding='utf-8') as f:
                json.dump(blocked, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving blocked number to file: {e}")
            return False

    def get_blocked_number(self, number: str) -> Optional[dict]:
        collection = self.get_collection("blocked_numbers")
        if collection is not None:
            try:
                return collection.find_one({"number": number})
            except Exception as e:
                logger.error(f"Error getting blocked number: {e}")
        return self._get_blocked_number_file(number)

    def _get_blocked_number_file(self, number: str) -> Optional[dict]:
        blocked_file = f"{DATA_DIR}/blocked.json"
        try:
            if os.path.exists(blocked_file):
                with open(blocked_file, 'r', encoding='utf-8') as f:
                    blocked = json.load(f)
                return blocked.get(number)
        except Exception as e:
            logger.error(f"Error getting blocked number from file: {e}")
        return None

    def get_all_blocked_numbers(self) -> List[dict]:
        collection = self.get_collection("blocked_numbers")
        if collection is not None:
            try:
                return list(collection.find({}))
            except Exception as e:
                logger.error(f"Error getting blocked numbers: {e}")
        return self._get_all_blocked_numbers_file()

    def _get_all_blocked_numbers_file(self) -> List[dict]:
        blocked_file = f"{DATA_DIR}/blocked.json"
        try:
            if os.path.exists(blocked_file):
                with open(blocked_file, 'r', encoding='utf-8') as f:
                    blocked_dict = json.load(f)
                return [{"number": k, **v} for k, v in blocked_dict.items()]
        except Exception as e:
            logger.error(f"Error getting blocked numbers from file: {e}")
        return []

    def remove_blocked_number(self, number: str) -> bool:
        collection = self.get_collection("blocked_numbers")
        if collection is not None:
            try:
                result = collection.delete_one({"number": number})
                return result.deleted_count > 0
            except Exception as e:
                logger.error(f"Error removing blocked number: {e}")
        return self._remove_blocked_number_file(number)

    def _remove_blocked_number_file(self, number: str) -> bool:
        blocked_file = f"{DATA_DIR}/blocked.json"
        try:
            if os.path.exists(blocked_file):
                with open(blocked_file, 'r', encoding='utf-8') as f:
                    blocked = json.load(f)
                if number in blocked:
                    del blocked[number]
                    with open(blocked_file, 'w', encoding='utf-8') as f:
                        json.dump(blocked, f, indent=2, ensure_ascii=False)
                    return True
        except Exception as e:
            logger.error(f"Error removing blocked number from file: {e}")
        return False

    def save_log(self, log_type: str, data: dict):
        collection = self.get_collection("logs")
        if collection is not None:
            try:
                collection.insert_one({"type": log_type, "data": data, "timestamp": datetime.now()})
                return True
            except Exception as e:
                logger.error(f"Error saving log: {e}")
        return False

    def get_stats(self) -> dict:
        stats = {"total_users": 0, "total_keys": 0, "used_keys": 0, "total_searches": 0}
        users = self.get_all_users()
        stats["total_users"] = len(users)
        keys = self.get_all_keys()
        stats["total_keys"] = len(keys)
        stats["used_keys"] = sum(1 for k in keys if k.get("is_used", False))
        collection = self.get_collection("search_history")
        if collection is not None:
            try:
                stats["total_searches"] = collection.count_documents({})
            except:
                pass
        return stats


# ==================== INITIALIZE MONGODB ====================
mongo = MongoDBManager(MONGO_URI, MONGO_DB_NAME)

# ==================== DATA MANAGEMENT ====================
def load_settings():
    global settings, api_settings, MAINTENANCE_MODE, MAINTENANCE_MESSAGE
    global MANDATORY_CHANNEL_ENABLED, MANDATORY_CHANNEL_ID, MANDATORY_CHANNEL_USERNAME, MANDATORY_CHANNEL_LINK, MANDATORY_CHANNEL_TYPE

    settings = {
        "bot_active": mongo.get_setting("bot_active", True),
        "referral_coins": mongo.get_setting("referral_coins", DEFAULT_REFERRAL_COINS),
        "daily_limit": mongo.get_setting("daily_limit", DAILY_FREE_LIMIT),
        "daily_free_enabled": mongo.get_setting("daily_free_enabled", True)
    }

    MAINTENANCE_MODE = mongo.get_setting("maintenance_mode", False)
    MAINTENANCE_MESSAGE = mongo.get_setting("maintenance_message", "🔧 Bot is under maintenance. Please try again later!\n\n👑 Developer: @KINGGKAI")

    MANDATORY_CHANNEL_ENABLED = mongo.get_setting("mandatory_channel_enabled", False)
    MANDATORY_CHANNEL_ID = mongo.get_setting("mandatory_channel_id", None)
    MANDATORY_CHANNEL_USERNAME = mongo.get_setting("mandatory_channel_username", "")
    MANDATORY_CHANNEL_LINK = mongo.get_setting("mandatory_channel_link", "")
    MANDATORY_CHANNEL_TYPE = mongo.get_setting("mandatory_channel_type", "public")

    api_settings = {"apis": {}}
    for key in DEFAULT_APIS.keys():
        api_data = mongo.get_api_setting(key)
        if api_data:
            api_settings["apis"][key] = api_data
        else:
            api_settings["apis"][key] = {"enabled": True, "url": DEFAULT_APIS[key]}
            mongo.save_api_setting(key, api_settings["apis"][key])
    
    load_approvals()
    logger.info(f"📝 Maintenance Message loaded: {MAINTENANCE_MESSAGE[:50]}...")


def get_user(user_id: int) -> dict:
    user = mongo.get_user(user_id)
    if not user:
        user = {
            "user_id": user_id,
            "joined_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "username": None,
            "coins": 0,
            "total_searches": 0,
            "daily_searches": 0,
            "last_search_date": date.today().isoformat(),
            "referral_code": f"{user_id}_{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}",
            "referred_by": None,
            "referrals": [],
            "is_admin": False,
            "redeemed_keys": [],
            "is_blocked": False,
            "blocked_reason": None,
            "blocked_at": None,
            "channel_verified": False,
            "channel_verified_at": None,
            "alert_sent": False
        }
        mongo.save_user(user)
    return user


def reset_all_credits():
    all_users = mongo.get_all_users()
    count = 0
    for user in all_users:
        if not is_admin(user["user_id"]):
            user["coins"] = 0
            mongo.save_user(user)
            count += 1
    mongo.save_log("credits_reset", {"count": count, "timestamp": datetime.now().isoformat()})
    return count


async def send_new_user_alert_async(bot, user_id: int, username: str = None):
    user = get_user(user_id)
    if user.get("alert_sent", False):
        return
    user["alert_sent"] = True
    mongo.save_user(user)

    alert_text = f"""\n🆕 *NEW USER JOINED!*\n\n👤 *User ID:* `{user_id}`\n👤 *Username:* @{username or 'None'}\n📅 *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n👑 *Developer:* @{DEVELOPER_USERNAME}\n"""
    all_users = mongo.get_all_users()
    for user_data in all_users:
        if user_data.get("is_admin", False) or user_data["user_id"] in OWNER_IDS:
            try:
                await bot.send_message(user_data["user_id"], alert_text, parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                logger.error(f"Failed to send new user alert: {e}")


def update_user_stats(user_id: int):
    user = get_user(user_id)
    today = date.today().isoformat()
    if user["last_search_date"] != today:
        user["daily_searches"] = 0
        user["last_search_date"] = today
    user["daily_searches"] += 1
    user["total_searches"] += 1
    user["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mongo.save_user(user)


def add_coins(user_id: int, amount: int):
    user = get_user(user_id)
    user["coins"] += amount
    mongo.save_user(user)


def deduct_coins(user_id: int, amount: int) -> bool:
    user = get_user(user_id)
    if user["coins"] >= amount:
        user["coins"] -= amount
        mongo.save_user(user)
        return True
    return False


def use_coin(user_id: int) -> bool:
    if has_unlimited_coins(user_id):
        return True
    user = get_user(user_id)
    if user["coins"] > 0:
        user["coins"] -= 1
        mongo.save_user(user)
        return True
    return False


def is_user_blocked(user_id: int) -> Tuple[bool, str]:
    user = get_user(user_id)
    if user.get("is_blocked", False):
        return True, user.get("blocked_reason", "No reason provided")
    return False, ""


def block_user(user_id: int, reason: str = "Blocked by admin", blocked_by: int = None) -> bool:
    user = get_user(user_id)
    user["is_blocked"] = True
    user["blocked_reason"] = reason
    user["blocked_at"] = datetime.now().isoformat()
    user["blocked_by"] = blocked_by
    mongo.save_user(user)
    mongo.save_log("user_blocked", {"user_id": user_id, "reason": reason, "blocked_by": blocked_by})
    return True


def unblock_user(user_id: int) -> bool:
    user = get_user(user_id)
    user["is_blocked"] = False
    user["blocked_reason"] = None
    user["blocked_at"] = None
    user["blocked_by"] = None
    mongo.save_user(user)
    mongo.save_log("user_unblocked", {"user_id": user_id})
    return True


def is_admin(user_id: int) -> bool:
    if user_id in OWNER_IDS:
        return True
    user = get_user(user_id)
    return user.get("is_admin", False)


def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS


def has_unlimited_coins(user_id: int) -> bool:
    return is_admin(user_id)


def can_search(user_id: int) -> Tuple[bool, int, bool]:
    blocked, reason = is_user_blocked(user_id)
    if blocked:
        return False, 0, False

    if has_unlimited_coins(user_id):
        return True, 999999, False

    user = get_user(user_id)
    today = date.today().isoformat()
    if user["last_search_date"] != today:
        user["daily_searches"] = 0
        user["last_search_date"] = today
        mongo.save_user(user)

    if not settings.get("daily_free_enabled", True):
        if user["coins"] > 0:
            return True, 0, True
        else:
            return False, 0, False

    remaining = settings["daily_limit"] - user["daily_searches"]
    if remaining > 0:
        return True, remaining, False
    elif user["coins"] > 0:
        return True, 0, True
    else:
        return False, 0, False


def get_api_url(service: str) -> str:
    return api_settings.get("apis", {}).get(service, {}).get("url", DEFAULT_APIS.get(service, ""))


def is_api_enabled(service: str) -> bool:
    return api_settings.get("apis", {}).get(service, {}).get("enabled", True)


def update_api_url(service: str, new_url: str) -> bool:
    try:
        if service not in api_settings.get("apis", {}):
            api_settings["apis"][service] = {"enabled": True, "url": DEFAULT_APIS.get(service, "")}
        api_settings["apis"][service]["url"] = new_url
        mongo.save_api_setting(service, api_settings["apis"][service])
        return True
    except Exception as e:
        logger.error(f"Error updating API URL: {e}")
        return False


def toggle_api(service: str) -> bool:
    try:
        current = api_settings["apis"][service]["enabled"]
        api_settings["apis"][service]["enabled"] = not current
        mongo.save_api_setting(service, api_settings["apis"][service])
        return not current
    except Exception as e:
        logger.error(f"Error toggling API: {e}")
        return False


def save_search_result(user_id: int, search_type: str, query: str, result: dict):
    mongo.save_search_result(user_id, search_type, query, result)


# ==================== KEY GENERATION ====================
def generate_keys(key_type: str, count: int, credits: int) -> list:
    keys = []
    for _ in range(count):
        key_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
        full_key = f"{key_type.upper()}_{key_id}"

        key_data = {
            "key": full_key,
            "key_type": key_type.upper(),
            "credits": credits,
            "used_by": None,
            "used_at": None,
            "created_at": datetime.now().isoformat(),
            "is_used": False
        }

        success = mongo.save_key(full_key, key_data)
        if success:
            keys.append(full_key)
            logger.info(f"✅ Key generated: {full_key} with {credits} credits")
        else:
            logger.error(f"❌ Failed to save key: {full_key}")

    return keys


def redeem_key(user_id: int, key: str) -> Tuple[bool, str]:
    key = key.strip().upper()

    key_data = mongo.get_key(key)
    if not key_data:
        return False, "❌ Invalid key! Key not found."
    if key_data.get("is_used", False):
        return False, "❌ This key has already been redeemed!"

    key_data["is_used"] = True
    key_data["used_by"] = user_id
    key_data["used_at"] = datetime.now().isoformat()
    mongo.save_key(key, key_data)

    credits = key_data.get("credits", 0)
    add_coins(user_id, credits)

    user = get_user(user_id)
    if "redeemed_keys" not in user:
        user["redeemed_keys"] = []
    user["redeemed_keys"].append({"key": key, "credits": credits, "redeemed_at": datetime.now().isoformat()})
    mongo.save_user(user)

    return True, f"✅ Key redeemed successfully!\n💰 You received {credits} coins!"


def revoke_key(key: str) -> Tuple[bool, str]:
    key = key.strip().upper()
    key_data = mongo.get_key(key)
    if not key_data:
        return False, "❌ Key not found!"
    if key_data.get("is_used", False):
        return False, "❌ Cannot revoke a used key!"
    if mongo.delete_key(key):
        return True, f"✅ Key revoked successfully: `{key}`"
    return False, "❌ Failed to revoke key!"


def revoke_all_unused_keys(key_type: str = None) -> Tuple[bool, str]:
    count = mongo.delete_unused_keys(key_type)
    if count > 0:
        type_msg = f" of type '{key_type}'" if key_type and key_type != "all" else ""
        return True, f"✅ Revoked {count} unused keys{type_msg}!"
    return False, "❌ No unused keys found to revoke!"


def get_unused_keys(key_type: str = None) -> List[dict]:
    all_keys = mongo.get_all_keys()
    unused = [k for k in all_keys if not k.get("is_used", False)]
    if key_type and key_type != "all":
        unused = [k for k in unused if k.get("key_type") == key_type.upper()]
    return unused


def process_referral(new_user_id: int, ref_code: str) -> bool:
    all_users = mongo.get_all_users()
    referrer_id = None
    for user in all_users:
        if user.get("referral_code") == ref_code:
            referrer_id = user["user_id"]
            break
    if referrer_id and referrer_id != new_user_id:
        user = get_user(new_user_id)
        user["referred_by"] = referrer_id
        mongo.save_user(user)
        add_coins(referrer_id, settings["referral_coins"])
        referrer = get_user(referrer_id)
        if str(new_user_id) not in referrer.get("referrals", []):
            referrer.setdefault("referrals", []).append(str(new_user_id))
            mongo.save_user(referrer)
        return True
    return False


def find_user_by_identifier(identifier: str) -> Optional[int]:
    identifier = identifier.strip()

    if identifier.isdigit():
        user = mongo.get_user(int(identifier))
        if user:
            return int(identifier)

    username = identifier.lstrip('@').lower().strip()
    all_users = mongo.get_all_users()
    for user in all_users:
        if user.get("username", "").lower() == username:
            return user["user_id"]

    for user in all_users:
        if username in user.get("username", "").lower():
            return user["user_id"]

    return None


def get_bot_uptime() -> str:
    uptime_seconds = int(time.time() - BOT_START_TIME)
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)


def get_system_info_for_admin() -> dict:
    try:
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_used": psutil.virtual_memory().used // (1024**2),
            "memory_total": psutil.virtual_memory().total // (1024**2),
            "disk_percent": psutil.disk_usage('/').percent,
            "disk_used": psutil.disk_usage('/').used // (1024**2),
            "disk_total": psutil.disk_usage('/').total // (1024**2),
            "platform": platform.system(),
            "platform_release": platform.release(),
            "python_version": platform.python_version()
        }
    except:
        return {"cpu_percent": 0, "memory_percent": 0, "memory_used": 0, "memory_total": 0, "disk_percent": 0, "disk_used": 0, "disk_total": 0, "platform": "Unknown", "platform_release": "Unknown", "python_version": "Unknown"}


# ==================== TG INFO FEATURE ====================
async def search_tg_info(query: str) -> Dict:
    query = query.strip()
    if not query:
        return {"error": "Invalid query"}

    if not is_api_enabled("tg_info"):
        return {"error": "TG Info API is disabled by admin"}

    if query.startswith("@"):
        query = query[1:]

    encoded_query = urllib.parse.quote(query)
    url = f"{get_api_url('tg_info')}{encoded_query}"
    
    logger.info(f"TG Info API Request: {url}")
    
    data = await make_api_request(url, "tg_info")

    if "error" in data:
        return data

    if data.get("success") and data.get("number"):
        return {
            "success": True,
            "query": query,
            "tg_id": data.get("tg_id"),
            "number": data.get("number"),
            "country": data.get("country", "Unknown"),
            "country_code": data.get("country_code", ""),
            "msg": data.get("msg", "Details fetched"),
            "raw": data
        }
    else:
        error_msg = data.get("msg", "No details found")
        return {"error": f"No details found for: {query}"}


def format_tg_info(result: Dict, query: str) -> str:
    if "error" in result:
        return f"❌ *TG INFO SEARCH FAILED*\n🔍 `{query}`\n⚠️ {result['error']}"

    output = f"\n✅ *TELEGRAM USER INFO*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    output += f"🔍 *Query:* `{query}`\n"
    output += f"🆔 *TG ID:* `{result.get('tg_id', 'N/A')}`\n"
    output += f"📱 *Phone Number:* `{result.get('number', 'N/A')}`\n"
    output += f"🌍 *Country:* {result.get('country', 'N/A')}\n"
    output += f"📞 *Country Code:* {result.get('country_code', 'N/A')}\n"
    output += f"📝 *Message:* {result.get('msg', 'Details fetched')}\n"
    output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    output += f"\n\n👑 *Developer:* [{DEVELOPER_USERNAME}]({DEVELOPER_LINK})"
    return output


async def tg_info_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await check_maintenance(update, context):
        return ConversationHandler.END

    if not settings.get("bot_active", True) and not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Bot is currently disabled by admin!", reply_markup=get_main_keyboard(update.effective_user.id))
        return ConversationHandler.END

    if not is_admin(update.effective_user.id):
        if not await check_group_approval(update, context):
            return ConversationHandler.END
        if not await check_mandatory_channel(update, context):
            return ConversationHandler.END

    user_id = update.effective_user.id

    can, remaining, use_coin_flag = can_search(user_id)
    if not can:
        user = get_user(user_id)
        await update.message.reply_text(
            f"❌ *Daily Limit Reached!*\n💰 Your Coins: {user['coins']}\n\nBuy more coins or share referral link!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard(user_id)
        )
        return ConversationHandler.END
    
    if use_coin_flag:
        await update.message.reply_text("⚠️ Using 1 coin for this search.", parse_mode=ParseMode.MARKDOWN)
        context.user_data["use_coin"] = True
    else:
        context.user_data["use_coin"] = False

    await update.message.reply_text(
        "📱 *Enter Telegram Username or ID*\n\n"
        "Examples:\n"
        "• `@KINGGKAI` (username)\n"
        "• `1451422178` (user ID)\n\n"
        "_Note: Make sure the user has interacted with the bot before._",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_cancel_keyboard()
    )
    return ASKING_TG_USERNAME


async def handle_tg_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await check_maintenance(update, context):
        return ConversationHandler.END

    user_id = update.effective_user.id
    text = update.message.text.strip()

    if text in ["❌ Cancel", "🔙 Back"]:
        await update.message.reply_text("❌ Cancelled", reply_markup=get_main_keyboard(user_id))
        return ConversationHandler.END

    if not text:
        await update.message.reply_text("❌ Please enter a valid username or ID!", reply_markup=get_cancel_keyboard())
        return ASKING_TG_USERNAME

    if context.user_data.get("use_coin", False):
        if not use_coin(user_id):
            await update.message.reply_text("❌ Not enough coins!", reply_markup=get_main_keyboard(user_id))
            return ConversationHandler.END

    await update.message.chat.send_action(action="typing")
    status_msg = await update.message.reply_text("⏳ Searching Telegram user info...")

    result = await search_tg_info(text)

    await status_msg.delete()

    if "error" not in result:
        update_user_stats(user_id)
        save_search_result(user_id, "tg_info", text, result)

    formatted = format_tg_info(result, text)

    can, remaining, _ = can_search(user_id)
    user = get_user(user_id)
    info = f"\n\n👑 Unlimited" if has_unlimited_coins(user_id) else f"\n\n📊 Free left: {remaining}\n💰 Coins: {user['coins']}"

    await send_long_message(update, formatted + info, disable_web_page_preview=True)
    await update.message.reply_text("✅ Search Complete", reply_markup=get_main_keyboard(user_id))

    return ConversationHandler.END


# ==================== API RESPONSE PROCESSING ====================
def process_api_response(data: Dict, search_type: str, query: str) -> Dict:
    if "error" in data:
        return data
    if "SUCCESS" in data or "success" in data:
        is_success = data.get("SUCCESS", data.get("success", False))
        query_val = data.get("QUERY", data.get("query", query))
        count = data.get("COUNT", data.get("count", 0))
        results = data.get("RESULTS", data.get("results", data.get("data", [])))
        if "DEVELOPER" in data:
            data.pop("DEVELOPER")
        if "developer" in data:
            data.pop("developer")
        return {"success": is_success, "query": query_val, "count": count, "results": results, "raw": data}
    if data.get("response", {}).get("parameters", {}).get("success") and data.get("response", {}).get("data"):
        api_data = data["response"]["data"]
        if isinstance(api_data, list):
            return {"success": True, "query": query, "count": len(api_data), "results": api_data, "raw": data}
        else:
            return {"success": True, "query": query, "count": 1, "results": [api_data], "raw": data}
    if data.get("status") == "success" and data.get("result"):
        result_data = data["result"]
        if isinstance(result_data, list):
            return {"success": True, "query": query, "count": len(result_data), "results": result_data, "raw": data}
        else:
            return {"success": True, "query": query, "count": 1, "results": [result_data], "raw": data}
    if data.get("data"):
        api_data = data["data"]
        if isinstance(api_data, list) and len(api_data) > 0:
            return {"success": True, "query": query, "count": len(api_data), "results": api_data, "raw": data}
    return {"error": "No data found"}


# ==================== FORMATTING FUNCTIONS WITH FILE OUTPUT ====================
def format_result_as_file(text: str, filename: str) -> str:
    import tempfile
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
    temp_file.write(text)
    temp_file.close()
    return temp_file.name


async def send_long_message(update: Update, text: str, parse_mode: str = ParseMode.MARKDOWN, **kwargs):
    """Send long message - if > 3 records, send as file"""
    # Count number of "📋 Record" occurrences in the text
    record_count = text.count("📋 Record")
    
    # If more than 3 records, send as file
    if record_count > 3:
        file_path = format_result_as_file(text, "search_result.txt")
        with open(file_path, 'rb') as f:
            # Extract first few lines for caption
            lines = text.split('\n')
            caption_lines = []
            for line in lines[:15]:
                caption_lines.append(line)
                if "📊 *Total Records:" in line:
                    break
            
            caption = "\n".join(caption_lines)
            if len(caption) > 900:
                caption = caption[:897] + "..."
            
            # Send file
            await update.message.reply_document(
                document=f, 
                filename="search_result.txt", 
                caption=f"📄 *Search Result*\n\n{caption}\n\n📁 *Full result saved as file*\n\n👑 *Developer:* @{DEVELOPER_USERNAME}",
                parse_mode=ParseMode.MARKDOWN
            )
        os.unlink(file_path)
    else:
        await update.message.reply_text(text, parse_mode=parse_mode, **kwargs)


def format_indian_number(processed: Dict, number: str) -> str:
    if "error" in processed:
        return f"❌ *SEARCH FAILED*\n📱 `{number}`\n⚠️ {processed['error']}"
    results = processed.get("results", [])
    count = processed.get("count", len(results))
    output = f"\n✅ *NUMBER SEARCH RESULT*\n📱 *Mobile:* `{number}`\n📊 *Total Records:* {count}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    # Show first 3 records, rest will be in file
    max_display = 3
    display_results = results[:max_display] if len(results) > max_display else results
    
    for idx, data in enumerate(display_results, 1):
        output += f"\n📋 *Record {idx}:*\n"
        if data.get('NAME') or data.get('name'):
            output += f"👤 *Name:* {escape_text(data.get('NAME', data.get('name', '')))}\n"
        if data.get('FNAME') or data.get('fname') or data.get('FATHER'):
            output += f"👨 *Father:* {escape_text(data.get('FNAME', data.get('fname', data.get('FATHER', ''))))}\n"
        if data.get('MOBILE') or data.get('mobile') or data.get('num'):
            output += f"📞 *Mobile:* `{data.get('MOBILE', data.get('mobile', data.get('num', '')))}`\n"
        if data.get('ALT') or data.get('alt'):
            output += f"📱 *Alt:* `{data.get('ALT', data.get('alt', ''))}`\n"
        if data.get('CIRCLE') or data.get('circle'):
            output += f"📡 *Circle:* {escape_text(data.get('CIRCLE', data.get('circle', '')))}\n"
        if data.get('AADHAR') or data.get('aadhar') or data.get('ID'):
            output += f"🆔 *Aadhar:* `{data.get('AADHAR', data.get('aadhar', data.get('ID', '')))}`\n"
        if data.get('EMAIL') or data.get('email'):
            output += f"📧 *Email:* {escape_text(data.get('EMAIL', data.get('email', '')))}\n"
        if data.get('ADDRESS') or data.get('address'):
            addr = data.get('ADDRESS', data.get('address', '')).replace('!', ' ').strip()
            output += f"📍 *Address:* {escape_text(addr)}\n"
        output += "─" * 35 + "\n"
    
    if count > max_display:
        output += f"\n_... and {count - max_display} more records (check file)_\n"
    
    output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    output += f"\n\n👑 *Developer:* [{DEVELOPER_USERNAME}]({DEVELOPER_LINK})"
    return output


def format_indian_aadhar(processed: Dict, aadhar: str) -> str:
    if "error" in processed:
        return f"❌ *AADHAR SEARCH FAILED*\n🆔 `{aadhar}`\n⚠️ {processed['error']}"
    results = processed.get("results", [])
    count = processed.get("count", len(results))
    seen = set()
    unique_results = []
    for item in results:
        mobile = item.get('MOBILE', item.get('mobile', item.get('num', '')))
        if mobile and mobile not in seen:
            seen.add(mobile)
            unique_results.append(item)
    
    output = f"\n✅ *AADHAR SEARCH RESULT*\n🆔 *Aadhar:* `{aadhar}`\n📊 *Records:* {len(unique_results)} (Total: {count})\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    max_display = 3
    display_results = unique_results[:max_display] if len(unique_results) > max_display else unique_results
    
    for idx, data in enumerate(display_results, 1):
        output += f"\n📋 *Record {idx}:*\n"
        if data.get('NAME') or data.get('name'):
            output += f"👤 *Name:* {escape_text(data.get('NAME', data.get('name', '')))}\n"
        if data.get('FNAME') or data.get('fname') or data.get('FATHER'):
            output += f"👨 *Father:* {escape_text(data.get('FNAME', data.get('fname', data.get('FATHER', ''))))}\n"
        if data.get('MOBILE') or data.get('mobile') or data.get('num'):
            output += f"📞 *Mobile:* `{data.get('MOBILE', data.get('mobile', data.get('num', '')))}`\n"
        if data.get('ALT') or data.get('alt'):
            output += f"📱 *Alt:* `{data.get('ALT', data.get('alt', ''))}`\n"
        if data.get('EMAIL') or data.get('email'):
            output += f"📧 *Email:* {escape_text(data.get('EMAIL', data.get('email', '')))}\n"
        if data.get('CIRCLE') or data.get('circle'):
            output += f"📡 *Circle:* {escape_text(data.get('CIRCLE', data.get('circle', '')))}\n"
        if data.get('ADDRESS') or data.get('address'):
            addr = data.get('ADDRESS', data.get('address', '')).replace('!', ' ').strip()
            output += f"📍 *Address:* {escape_text(addr)}\n"
        output += "─" * 35 + "\n"
    
    if len(unique_results) > max_display:
        output += f"\n_... and {len(unique_results) - max_display} more records (check file)_\n"
    
    output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    output += f"\n\n👑 *Developer:* [{DEVELOPER_USERNAME}]({DEVELOPER_LINK})"
    return output


def format_pak_number(processed: Dict, number: str) -> str:
    if "error" in processed:
        return f"❌ *PAKISTAN NUMBER SEARCH FAILED*\n📱 `{number}`\n⚠️ {processed['error']}"
    results = processed.get("results", [])
    count = processed.get("count", len(results))
    output = f"\n✅ *PAKISTAN NUMBER RESULT*\n📱 *Number:* `{number}`\n📊 *Records:* {count}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    max_display = 3
    display_results = results[:max_display] if len(results) > max_display else results
    
    for idx, data in enumerate(display_results, 1):
        output += f"\n📋 *Record {idx}:*\n"
        if data.get('NAME') or data.get('name') or data.get('Name'):
            output += f"👤 *Name:* {escape_text(data.get('NAME', data.get('name', data.get('Name', ''))))}\n"
        if data.get('FATHER') or data.get('father') or data.get('Father'):
            output += f"👨 *Father:* {escape_text(data.get('FATHER', data.get('father', data.get('Father', ''))))}\n"
        if data.get('CNIC') or data.get('cnic'):
            output += f"🪪 *CNIC:* `{data.get('CNIC', data.get('cnic', ''))}`\n"
        if data.get('ADDRESS') or data.get('address') or data.get('Address'):
            output += f"📍 *Address:* {escape_text(data.get('ADDRESS', data.get('address', data.get('Address', ''))))}\n"
        if data.get('OPERATOR') or data.get('operator'):
            output += f"📡 *Operator:* {escape_text(data.get('OPERATOR', data.get('operator', '')))}\n"
        output += "─" * 35 + "\n"
    
    if count > max_display:
        output += f"\n_... and {count - max_display} more records (check file)_\n"
    
    output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    output += f"\n\n👑 *Developer:* [{DEVELOPER_USERNAME}]({DEVELOPER_LINK})"
    return output


def format_pak_cnic(processed: Dict, cnic: str) -> str:
    if "error" in processed:
        return f"❌ *PAKISTAN CNIC SEARCH FAILED*\n🪪 `{cnic}`\n⚠️ {processed['error']}"
    results = processed.get("results", [])
    count = processed.get("count", len(results))
    seen = set()
    unique_results = []
    for item in results:
        mobile = item.get('MOBILE', item.get('mobile', item.get('Mobile', '')))
        if mobile and mobile not in seen:
            seen.add(mobile)
            unique_results.append(item)
    
    output = f"\n✅ *PAKISTAN CNIC RESULT*\n🪪 *CNIC:* `{cnic}`\n📊 *Linked Numbers:* {len(unique_results)} (Total: {count})\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    max_display = 3
    display_results = unique_results[:max_display] if len(unique_results) > max_display else unique_results
    
    for idx, data in enumerate(display_results, 1):
        output += f"\n📋 *Record {idx}:*\n"
        if data.get('NAME') or data.get('name') or data.get('Name'):
            output += f"👤 *Name:* {escape_text(data.get('NAME', data.get('name', data.get('Name', ''))))}\n"
        if data.get('MOBILE') or data.get('mobile') or data.get('Mobile'):
            output += f"📱 *Mobile:* `{data.get('MOBILE', data.get('mobile', data.get('Mobile', '')))}`\n"
        if data.get('ADDRESS') or data.get('address') or data.get('Address'):
            output += f"📍 *Address:* {escape_text(data.get('ADDRESS', data.get('address', data.get('Address', ''))))}\n"
        output += "─" * 35 + "\n"
    
    if len(unique_results) > max_display:
        output += f"\n_... and {len(unique_results) - max_display} more records (check file)_\n"
    
    output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    output += f"\n\n👑 *Developer:* [{DEVELOPER_USERNAME}]({DEVELOPER_LINK})"
    return output


def format_pak_police(processed: Dict, number: str) -> str:
    if "error" in processed:
        return f"❌ *POLICE RECORD SEARCH FAILED*\n📱 `{number}`\n⚠️ {processed['error']}"
    results = processed.get("results", [])
    count = processed.get("count", len(results))
    if count == 0:
        return f"❌ *NO POLICE RECORD FOUND*\n📱 `{number}`"
    
    output = f"\n✅ *PAKISTAN POLICE RECORD*\n📱 *Number:* `{number}`\n📊 *Records:* {count}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    max_display = 3
    display_results = results[:max_display] if len(results) > max_display else results
    
    for idx, data in enumerate(display_results, 1):
        output += f"\n🚔 *Record {idx}:*\n"
        if data.get('NAME') or data.get('name') or data.get('Name'):
            output += f"👤 *Name:* {escape_text(data.get('NAME', data.get('name', data.get('Name', ''))))}\n"
        if data.get('CONTACT') or data.get('contact') or data.get('Contact'):
            output += f"📱 *Contact:* `{data.get('CONTACT', data.get('contact', data.get('Contact', '')))}`\n"
        if data.get('CNIC') or data.get('cnic'):
            output += f"🪪 *CNIC:* `{data.get('CNIC', data.get('cnic', ''))}`\n"
        if data.get('REGION') or data.get('region') or data.get('Region'):
            output += f"📍 *Region:* {escape_text(data.get('REGION', data.get('region', data.get('Region', ''))))}\n"
        if data.get('DISTRICT') or data.get('district') or data.get('District'):
            output += f"🏛️ *District:* {escape_text(data.get('DISTRICT', data.get('district', data.get('District', ''))))}\n"
        if data.get('POLICE_STATION') or data.get('police_station') or data.get('Police Station'):
            output += f"🚓 *Station:* {escape_text(data.get('POLICE_STATION', data.get('police_station', data.get('Police Station', ''))))}\n"
        if data.get('COMPLAINT_RECORD') or data.get('complaint_record') or data.get('Complaint Record'):
            output += f"📋 *Complaint:* {escape_text(data.get('COMPLAINT_RECORD', data.get('complaint_record', data.get('Complaint Record', ''))))}\n"
        if data.get('OFFENSE') or data.get('offense') or data.get('Offense'):
            output += f"⚠️ *Offense:* {escape_text(data.get('OFFENSE', data.get('offense', data.get('Offense', ''))))}\n"
        if data.get('COMPLAINT_STATUS') or data.get('complaint_status') or data.get('Complaint Status'):
            output += f"📊 *Status:* {escape_text(data.get('COMPLAINT_STATUS', data.get('complaint_status', data.get('Complaint Status', ''))))}\n"
        if data.get('OFFICER_NAME') or data.get('officer_name') or data.get('Officer Name'):
            output += f"👮 *Officer:* {escape_text(data.get('OFFICER_NAME', data.get('officer_name', data.get('Officer Name', ''))))}\n"
        output += "─" * 35 + "\n"
    
    if count > max_display:
        output += f"\n_... and {count - max_display} more records (check file)_\n"
    
    output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    output += f"\n\n👑 *Developer:* [{DEVELOPER_USERNAME}]({DEVELOPER_LINK})"
    return output


def format_gst_billing(processed: Dict, gstin: str) -> str:
    if "error" in processed:
        return f"❌ *GST BILLING SEARCH FAILED*\n💰 `{gstin}`\n⚠️ {processed['error']}"
    results = processed.get("results", [])
    output = f"\n✅ *GST BILLING HISTORY*\n💰 *GSTIN:* `{gstin}`\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    if results and results[0].get("error_code") == 206:
        output += "\n⚠️ *Failed to fetch billing data*\n"
    elif results:
        max_display = 3
        display_results = results[:max_display] if len(results) > max_display else results
        
        for idx, data in enumerate(display_results, 1):
            output += f"\n📋 *Invoice {idx}:*\n"
            if data.get('INVOICE_NO') or data.get('invoice_no'):
                output += f"📄 *Invoice:* {escape_text(data.get('INVOICE_NO', data.get('invoice_no', '')))}\n"
            if data.get('INVOICE_DATE') or data.get('invoice_date'):
                output += f"📅 *Date:* {escape_text(data.get('INVOICE_DATE', data.get('invoice_date', '')))}\n"
            if data.get('BUYER_NAME') or data.get('buyer_name'):
                output += f"👤 *Buyer:* {escape_text(data.get('BUYER_NAME', data.get('buyer_name', '')))}\n"
            if data.get('TOTAL_AMOUNT') or data.get('total_amount'):
                output += f"💰 *Amount:* ₹{escape_text(data.get('TOTAL_AMOUNT', data.get('total_amount', '')))}\n"
            output += "─" * 35 + "\n"
        
        if len(results) > max_display:
            output += f"\n_... and {len(results) - max_display} more invoices (check file)_\n"
    else:
        output += "\n⚠️ No billing data available\n"
    
    output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    output += f"\n\n👑 *Developer:* [{DEVELOPER_USERNAME}]({DEVELOPER_LINK})"
    return output


def format_pan_gst(processed: Dict, pan: str) -> str:
    if "error" in processed:
        return f"❌ *PAN TO GST SEARCH FAILED*\n📇 `{pan}`\n⚠️ {processed['error']}"
    results = processed.get("results", [])
    count = processed.get("count", len(results))
    output = f"\n✅ *PAN TO GST RESULT*\n📇 *PAN:* `{pan}`\n📊 *GSTINs Found:* {count}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    max_display = 3
    display_results = results[:max_display] if len(results) > max_display else results
    
    for idx, data in enumerate(display_results, 1):
        output += f"\n🏢 *Business {idx}:*\n"
        if data.get('LGNM') or data.get('lgnm'):
            output += f"📛 *Legal Name:* {escape_text(data.get('LGNM', data.get('lgnm', '')))}\n"
        if data.get('TRADENAM') or data.get('tradeNam'):
            output += f"🏷️ *Trade Name:* {escape_text(data.get('TRADENAM', data.get('tradeNam', '')))}\n"
        if data.get('GSTIN') or data.get('gstin'):
            output += f"💰 *GSTIN:* `{data.get('GSTIN', data.get('gstin', ''))}`\n"
        if data.get('STS') or data.get('sts'):
            output += f"📊 *Status:* {escape_text(data.get('STS', data.get('sts', '')))}\n"
        if data.get('DTY') or data.get('dty'):
            output += f"📝 *Type:* {escape_text(data.get('DTY', data.get('dty', '')))}\n"
        if data.get('CTB') or data.get('ctb'):
            output += f"🏛️ *Business Type:* {escape_text(data.get('CTB', data.get('ctb', '')))}\n"
        if data.get('RGDT') or data.get('rgdt'):
            output += f"📅 *Reg Date:* {escape_text(data.get('RGDT', data.get('rgdt', '')))}\n"
        if data.get('PRADR') or data.get('pradr'):
            addr = data.get('PRADR', data.get('pradr', {}))
            if isinstance(addr, dict):
                addr_data = addr.get('addr', {})
                address_parts = []
                if addr_data.get('bno'):
                    address_parts.append(addr_data['bno'])
                if addr_data.get('st'):
                    address_parts.append(addr_data['st'])
                if addr_data.get('loc'):
                    address_parts.append(addr_data['loc'])
                if addr_data.get('stcd'):
                    address_parts.append(addr_data['stcd'])
                if addr_data.get('pncd'):
                    address_parts.append(addr_data['pncd'])
                if address_parts:
                    output += f"📍 *Address:* {escape_text(', '.join(address_parts))}\n"
        if data.get('NBA') or data.get('nba'):
            nba = data.get('NBA', data.get('nba', []))
            if isinstance(nba, list):
                output += f"💼 *Nature:* {escape_text(', '.join(nba))}\n"
        output += "─" * 35 + "\n"
    
    if count > max_display:
        output += f"\n_... and {count - max_display} more GSTINs (check file)_\n"
    
    output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    output += f"\n\n👑 *Developer:* [{DEVELOPER_USERNAME}]({DEVELOPER_LINK})"
    return output


def format_aadhar_family(processed: Dict, aadhar: str) -> str:
    if "error" in processed:
        return f"❌ *AADHAR FAMILY SEARCH FAILED*\n🆔 `{aadhar}`\n⚠️ {processed['error']}"
    results = processed.get("results", [])
    count = processed.get("count", len(results))
    output = f"\n✅ *AADHAR FAMILY RESULT*\n🆔 *Aadhar:* `{aadhar}`\n👨‍👩‍👧 *Family Members:* {count}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    max_display = 3
    display_results = results[:max_display] if len(results) > max_display else results
    
    for idx, data in enumerate(display_results, 1):
        output += f"\n👤 *Member {idx}:*\n"
        if data.get('NAME') or data.get('name'):
            output += f"📛 *Name:* {escape_text(data.get('NAME', data.get('name', '')))}\n"
        if data.get('RELATION') or data.get('relation'):
            output += f"🔗 *Relation:* {escape_text(data.get('RELATION', data.get('relation', '')))}\n"
        if data.get('AADHAR') or data.get('aadhar'):
            output += f"🆔 *Aadhar:* `{data.get('AADHAR', data.get('aadhar', ''))}`\n"
        if data.get('MOBILE') or data.get('mobile'):
            output += f"📱 *Mobile:* `{data.get('MOBILE', data.get('mobile', ''))}`\n"
        if data.get('DOB') or data.get('dob'):
            output += f"🎂 *DOB:* {escape_text(data.get('DOB', data.get('dob', '')))}\n"
        if data.get('GENDER') or data.get('gender'):
            output += f"⚥ *Gender:* {escape_text(data.get('GENDER', data.get('gender', '')))}\n"
        output += "─" * 35 + "\n"
    
    if count > max_display:
        output += f"\n_... and {count - max_display} more members (check file)_\n"
    
    output += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    output += f"\n\n👑 *Developer:* [{DEVELOPER_USERNAME}]({DEVELOPER_LINK})"
    return output


# ==================== API SEARCH FUNCTIONS ====================
async def make_api_request(url: str, service: str) -> Dict:
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if "DEVELOPER" in data:
                        del data["DEVELOPER"]
                    if "developer" in data:
                        del data["developer"]
                    return data
                elif response.status == 404:
                    return {"error": "No data found (HTTP 404)"}
                else:
                    return {"error": f"API Error: HTTP {response.status}"}
    except asyncio.TimeoutError:
        return {"error": "Request timeout"}
    except aiohttp.ClientError as e:
        return {"error": f"Connection error: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}


async def search_indian_number(number: str) -> Dict:
    number = ''.join(filter(str.isdigit, number))
    if len(number) < 10:
        return {"error": "Invalid number length"}
    blocked = mongo.get_blocked_number(number)
    if blocked:
        return {"error": f"Number blocked: {blocked.get('reason', 'Unknown')}"}
    if not is_api_enabled("num"):
        return {"error": "API disabled by admin"}
    url = f"{get_api_url('num')}{number}"
    data = await make_api_request(url, "num")
    if "error" in data:
        return data
    processed = process_api_response(data, "num", number)
    return processed


async def search_indian_aadhar(aadhar: str) -> Dict:
    aadhar = ''.join(filter(str.isdigit, aadhar))
    if len(aadhar) != 12:
        return {"error": "Invalid Aadhar length (12 digits required)"}
    if not is_api_enabled("aadhar"):
        return {"error": "API disabled by admin"}
    url = f"{get_api_url('aadhar')}{aadhar}"
    data = await make_api_request(url, "aadhar")
    if "error" in data:
        return data
    processed = process_api_response(data, "aadhar", aadhar)
    return processed


async def search_pak_number(number: str) -> Dict:
    number = ''.join(filter(str.isdigit, number))
    if len(number) < 10:
        return {"error": "Invalid Pakistan number"}
    if not is_api_enabled("pak_num"):
        return {"error": "API disabled by admin"}
    url = f"{get_api_url('pak_num')}{number}"
    data = await make_api_request(url, "pak_num")
    if "error" in data:
        return data
    processed = process_api_response(data, "pak_num", number)
    return processed


async def search_pak_cnic(cnic: str) -> Dict:
    cnic = ''.join(filter(str.isdigit, cnic))
    if len(cnic) != 13:
        return {"error": "Invalid CNIC length (13 digits required)"}
    if not is_api_enabled("pak_cnic"):
        return {"error": "API disabled by admin"}
    url = f"{get_api_url('pak_cnic')}{cnic}"
    data = await make_api_request(url, "pak_cnic")
    if "error" in data:
        return data
    processed = process_api_response(data, "pak_cnic", cnic)
    return processed


async def search_pak_police(number: str) -> Dict:
    number = ''.join(filter(str.isdigit, number))
    if not is_api_enabled("pak_police"):
        return {"error": "API disabled by admin"}
    url = f"{get_api_url('pak_police')}{number}"
    data = await make_api_request(url, "pak_police")
    if "error" in data:
        return data
    processed = process_api_response(data, "pak_police", number)
    return processed


async def search_gst_billing(gstin: str) -> Dict:
    gstin = gstin.strip().upper()
    if len(gstin) != 15:
        return {"error": "Invalid GSTIN length (15 characters required)"}
    if not is_api_enabled("gst_billing"):
        return {"error": "API disabled by admin"}
    url = f"{get_api_url('gst_billing')}{gstin}"
    data = await make_api_request(url, "gst_billing")
    if "error" in data:
        return data
    processed = process_api_response(data, "gst_billing", gstin)
    if processed.get("results") and processed["results"][0].get("error_code") == 206:
        return {"error": "Failed to fetch billing data"}
    return processed


async def search_pan_gst(pan: str) -> Dict:
    pan = pan.strip().upper()
    if len(pan) != 10:
        return {"error": "Invalid PAN length (10 characters required)"}
    if not is_api_enabled("pan_gst"):
        return {"error": "API disabled by admin"}
    url = f"{get_api_url('pan_gst')}{pan}"
    data = await make_api_request(url, "pan_gst")
    if "error" in data:
        return data
    processed = process_api_response(data, "pan_gst", pan)
    return processed


async def search_aadhar_family(aadhar: str) -> Dict:
    aadhar = ''.join(filter(str.isdigit, aadhar))
    if len(aadhar) != 12:
        return {"error": "Invalid Aadhar length (12 digits required)"}
    if not is_api_enabled("aadhar_family"):
        return {"error": "API disabled by admin"}
    url = f"{get_api_url('aadhar_family')}{aadhar}"
    data = await make_api_request(url, "aadhar_family")
    if "error" in data:
        return data
    processed = process_api_response(data, "aadhar_family", aadhar)
    return processed


# ==================== SEARCH HANDLERS ====================
async def check_and_start_search(update: Update, context: ContextTypes.DEFAULT_TYPE, search_type: str) -> bool:
    if await check_maintenance(update, context):
        return False

    if not settings.get("bot_active", True) and not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Bot is currently disabled by admin!", reply_markup=get_main_keyboard(update.effective_user.id))
        return False

    if not is_admin(update.effective_user.id):
        if not await check_group_approval(update, context):
            return False
        if not await check_mandatory_channel(update, context):
            return False

    user_id = update.effective_user.id

    can, remaining, use_coin_flag = can_search(user_id)
    if not can:
        user = get_user(user_id)
        await update.message.reply_text(
            f"❌ *Daily Limit Reached!*\n💰 Your Coins: {user['coins']}\n\nBuy more coins or share referral link!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_keyboard(user_id)
        )
        return False
    if use_coin_flag:
        await update.message.reply_text("⚠️ Using 1 coin for this search.", parse_mode=ParseMode.MARKDOWN)
        context.user_data["use_coin"] = True
    else:
        context.user_data["use_coin"] = False

    context.user_data["search_type"] = search_type
    return True


async def indian_number_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await check_and_start_search(update, context, "num"):
        return ConversationHandler.END
    await update.message.reply_text("🔍 *Enter Indian Mobile Number*\nExample: `9876543210`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_cancel_keyboard())
    return ASKING_NUMBER


async def indian_aadhar_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await check_and_start_search(update, context, "aadhar"):
        return ConversationHandler.END
    await update.message.reply_text("🆔 *Enter 12-digit Aadhar Number*\nExample: `123456789012`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_cancel_keyboard())
    return ASKING_AADHAR


async def pak_number_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await check_and_start_search(update, context, "pak_num"):
        return ConversationHandler.END
    await update.message.reply_text("🇵🇰 *Enter Pakistan Mobile Number*\nExample: `3001234567`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_cancel_keyboard())
    return ASKING_PAK_NUM


async def pak_cnic_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await check_and_start_search(update, context, "pak_cnic"):
        return ConversationHandler.END
    await update.message.reply_text("🪪 *Enter 13-digit Pakistan CNIC*\nExample: `1234567890123`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_cancel_keyboard())
    return ASKING_PAK_CNIC


async def pak_police_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await check_and_start_search(update, context, "pak_police"):
        return ConversationHandler.END
    await update.message.reply_text("🚔 *Enter Pakistan Mobile Number for Police Record*\nExample: `3001234567`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_cancel_keyboard())
    return ASKING_PAK_POLICE


async def gst_billing_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await check_and_start_search(update, context, "gst_billing"):
        return ConversationHandler.END
    await update.message.reply_text("💰 *Enter 15-digit GSTIN*\nExample: `09AAYFK4129N1ZF`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_cancel_keyboard())
    return ASKING_GST_BILLING


async def pan_gst_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await check_and_start_search(update, context, "pan_gst"):
        return ConversationHandler.END
    await update.message.reply_text("📇 *Enter 10-character PAN*\nExample: `AAYFK4129N`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_cancel_keyboard())
    return ASKING_PAN_GST


async def aadhar_family_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await check_and_start_search(update, context, "aadhar_family"):
        return ConversationHandler.END
    await update.message.reply_text("👨‍👩‍👧 *Enter 12-digit Aadhar Number for Family Details*\nExample: `123456789012`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_cancel_keyboard())
    return ASKING_AADHAR_FAMILY


# ==================== INPUT HANDLERS ====================
async def handle_indian_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await check_maintenance(update, context):
        return ConversationHandler.END
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if text == "❌ Cancel" or text == "🔙 Back":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_main_keyboard(user_id))
        return ConversationHandler.END
    number = ''.join(filter(str.isdigit, text))
    if len(number) < 10:
        await update.message.reply_text("❌ Invalid number!", reply_markup=get_cancel_keyboard())
        return ASKING_NUMBER
    if context.user_data.get("use_coin", False):
        if not use_coin(user_id):
            await update.message.reply_text("❌ Not enough coins!", reply_markup=get_main_keyboard(user_id))
            return ConversationHandler.END
    await update.message.chat.send_action(action="typing")
    status_msg = await update.message.reply_text("⏳ Searching...")
    result = await search_indian_number(number)
    await status_msg.delete()
    if "error" not in result:
        update_user_stats(user_id)
        save_search_result(user_id, "indian_number", number, result)
    formatted = format_indian_number(result, number)
    can, remaining, _ = can_search(user_id)
    user = get_user(user_id)
    info = f"\n\n👑 Unlimited" if has_unlimited_coins(user_id) else f"\n\n📊 Free left: {remaining}\n💰 Coins: {user['coins']}"
    
    full_text = formatted + info
    await send_long_message(update, full_text, disable_web_page_preview=True)
    await update.message.reply_text("✅ Search Complete", reply_markup=get_main_keyboard(user_id))
    return ConversationHandler.END


async def handle_indian_aadhar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await check_maintenance(update, context):
        return ConversationHandler.END
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if text == "❌ Cancel" or text == "🔙 Back":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_main_keyboard(user_id))
        return ConversationHandler.END
    aadhar = ''.join(filter(str.isdigit, text))
    if len(aadhar) != 12:
        await update.message.reply_text("❌ Invalid Aadhar! Must be 12 digits.", reply_markup=get_cancel_keyboard())
        return ASKING_AADHAR
    if context.user_data.get("use_coin", False):
        if not use_coin(user_id):
            await update.message.reply_text("❌ Not enough coins!", reply_markup=get_main_keyboard(user_id))
            return ConversationHandler.END
    await update.message.chat.send_action(action="typing")
    status_msg = await update.message.reply_text("⏳ Searching Aadhar...")
    result = await search_indian_aadhar(aadhar)
    await status_msg.delete()
    if "error" not in result:
        update_user_stats(user_id)
        save_search_result(user_id, "indian_aadhar", aadhar, result)
    formatted = format_indian_aadhar(result, aadhar)
    can, remaining, _ = can_search(user_id)
    user = get_user(user_id)
    info = f"\n\n👑 Unlimited" if has_unlimited_coins(user_id) else f"\n\n📊 Free left: {remaining}\n💰 Coins: {user['coins']}"
    
    full_text = formatted + info
    await send_long_message(update, full_text, disable_web_page_preview=True)
    await update.message.reply_text("✅ Search Complete", reply_markup=get_main_keyboard(user_id))
    return ConversationHandler.END


async def handle_pak_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await check_maintenance(update, context):
        return ConversationHandler.END
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if text == "❌ Cancel" or text == "🔙 Back":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_main_keyboard(user_id))
        return ConversationHandler.END
    number = ''.join(filter(str.isdigit, text))
    if context.user_data.get("use_coin", False):
        if not use_coin(user_id):
            await update.message.reply_text("❌ Not enough coins!", reply_markup=get_main_keyboard(user_id))
            return ConversationHandler.END
    await update.message.chat.send_action(action="typing")
    status_msg = await update.message.reply_text("⏳ Searching Pakistan Number...")
    result = await search_pak_number(number)
    await status_msg.delete()
    if "error" not in result:
        update_user_stats(user_id)
        save_search_result(user_id, "pak_number", number, result)
    formatted = format_pak_number(result, number)
    can, remaining, _ = can_search(user_id)
    user = get_user(user_id)
    info = f"\n\n👑 Unlimited" if has_unlimited_coins(user_id) else f"\n\n📊 Free left: {remaining}\n💰 Coins: {user['coins']}"
    
    full_text = formatted + info
    await send_long_message(update, full_text, disable_web_page_preview=True)
    await update.message.reply_text("✅ Search Complete", reply_markup=get_main_keyboard(user_id))
    return ConversationHandler.END


async def handle_pak_cnic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await check_maintenance(update, context):
        return ConversationHandler.END
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if text == "❌ Cancel" or text == "🔙 Back":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_main_keyboard(user_id))
        return ConversationHandler.END
    cnic = ''.join(filter(str.isdigit, text))
    if len(cnic) != 13:
        await update.message.reply_text("❌ Invalid CNIC! Must be 13 digits.", reply_markup=get_cancel_keyboard())
        return ASKING_PAK_CNIC
    if context.user_data.get("use_coin", False):
        if not use_coin(user_id):
            await update.message.reply_text("❌ Not enough coins!", reply_markup=get_main_keyboard(user_id))
            return ConversationHandler.END
    await update.message.chat.send_action(action="typing")
    status_msg = await update.message.reply_text("⏳ Searching Pakistan CNIC...")
    result = await search_pak_cnic(cnic)
    await status_msg.delete()
    if "error" not in result:
        update_user_stats(user_id)
        save_search_result(user_id, "pak_cnic", cnic, result)
    formatted = format_pak_cnic(result, cnic)
    can, remaining, _ = can_search(user_id)
    user = get_user(user_id)
    info = f"\n\n👑 Unlimited" if has_unlimited_coins(user_id) else f"\n\n📊 Free left: {remaining}\n💰 Coins: {user['coins']}"
    
    full_text = formatted + info
    await send_long_message(update, full_text, disable_web_page_preview=True)
    await update.message.reply_text("✅ Search Complete", reply_markup=get_main_keyboard(user_id))
    return ConversationHandler.END


async def handle_pak_police(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await check_maintenance(update, context):
        return ConversationHandler.END
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if text == "❌ Cancel" or text == "🔙 Back":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_main_keyboard(user_id))
        return ConversationHandler.END
    number = ''.join(filter(str.isdigit, text))
    if context.user_data.get("use_coin", False):
        if not use_coin(user_id):
            await update.message.reply_text("❌ Not enough coins!", reply_markup=get_main_keyboard(user_id))
            return ConversationHandler.END
    await update.message.chat.send_action(action="typing")
    status_msg = await update.message.reply_text("⏳ Checking Police Records...")
    result = await search_pak_police(number)
    await status_msg.delete()
    if "error" not in result:
        update_user_stats(user_id)
        save_search_result(user_id, "pak_police", number, result)
    formatted = format_pak_police(result, number)
    can, remaining, _ = can_search(user_id)
    user = get_user(user_id)
    info = f"\n\n👑 Unlimited" if has_unlimited_coins(user_id) else f"\n\n📊 Free left: {remaining}\n💰 Coins: {user['coins']}"
    
    full_text = formatted + info
    await send_long_message(update, full_text, disable_web_page_preview=True)
    await update.message.reply_text("✅ Search Complete", reply_markup=get_main_keyboard(user_id))
    return ConversationHandler.END


async def handle_gst_billing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await check_maintenance(update, context):
        return ConversationHandler.END
    user_id = update.effective_user.id
    text = update.message.text.strip().upper()
    if text == "❌ Cancel" or text == "🔙 Back":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_main_keyboard(user_id))
        return ConversationHandler.END
    gstin = text
    if len(gstin) != 15:
        await update.message.reply_text("❌ Invalid GSTIN! Must be 15 characters.", reply_markup=get_cancel_keyboard())
        return ASKING_GST_BILLING
    if context.user_data.get("use_coin", False):
        if not use_coin(user_id):
            await update.message.reply_text("❌ Not enough coins!", reply_markup=get_main_keyboard(user_id))
            return ConversationHandler.END
    await update.message.chat.send_action(action="typing")
    status_msg = await update.message.reply_text("⏳ Fetching GST Billing...")
    result = await search_gst_billing(gstin)
    await status_msg.delete()
    if "error" not in result:
        update_user_stats(user_id)
        save_search_result(user_id, "gst_billing", gstin, result)
    formatted = format_gst_billing(result, gstin)
    can, remaining, _ = can_search(user_id)
    user = get_user(user_id)
    info = f"\n\n👑 Unlimited" if has_unlimited_coins(user_id) else f"\n\n📊 Free left: {remaining}\n💰 Coins: {user['coins']}"
    
    full_text = formatted + info
    await send_long_message(update, full_text, disable_web_page_preview=True)
    await update.message.reply_text("✅ Search Complete", reply_markup=get_main_keyboard(user_id))
    return ConversationHandler.END


async def handle_pan_gst(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await check_maintenance(update, context):
        return ConversationHandler.END
    user_id = update.effective_user.id
    text = update.message.text.strip().upper()
    if text == "❌ Cancel" or text == "🔙 Back":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_main_keyboard(user_id))
        return ConversationHandler.END
    pan = text
    if len(pan) != 10:
        await update.message.reply_text("❌ Invalid PAN! Must be 10 characters.", reply_markup=get_cancel_keyboard())
        return ASKING_PAN_GST
    if context.user_data.get("use_coin", False):
        if not use_coin(user_id):
            await update.message.reply_text("❌ Not enough coins!", reply_markup=get_main_keyboard(user_id))
            return ConversationHandler.END
    await update.message.chat.send_action(action="typing")
    status_msg = await update.message.reply_text("⏳ Searching PAN to GST...")
    result = await search_pan_gst(pan)
    await status_msg.delete()
    if "error" not in result:
        update_user_stats(user_id)
        save_search_result(user_id, "pan_gst", pan, result)
    formatted = format_pan_gst(result, pan)
    can, remaining, _ = can_search(user_id)
    user = get_user(user_id)
    info = f"\n\n👑 Unlimited" if has_unlimited_coins(user_id) else f"\n\n📊 Free left: {remaining}\n💰 Coins: {user['coins']}"
    
    full_text = formatted + info
    await send_long_message(update, full_text, disable_web_page_preview=True)
    await update.message.reply_text("✅ Search Complete", reply_markup=get_main_keyboard(user_id))
    return ConversationHandler.END


async def handle_aadhar_family(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await check_maintenance(update, context):
        return ConversationHandler.END
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if text == "❌ Cancel" or text == "🔙 Back":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_main_keyboard(user_id))
        return ConversationHandler.END
    aadhar = ''.join(filter(str.isdigit, text))
    if len(aadhar) != 12:
        await update.message.reply_text("❌ Invalid Aadhar! Must be 12 digits.", reply_markup=get_cancel_keyboard())
        return ASKING_AADHAR_FAMILY
    if context.user_data.get("use_coin", False):
        if not use_coin(user_id):
            await update.message.reply_text("❌ Not enough coins!", reply_markup=get_main_keyboard(user_id))
            return ConversationHandler.END
    await update.message.chat.send_action(action="typing")
    status_msg = await update.message.reply_text("⏳ Searching Family Details...")
    result = await search_aadhar_family(aadhar)
    await status_msg.delete()
    if "error" not in result:
        update_user_stats(user_id)
        save_search_result(user_id, "aadhar_family", aadhar, result)
    formatted = format_aadhar_family(result, aadhar)
    can, remaining, _ = can_search(user_id)
    user = get_user(user_id)
    info = f"\n\n👑 Unlimited" if has_unlimited_coins(user_id) else f"\n\n📊 Free left: {remaining}\n💰 Coins: {user['coins']}"
    
    full_text = formatted + info
    await send_long_message(update, full_text, disable_web_page_preview=True)
    await update.message.reply_text("✅ Search Complete", reply_markup=get_main_keyboard(user_id))
    return ConversationHandler.END


# ==================== SYSTEM INFO ====================
async def system_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_maintenance(update, context):
        return
    user_id = update.effective_user.id
    is_admin_user = is_admin(user_id)
    uptime = get_bot_uptime()
    speed = await get_network_speed()

    if is_admin_user:
        sys_info = get_system_info_for_admin()
        output = f"""\n🖥️ *{BOT_NAME} SYSTEM STATUS [ADMIN]*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🤖 *Bot Info:*\n• Name: {BOT_NAME}\n• Version: {BOT_VERSION}\n• Uptime: {uptime}\n• Status: {'🟢 ACTIVE' if settings.get('bot_active', True) else '🔴 INACTIVE'}\n• Daily Free: {'🟢 ON' if settings.get('daily_free_enabled', True) else '🔴 OFF'}\n\n🌐 *Network:*\n{speed['emoji']} Ping: {speed['ping_ms']} ms\n📊 Speed: {speed['status']}\n\n💻 *Server:*\n• OS: {sys_info['platform']} {sys_info['platform_release']}\n• Python: {sys_info['python_version']}\n• CPU: {sys_info['cpu_percent']}%\n• RAM: {sys_info['memory_used']}MB / {sys_info['memory_total']}MB ({sys_info['memory_percent']}%)\n• Disk: {sys_info['disk_used']}MB / {sys_info['disk_total']}MB ({sys_info['disk_percent']}%)\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👑 *Developer:* @{DEVELOPER_USERNAME}\n"""
    else:
        output = f"""\n🖥️ *{BOT_NAME} SYSTEM STATUS*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🤖 *Bot Info:*\n• Name: {BOT_NAME}\n• Version: {BOT_VERSION}\n• Uptime: {uptime}\n• Status: {'🟢 ACTIVE' if settings.get('bot_active', True) else '🔴 INACTIVE'}\n\n🌐 *Network:*\n{speed['emoji']} Ping: {speed['ping_ms']} ms\n📊 Speed: {speed['status']} ({speed['description']})\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👑 *Developer:* @{DEVELOPER_USERNAME}\n"""
    await update.message.reply_text(output, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


# ==================== REDEEM KEY ====================
async def redeem_key_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await check_maintenance(update, context):
        return ConversationHandler.END
    user_id = update.effective_user.id
    await update.message.reply_text("🎫 *Enter your redemption key:*\n\nExample: `KING_ABC123XYZ4567890`\n\n*Send key to redeem coins*", parse_mode=ParseMode.MARKDOWN, reply_markup=get_cancel_keyboard())
    return ASKING_REDEEM_KEY


async def handle_redeem_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    key = update.message.text.strip()
    if key == "❌ Cancel" or key == "🔙 Back":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_main_keyboard(user_id))
        return ConversationHandler.END
    success, message = redeem_key(user_id, key)
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_keyboard(user_id))
    return ConversationHandler.END


# ==================== GENERATE KEYS ====================
async def generate_keys_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admins can generate keys!")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "🔑 *KEY GENERATION HELP*\n\n"
            "*Format 1:* `/gen count credits`\n"
            "Example: `/gen 20 10`\n\n"
            "*Format 2:* `/gen type count credits`\n"
            "Example: `/gen KING 10 10`\n\n"
            "*How to use:* Users redeem via `/redeem <key>`\n\n"
            "👑 *Developer:* @KINGGKAI",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    try:
        if len(args) == 2:
            count = int(args[0])
            credits = int(args[1])
            key_type = "NORMAL"
        elif len(args) == 3:
            key_type = args[0].upper()
            count = int(args[1])
            credits = int(args[2])
        else:
            await update.message.reply_text("❌ Invalid format! Use: `/gen [type] count credits`", parse_mode=ParseMode.MARKDOWN)
            return

        if count <= 0 or count > 500:
            await update.message.reply_text("❌ Count must be between 1 and 500")
            return
        if credits <= 0 or credits > 100000:
            await update.message.reply_text("❌ Credits must be between 1 and 100000")
            return

        await update.message.reply_text(f"⏳ Generating {count} keys...")
        keys = generate_keys(key_type, count, credits)

        if not keys:
            await update.message.reply_text("❌ Failed to generate keys! Check database connection.", reply_markup=get_admin_keyboard())
            return

        keys_text = "\n".join([f"`{k}`" for k in keys[:20]])
        output = f"🔑 *KEYS GENERATED!*\n\n📋 Type: `{key_type}`\n🔢 Count: {len(keys)}\n💰 Credits: {credits}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{keys_text}"

        if len(keys) > 20:
            output += f"\n\n_... and {len(keys) - 20} more keys_"

        output += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n📝 Use: /redeem <key>\n👑 Developer: @{DEVELOPER_USERNAME}"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 BROADCAST KEYS", callback_data=f"broadcast_keys_{key_type}_{count}_{credits}")],
            [InlineKeyboardButton("❌ CLOSE", callback_data="close")]
        ])

        if len(output) > 4000:
            file_path = format_result_as_file(output, "keys.txt")
            with open(file_path, 'rb') as f:
                await update.message.reply_document(
                    document=f, 
                    filename="generated_keys.txt", 
                    caption=f"🔑 {len(keys)} keys generated",
                    reply_markup=keyboard
                )
            os.unlink(file_path)
        else:
            await update.message.reply_text(
                output, 
                parse_mode=ParseMode.MARKDOWN, 
                disable_web_page_preview=True, 
                reply_markup=keyboard
            )

    except ValueError:
        await update.message.reply_text("❌ Invalid numbers! Use: `/gen 20 10`", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error in generate_keys_command: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}", reply_markup=get_admin_keyboard())


# ==================== REVOKE KEYS ====================
async def revoke_keys_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admins can revoke keys!")
        return
    await update.message.reply_text("🗑️ *Revoke Keys Menu*\n\n• Revoke Single Key\n• Revoke All Unused\n• Revoke By Type", parse_mode=ParseMode.MARKDOWN, reply_markup=get_revoke_keys_keyboard())


async def revoke_single_key_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await update.message.reply_text("🗑️ *Enter the key to revoke:*\nExample: `KING_ABC123XYZ4567890`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_cancel_keyboard())
    return ASKING_REVOKE_KEY


async def revoke_single_key_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    key = update.message.text.strip().upper()
    if key == "❌ Cancel":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_admin_keyboard())
        return ConversationHandler.END
    success, message = revoke_key(key)
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())
    return ConversationHandler.END


async def revoke_all_unused(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admins can revoke keys!")
        return
    await update.message.reply_text("⏳ Revoking all unused keys...")
    success, message = revoke_all_unused_keys("all")
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())


async def revoke_by_type_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    all_keys = mongo.get_all_keys()
    key_types = set()
    for key in all_keys:
        if not key.get("is_used", False):
            key_types.add(key.get("key_type", "NORMAL"))
    if not key_types:
        await update.message.reply_text("📋 No unused keys found!", reply_markup=get_admin_keyboard())
        return ConversationHandler.END
    keyboard = []
    for kt in key_types:
        keyboard.append([KeyboardButton(f"🗑️ Revoke {kt}")])
    keyboard.append([KeyboardButton("🔙 Back")])
    await update.message.reply_text("🗑️ *Select key type:*", parse_mode=ParseMode.MARKDOWN, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return ASKING_REVOKE_KEY_ID


async def revoke_by_type_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text == "🔙 Back":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_admin_keyboard())
        return ConversationHandler.END
    if text.startswith("🗑️ Revoke "):
        key_type = text.replace("🗑️ Revoke ", "").upper()
        await update.message.reply_text(f"⏳ Revoking all unused keys of type '{key_type}'...")
        success, message = revoke_all_unused_keys(key_type)
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())
    return ConversationHandler.END


async def show_unused_keys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admins can view unused keys!")
        return
    unused_keys = get_unused_keys()
    if not unused_keys:
        await update.message.reply_text("📋 No unused keys found!", reply_markup=get_admin_keyboard())
        return
    by_type = {}
    for key in unused_keys:
        ktype = key.get("key_type", "NORMAL")
        if ktype not in by_type:
            by_type[ktype] = []
        by_type[ktype].append(key["key"])
    output = f"📋 *UNUSED KEYS*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\nTotal: {len(unused_keys)}\n\n"
    for ktype, keys in by_type.items():
        output += f"*{ktype}* ({len(keys)}):\n"
        for k in keys[:10]:
            output += f"`{k}`\n"
        if len(keys) > 10:
            output += f"_... and {len(keys) - 10} more_\n"
        output += "\n"
    await send_long_message(update, output)
    await update.message.reply_text("✅ Done", reply_markup=get_admin_keyboard())


# ==================== BLOCK USER ====================
async def block_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await update.message.reply_text("🚷 *Enter user ID or @username to block:*\nExample: `123456789 Spamming`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_cancel_keyboard())
    return ASKING_BLOCK_USER


async def block_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    text = update.message.text.strip()
    if text == "❌ Cancel":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_admin_keyboard())
        return ConversationHandler.END
    parts = text.split(" ", 1)
    identifier = parts[0]
    reason = parts[1] if len(parts) > 1 else "Blocked by admin"
    user_id = find_user_by_identifier(identifier)
    if user_id:
        if user_id in OWNER_IDS:
            await update.message.reply_text("❌ Cannot block the owner!", reply_markup=get_admin_keyboard())
        else:
            block_user(user_id, reason, update.effective_user.id)
            user = get_user(user_id)
            username = user.get("username", "No username")
            try:
                await context.bot.send_message(user_id, f"🚷 *You have been blocked!*\n\n📋 Reason: {reason}\nContact @{SUPPORT_USERNAME}", parse_mode=ParseMode.MARKDOWN)
            except:
                pass
            await update.message.reply_text(f"✅ *User blocked:* `{user_id}` (@{username})\n📋 Reason: {reason}", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())
    else:
        await update.message.reply_text(f"❌ User not found: `{identifier}`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())
    return ConversationHandler.END


async def unblock_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await update.message.reply_text("✅ *Enter user ID or @username to unblock:*\nExample: `123456789`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_cancel_keyboard())
    return ASKING_UNBLOCK_NUMBER


async def unblock_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    text = update.message.text.strip()
    if text == "❌ Cancel":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_admin_keyboard())
        return ConversationHandler.END
    user_id = find_user_by_identifier(text)
    if user_id:
        user = get_user(user_id)
        if user.get("is_blocked", False):
            unblock_user(user_id)
            username = user.get("username", "No username")
            try:
                await context.bot.send_message(user_id, f"✅ *You have been unblocked!*\n\nYou can now use the bot again.", parse_mode=ParseMode.MARKDOWN)
            except:
                pass
            await update.message.reply_text(f"✅ *User unblocked:* `{user_id}` (@{username})", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())
        else:
            await update.message.reply_text(f"ℹ️ User `{user_id}` is not blocked.", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())
    else:
        await update.message.reply_text(f"❌ User not found: `{text}`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())
    return ConversationHandler.END


async def show_blocked_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    all_users = mongo.get_all_users()
    blocked_users = [u for u in all_users if u.get("is_blocked", False)]
    if not blocked_users:
        await update.message.reply_text("📋 *No blocked users*", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())
        return
    output = "🚷 *BLOCKED USERS*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for user in blocked_users[:30]:
        username = user.get("username", "No username")
        reason = user.get("blocked_reason", "No reason")
        blocked_at = user.get("blocked_at", "Unknown")
        output += f"• `{user['user_id']}` - @{username}\n  📋 {reason}\n  📅 {blocked_at[:10]}\n\n"
    if len(blocked_users) > 30:
        output += f"\n_... and {len(blocked_users) - 30} more_"
    await send_long_message(update, output)
    await update.message.reply_text("✅ Done", reply_markup=get_admin_keyboard())


# ==================== MAINTENANCE MODE COMMANDS ====================
async def maintenance_mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admins can change maintenance mode!")
        return
    args = context.args
    if not args:
        current = "🔴 ENABLED" if MAINTENANCE_MODE else "🟢 DISABLED"
        await update.message.reply_text(f"🔧 *Maintenance Mode*\nStatus: {current}\n\nCommands:\n/maintenance on\n/maintenance off\n/maintenance msg <message>", parse_mode=ParseMode.MARKDOWN)
        return
    action = args[0].lower()
    if action == "on":
        set_maintenance_mode(True)
        await update.message.reply_text("🔧 *Maintenance Mode ENABLED*", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())
    elif action == "off":
        set_maintenance_mode(False)
        await update.message.reply_text("✅ *Maintenance Mode DISABLED*", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())
    elif action == "msg" and len(args) > 1:
        message = " ".join(args[1:])
        set_maintenance_mode(MAINTENANCE_MODE, message)
        await update.message.reply_text("✅ *Maintenance message updated!*", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())
    else:
        await update.message.reply_text("❌ Invalid command!", parse_mode=ParseMode.MARKDOWN)


# ==================== COMMAND HANDLERS ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_maintenance(update, context):
        return
    user = update.effective_user
    args = context.args
    if args and args[0].startswith("ref_"):
        process_referral(user.id, args[0][4:])
    user_data = get_user(user.id)
    if user.username:
        user_data["username"] = user.username
        mongo.save_user(user_data)

    if user_data.get("total_searches", 0) == 0 and not user_data.get("alert_sent", False):
        await send_new_user_alert_async(context.bot, user.id, user.username)

    if not is_admin(user.id):
        if not await check_group_approval(update, context):
            return
        if not await check_mandatory_channel(update, context):
            return

    welcome = f"👋 *Welcome {escape_text(user.first_name)}!*\n\n🔍 *{BOT_NAME} v{BOT_VERSION}*\n\n✅ *Services:*\n• 🇮🇳 Indian Number & Aadhar\n• 🇵🇰 Pakistan Number, CNIC, Police\n• 💰 GST Billing & PAN to GST\n• 👨‍👩‍👧 Aadhar Family\n• 📱 TG Info (Username/ID)\n\n💰 *Free {settings['daily_limit']} searches/day*\n• Referral: +{settings['referral_coins']} coins\n\n👑 *Developer:* @{DEVELOPER_USERNAME}"
    await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_keyboard(user.id))


async def num_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_maintenance(update, context):
        return
    if not settings.get("bot_active", True) and not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Bot is disabled!", reply_markup=get_main_keyboard(update.effective_user.id))
        return
    if not context.args:
        await update.message.reply_text("❌ Usage: `/num 9876543210`", parse_mode=ParseMode.MARKDOWN)
        return
    user_id = update.effective_user.id

    if not is_admin(user_id):
        if not await check_group_approval(update, context):
            return
        if not await check_mandatory_channel(update, context):
            return

    can, _, use_coin_flag = can_search(user_id)
    if not can:
        await update.message.reply_text("❌ Daily limit reached!", parse_mode=ParseMode.MARKDOWN)
        return
    if use_coin_flag:
        use_coin(user_id)
    number = context.args[0]
    await update.message.chat.send_action(action="typing")
    result = await search_indian_number(number)
    if "error" not in result:
        update_user_stats(user_id)
        save_search_result(user_id, "indian_number", number, result)
    formatted = format_indian_number(result, number)
    await send_long_message(update, formatted, disable_web_page_preview=True)


async def aadhar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_maintenance(update, context):
        return
    if not settings.get("bot_active", True) and not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Bot is disabled!", reply_markup=get_main_keyboard(update.effective_user.id))
        return
    if not context.args:
        await update.message.reply_text("❌ Usage: `/aadhar 123456789012`", parse_mode=ParseMode.MARKDOWN)
        return
    user_id = update.effective_user.id

    if not is_admin(user_id):
        if not await check_group_approval(update, context):
            return
        if not await check_mandatory_channel(update, context):
            return

    can, _, use_coin_flag = can_search(user_id)
    if not can:
        await update.message.reply_text("❌ Daily limit reached!", parse_mode=ParseMode.MARKDOWN)
        return
    if use_coin_flag:
        use_coin(user_id)

    aadhar = context.args[0]
    await update.message.chat.send_action(action="typing")
    result = await search_indian_aadhar(aadhar)
    if "error" not in result:
        update_user_stats(user_id)
        save_search_result(user_id, "indian_aadhar", aadhar, result)
    formatted = format_indian_aadhar(result, aadhar)
    await send_long_message(update, formatted, disable_web_page_preview=True)


async def my_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_maintenance(update, context):
        return
    user = get_user(update.effective_user.id)
    if has_unlimited_coins(update.effective_user.id):
        text = "👑 *ADMIN*\n💰 Coins: UNLIMITED ✅"
    else:
        text = f"💰 *YOUR BALANCE*\n💎 Coins: {user['coins']}\n\n_Share referral link to earn {settings['referral_coins']} coins!_"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def referral_link_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_maintenance(update, context):
        return
    user = get_user(update.effective_user.id)
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=ref_{user['referral_code']}"
    text = f"🔗 *YOUR REFERRAL LINK*\n`{link}`\n\n💰 Earn {settings['referral_coins']} coins per referral!"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_maintenance(update, context):
        return
    user = get_user(update.effective_user.id)
    today = date.today().isoformat()
    daily = 0 if user["last_search_date"] != today else user["daily_searches"]
    remaining = settings["daily_limit"] - daily
    history = mongo.get_search_history(update.effective_user.id, 1000)
    usage_percent = (daily / settings["daily_limit"]) * 100 if settings["daily_limit"] > 0 else 0
    bar_length = 10
    filled = int(bar_length * usage_percent / 100)
    bar = "█" * filled + "░" * (bar_length - filled)

    text = f"""\n📊 *YOUR STATISTICS*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n👤 *Profile*\n• Username: @{user.get('username', 'Unknown')}\n• ID: `{user['user_id']}`\n• Joined: {user['joined_date'][:10]}\n\n💰 *Wallet*\n• Coins: `{user['coins']}`\n\n🔍 *Search Activity*\n• Total Searches: `{user['total_searches']}`\n• Today: `{daily}/{settings['daily_limit']}`\n• Progress: `[{bar}] {usage_percent:.0f}%`\n• Remaining Free: `{remaining}`\n\n👥 *Referrals*\n• Total Referrals: `{len(user.get('referrals', []))}`\n• Earn per Referral: `{settings['referral_coins']}` coins\n\n📜 *History*\n• Total Records: `{len(history)}`\n\n💡 _Share referral link to earn more coins!_\n👑 *Developer:* @{DEVELOPER_USERNAME}\n"""
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def buy_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_maintenance(update, context):
        return
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 50 Coins - ₹30", callback_data="buy_50")],
        [InlineKeyboardButton("💰 100 Coins - ₹50", callback_data="buy_100")],
        [InlineKeyboardButton("💰 250 Coins - ₹120", callback_data="buy_250")],
        [InlineKeyboardButton("💰 500 Coins - ₹200", callback_data="buy_500")],
        [InlineKeyboardButton("❌ Close", callback_data="close")]
    ])
    text = f"💎 *BUY COINS*\n\n*UPI:* `{UPI_ID}`\n*Contact:* @{SUPPORT_USERNAME}"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"""\n❓ *HELP MENU*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n*Commands:*\n/num <number> - Indian Number\n/aadhar <aadhar> - Indian Aadhar\n/stats - Your statistics\n/coins - Check coins\n/referral - Referral link\n/redeem - Redeem key\n/system - System info\n/history - Search history\n/id - Get your IDs\n\n*Support:* @{SUPPORT_USERNAME}\n👑 *Developer:* @{DEVELOPER_USERNAME}\n"""
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def search_history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_maintenance(update, context):
        return
    user_id = update.effective_user.id
    history = mongo.get_search_history(user_id, 50)
    if not history:
        await update.message.reply_text("📋 *No search history found*", parse_mode=ParseMode.MARKDOWN)
        return

    today_count = 0
    week_count = 0
    month_count = 0

    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    output = "📋 *YOUR SEARCH HISTORY*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    for h in history[:20]:
        ts = h.get("timestamp", datetime.now())
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts)
            except:
                ts = datetime.now()

        timestamp = ts.strftime("%Y-%m-%d %H:%M")
        search_type = h.get('search_type', 'Unknown')
        query = h.get('query', '?')

        if ts.date() == today:
            today_count += 1
        if ts.date() >= week_ago:
            week_count += 1
        if ts.date() >= month_ago:
            month_count += 1

        output += f"• *{search_type}*\n  🔍 `{query}`\n  📅 {timestamp}\n\n"

    output += f"""\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📊 *SUMMARY*\n• Today: `{today_count}` searches\n• This Week: `{week_count}` searches  \n• This Month: `{month_count}` searches\n• Total Shown: `{len(history[:20])}`\n"""

    if len(history) > 20:
        output += f"\n_... and {len(history) - 20} more records_"

    await send_long_message(update, output)


# ==================== KEYBOARDS ====================
def get_main_keyboard(user_id: int = None) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("🔍 Indian Number"), KeyboardButton("🆔 Indian Aadhar")],
        [KeyboardButton("🇵🇰 Pak Number"), KeyboardButton("🪪 Pak CNIC")],
        [KeyboardButton("🚔 Pak Police"), KeyboardButton("👨‍👩‍👧 Aadhar Family")],
        [KeyboardButton("💰 GST Billing"), KeyboardButton("📇 PAN to GST")],
        [KeyboardButton("📱 TG Info"), KeyboardButton("💎 My Coins")],
        [KeyboardButton("🔗 Referral"), KeyboardButton("📊 Stats")],
        [KeyboardButton("🎫 Redeem Key"), KeyboardButton("🖥️ System Info")],
        [KeyboardButton("❓ Help"), KeyboardButton("📜 History")],
        [KeyboardButton("💰 Buy Coins")],
    ]
    if user_id and is_admin(user_id):
        keyboard.append([KeyboardButton("⚙️ Admin Panel")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("📊 Bot Status"), KeyboardButton("👥 All Users")],
        [KeyboardButton("📊 All Users Stats"), KeyboardButton("🔛 Toggle Bot")],
        [KeyboardButton("🔧 Maintenance"), KeyboardButton("📢 Broadcast")],
        [KeyboardButton("💰 Set Referral Coins"), KeyboardButton("🚫 Block Number")],
        [KeyboardButton("✅ Unblock Number"), KeyboardButton("🚷 Block User")],
        [KeyboardButton("✅ Unblock User"), KeyboardButton("👑 Add Admin")],
        [KeyboardButton("👑 Remove Admin"), KeyboardButton("📋 Admin List")],
        [KeyboardButton("📋 Blocked List"), KeyboardButton("💎 Add Coins")],
        [KeyboardButton("📊 Set Daily Limit"), KeyboardButton("⚙️ API Settings")],
        [KeyboardButton("🔑 Generate Keys"), KeyboardButton("📋 Key Stats")],
        [KeyboardButton("🗑️ Revoke Keys"), KeyboardButton("📋 Unused Keys")],
        [KeyboardButton("📢 Channel Settings"), KeyboardButton("💰 Reset All Credits")],
        [KeyboardButton("🔍 Detect Coins"), KeyboardButton("🔄 Toggle Daily Free")],
        [KeyboardButton("📋 Pending Approvals"), KeyboardButton("✅ Approved Groups")],
        [KeyboardButton("🔙 Exit Admin")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_revoke_keys_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("🗑️ Revoke Single Key")],
        [KeyboardButton("🗑️ Revoke All Unused")],
        [KeyboardButton("🗑️ Revoke By Type")],
        [KeyboardButton("🔙 Back to Admin")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_api_settings_keyboard() -> ReplyKeyboardMarkup:
    keyboard = []
    row = []
    for key, service in API_SERVICES.items():
        status = "🟢" if is_api_enabled(key) else "🔴"
        button_text = f"{status} {service['name']}"
        row.append(KeyboardButton(button_text))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([KeyboardButton("📝 Update API URL"), KeyboardButton("📊 API Status")])
    keyboard.append([KeyboardButton("🔙 Back to Admin")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_api_select_keyboard() -> ReplyKeyboardMarkup:
    keyboard = []
    for key, service in API_SERVICES.items():
        keyboard.append([KeyboardButton(f"📝 Update {service['name']}")])
    keyboard.append([KeyboardButton("🔙 Back")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([[KeyboardButton("❌ Cancel")]], resize_keyboard=True)


def get_back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([[KeyboardButton("🔙 Back")]], resize_keyboard=True)


# ==================== API SETTINGS ====================
async def api_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("⚙️ *API Settings*\n🟢 = Enabled, 🔴 = Disabled\nTap to toggle:", parse_mode=ParseMode.MARKDOWN, reply_markup=get_api_settings_keyboard())


async def api_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    text = "📊 *API STATUS*\n\n"
    for key, service in API_SERVICES.items():
        status = "🟢 ENABLED" if is_api_enabled(key) else "🔴 DISABLED"
        text += f"{service['emoji']} *{service['name']}:* {status}\n"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_api_settings_keyboard())


async def toggle_api_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    text = update.message.text
    clean_text = text
    if clean_text.startswith("🟢") or clean_text.startswith("🔴"):
        clean_text = clean_text[2:].strip()
    for key, service in API_SERVICES.items():
        if service['name'] in clean_text:
            new_status = toggle_api(key)
            status = "ENABLED 🟢" if new_status else "DISABLED 🔴"
            await update.message.reply_text(f"✅ {service['name']} is now {status}", reply_markup=get_api_settings_keyboard())
            return


async def update_api_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await update.message.reply_text("📝 *Select API to Update:*", parse_mode=ParseMode.MARKDOWN, reply_markup=get_api_select_keyboard())
    return ASKING_API_SELECT


async def update_api_url_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    text = update.message.text
    if text == "🔙 Back":
        await update.message.reply_text("⚙️ *API Settings*", parse_mode=ParseMode.MARKDOWN, reply_markup=get_api_settings_keyboard())
        return ConversationHandler.END
    for key, service in API_SERVICES.items():
        if service['name'] in text:
            context.user_data["updating_api"] = key
            current_url = get_api_url(key)
            await update.message.reply_text(f"📝 *Update {service['name']}*\n\nCurrent: `{current_url}`\n\nSend new URL:", parse_mode=ParseMode.MARKDOWN, reply_markup=get_cancel_keyboard())
            return ASKING_API_UPDATE
    return ConversationHandler.END


async def update_api_url_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    text = update.message.text.strip()
    if text == "❌ Cancel":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_api_settings_keyboard())
        return ConversationHandler.END
    if not text.startswith("http"):
        await update.message.reply_text("❌ Invalid URL! Must start with http:// or https://", reply_markup=get_cancel_keyboard())
        return ASKING_API_UPDATE
    key = context.user_data.get("updating_api")
    if key:
        if update_api_url(key, text):
            await update.message.reply_text(f"✅ API Updated Successfully!\n`{text[:50]}...`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_api_settings_keyboard())
        else:
            await update.message.reply_text("❌ Failed to update API.", reply_markup=get_api_settings_keyboard())
    context.user_data.pop("updating_api", None)
    return ConversationHandler.END


async def back_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("⚙️ *Admin Panel*", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())


# ==================== ADMIN COMMANDS ====================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("⚙️ *Admin Panel*", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())


async def bot_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    stats = mongo.get_stats()
    uptime = get_bot_uptime()
    sys_info = get_system_info_for_admin()
    text = f"""\n📊 *BOT STATUS*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🤖 *Bot:* {BOT_NAME} v{BOT_VERSION}\n⏱️ Uptime: {uptime}\n📊 Status: {'🟢 ACTIVE' if settings['bot_active'] else '🔴 INACTIVE'}\n🔧 Maintenance: {'🔴 ON' if MAINTENANCE_MODE else '🟢 OFF'}\n📢 Mandatory Channel: {'🟢 ON' if is_mandatory_channel_enabled() else '🔴 OFF'}\n💰 Daily Free: {'🟢 ON' if settings.get('daily_free_enabled', True) else '🔴 OFF'}\n\n👥 Users: {stats['total_users']}\n🚷 Blocked: {len([u for u in mongo.get_all_users() if u.get('is_blocked', False)])}\n\n🔍 Searches: {stats['total_searches']}\n📊 Daily Limit: {settings['daily_limit']}\n\n🔑 Keys: {stats['total_keys']} total, {stats['used_keys']} used, {stats['total_keys'] - stats['used_keys']} unused\n\n✅ Approved Groups: {len(APPROVED_GROUPS)}\n⏳ Pending Approvals: {len(PENDING_APPROVALS)}\n\n💻 System: CPU {sys_info['cpu_percent']}% | RAM {sys_info['memory_percent']}% | Disk {sys_info['disk_percent']}%\n\n👑 Developer: @{DEVELOPER_USERNAME}\n"""
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())


async def toggle_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    settings["bot_active"] = not settings["bot_active"]
    mongo.save_setting("bot_active", settings["bot_active"])
    status = "ACTIVE 🟢" if settings["bot_active"] else "INACTIVE 🔴"
    await update.message.reply_text(f"✅ Bot is now {status}", reply_markup=get_admin_keyboard())


async def maintenance_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    current_status = "🔴 ENABLED" if MAINTENANCE_MODE else "🟢 DISABLED"
    keyboard = [
        [KeyboardButton("🔧 Enable"), KeyboardButton("✅ Disable")],
        [KeyboardButton("📝 Set Message")],
        [KeyboardButton("🔙 Back")]
    ]
    await update.message.reply_text(
        f"🔧 *Maintenance Mode*\nStatus: {current_status}\n\n📝 *Message:*\n{MAINTENANCE_MESSAGE}\n\nUse buttons below to manage:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


async def handle_maintenance_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    text = update.message.text
    if text == "🔧 Enable":
        set_maintenance_mode(True)
        await update.message.reply_text("🔧 Maintenance Mode ENABLED", reply_markup=get_admin_keyboard())
    elif text == "✅ Disable":
        set_maintenance_mode(False)
        await update.message.reply_text("✅ Maintenance Mode DISABLED", reply_markup=get_admin_keyboard())
    elif text == "📝 Set Message":
        return await set_maintenance_message_start(update, context)
    elif text == "🔙 Back":
        await update.message.reply_text("⚙️ Admin Panel", reply_markup=get_admin_keyboard())
    return ConversationHandler.END


async def set_daily_limit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(f"📊 *Set Daily Search Limit*\nCurrent: {settings['daily_limit']}\n\nEnter new limit:", parse_mode=ParseMode.MARKDOWN, reply_markup=get_cancel_keyboard())
    return ASKING_SET_DAILY_LIMIT


async def set_daily_limit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    text = update.message.text.strip()
    if text == "❌ Cancel":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_admin_keyboard())
        return ConversationHandler.END
    try:
        limit = int(text)
        if limit < 1:
            raise ValueError
        settings["daily_limit"] = limit
        mongo.save_setting("daily_limit", limit)
        await update.message.reply_text(f"✅ Daily limit set to {limit}", reply_markup=get_admin_keyboard())
    except:
        await update.message.reply_text("❌ Invalid limit!", reply_markup=get_cancel_keyboard())
        return ASKING_SET_DAILY_LIMIT
    return ConversationHandler.END


async def blocked_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    blocked = mongo.get_all_blocked_numbers()
    if not blocked:
        await update.message.reply_text("📋 No blocked numbers", reply_markup=get_admin_keyboard())
        return
    text = "🚫 *BLOCKED NUMBERS*\n\n"
    for num_data in blocked[:30]:
        num = num_data.get('number')
        reason = num_data.get('reason', 'No reason')
        by = num_data.get('blocked_by', 'Unknown')
        text += f"📱 `{num}`\n   Reason: {reason}\n   Blocked by: {by}\n\n"
    if len(blocked) > 30:
        text += f"\n_... and {len(blocked) - 30} more_"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())


async def admin_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    admins = list(OWNER_IDS)
    all_users = mongo.get_all_users()
    for user in all_users:
        if user.get("is_admin", False) and user['user_id'] not in admins:
            admins.append(user['user_id'])
    text = "👑 *ADMIN LIST*\n\n"
    for uid in admins:
        user = get_user(uid)
        username = user.get("username", "No username")
        role = "OWNER" if uid in OWNER_IDS else "ADMIN"
        text += f"• `{uid}` - @{username} ({role})\n"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())


# ==================== BROADCAST WITH LIVE PROGRESS ====================
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    
    global BROADCAST_ACTIVE, BROADCAST_STOP, BROADCAST_STATS
    if BROADCAST_ACTIVE:
        await update.message.reply_text("⚠️ A broadcast is already running!")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "📢 *Send your broadcast message:*\n\n"
        "✅ Supports:\n"
        "• Text (sent as copy)\n"
        "• Forwarded messages (sent as copy)\n"
        "• Photos, Videos, Documents, Audio\n"
        "• Polls, Quizzes\n"
        "• APK files\n\n"
        "📊 Live progress will be shown.\n"
        "⏹️ You can stop anytime with STOP button.\n\n"
        "Send /cancel to cancel.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_cancel_keyboard()
    )
    return ASKING_BROADCAST


async def broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    
    global BROADCAST_ACTIVE, BROADCAST_STOP, BROADCAST_STATS, BROADCAST_MSG_ID, BROADCAST_CHAT_ID
    
    BROADCAST_ACTIVE = True
    BROADCAST_STOP = False
    BROADCAST_STATS = {"sent": 0, "failed": 0, "blocked": 0, "total": 0}
    BROADCAST_CHAT_ID = update.effective_chat.id
    
    # Send initial progress message
    progress_msg = await update.message.reply_text(
        "📢 *BROADCAST STARTED*\n\n"
        "📨 Sent: 0\n"
        "❌ Failed: 0\n"
        "🚷 Blocked: 0\n"
        "📊 Total: 0\n\n"
        "⏳ Processing...\n\n"
        "⏹️ /stop_broadcast to stop",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏹️ STOP", callback_data="stop_broadcast")],
            [InlineKeyboardButton("📊 Live Stats", callback_data="broadcast_stats")]
        ])
    )
    BROADCAST_MSG_ID = progress_msg.message_id
    
    all_users = mongo.get_all_users()
    total_users = len(all_users)
    BROADCAST_STATS["total"] = total_users
    
    # Update progress
    await progress_msg.edit_text(
        f"📢 *BROADCAST STARTED*\n\n"
        f"📨 Sent: 0\n"
        f"❌ Failed: 0\n"
        f"🚷 Blocked: 0\n"
        f"📊 Total: {total_users}\n\n"
        f"⏳ Progress: 0% (0/{total_users})\n\n"
        f"⏹️ /stop_broadcast to stop",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏹️ STOP", callback_data="stop_broadcast")],
            [InlineKeyboardButton("📊 Live Stats", callback_data="broadcast_stats")]
        ])
    )
    
    # Process users in background
    await asyncio.create_task(process_broadcast(update, context))
    
    return ConversationHandler.END


async def process_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process broadcast in background"""
    global BROADCAST_ACTIVE, BROADCAST_STOP, BROADCAST_STATS, BROADCAST_MSG_ID, BROADCAST_CHAT_ID
    
    all_users = mongo.get_all_users()
    total_users = len(all_users)
    
    # Store message details for sending
    msg_text = update.message.text
    msg_caption = update.message.caption
    
    # Get media info
    photo = update.message.photo[-1] if update.message.photo else None
    document = update.message.document
    video = update.message.video
    audio = update.message.audio
    voice = update.message.voice
    video_note = update.message.video_note
    animation = update.message.animation
    sticker = update.message.sticker
    poll = update.message.poll
    is_forward = update.message.forward_from or update.message.forward_from_chat
    
    # Get chat_id and message_id for copy
    chat_id = update.effective_chat.id
    message_id = update.message.message_id
    
    for idx, user in enumerate(all_users):
        if BROADCAST_STOP:
            break
            
        uid = user['user_id']
        try:
            if user.get("is_blocked", False):
                BROADCAST_STATS["blocked"] += 1
                continue
            
            # Send message based on type
            if msg_text and not photo and not document and not video and not audio and not voice and not video_note and not animation and not sticker and not poll:
                await context.bot.send_message(
                    chat_id=uid,
                    text=msg_text,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True
                )
            elif photo:
                await context.bot.send_photo(
                    chat_id=uid,
                    photo=photo.file_id,
                    caption=msg_caption,
                    parse_mode=ParseMode.MARKDOWN
                )
            elif document:
                await context.bot.send_document(
                    chat_id=uid,
                    document=document.file_id,
                    caption=msg_caption,
                    parse_mode=ParseMode.MARKDOWN
                )
            elif video:
                await context.bot.send_video(
                    chat_id=uid,
                    video=video.file_id,
                    caption=msg_caption,
                    parse_mode=ParseMode.MARKDOWN
                )
            elif audio:
                await context.bot.send_audio(
                    chat_id=uid,
                    audio=audio.file_id,
                    caption=msg_caption,
                    parse_mode=ParseMode.MARKDOWN
                )
            elif voice:
                await context.bot.send_voice(
                    chat_id=uid,
                    voice=voice.file_id,
                    caption=msg_caption,
                    parse_mode=ParseMode.MARKDOWN
                )
            elif video_note:
                await context.bot.send_video_note(
                    chat_id=uid,
                    video_note=video_note.file_id
                )
            elif animation:
                await context.bot.send_animation(
                    chat_id=uid,
                    animation=animation.file_id,
                    caption=msg_caption,
                    parse_mode=ParseMode.MARKDOWN
                )
            elif sticker:
                await context.bot.send_sticker(
                    chat_id=uid,
                    sticker=sticker.file_id
                )
            elif poll:
                await context.bot.send_poll(
                    chat_id=uid,
                    question=poll.question,
                    options=[option.text for option in poll.options],
                    is_anonymous=poll.is_anonymous,
                    type=poll.type,
                    allows_multiple_answers=poll.allows_multiple_answers
                )
            elif is_forward:
                # Handle forwarded messages - send as copy
                await context.bot.copy_message(
                    chat_id=uid,
                    from_chat_id=chat_id,
                    message_id=message_id
                )
            else:
                # Fallback
                await context.bot.send_message(
                    chat_id=uid,
                    text="📢 Broadcast message from admin",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            BROADCAST_STATS["sent"] += 1
            
        except Exception as e:
            BROADCAST_STATS["failed"] += 1
            logger.error(f"Failed to send broadcast to {uid}: {e}")
        
        # Update progress every 5 messages
        if idx % 5 == 0:
            try:
                progress = int((idx + 1) / total_users * 100)
                await context.bot.edit_message_text(
                    chat_id=BROADCAST_CHAT_ID,
                    message_id=BROADCAST_MSG_ID,
                    text=f"📢 *BROADCAST IN PROGRESS*\n\n"
                         f"📨 Sent: {BROADCAST_STATS['sent']}\n"
                         f"❌ Failed: {BROADCAST_STATS['failed']}\n"
                         f"🚷 Blocked: {BROADCAST_STATS['blocked']}\n"
                         f"📊 Total: {total_users}\n\n"
                         f"⏳ Progress: {progress}% ({idx+1}/{total_users})\n"
                         f"📌 {'⏹️ STOPPING...' if BROADCAST_STOP else '🔄 Running...'}\n\n"
                         f"⏹️ /stop_broadcast to stop",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⏹️ STOP", callback_data="stop_broadcast")],
                        [InlineKeyboardButton("📊 Live Stats", callback_data="broadcast_stats")]
                    ])
                )
            except Exception as e:
                logger.error(f"Error updating progress: {e}")
        
        await asyncio.sleep(0.03)  # Rate limit
    
    # Broadcast complete
    BROADCAST_ACTIVE = False
    
    if BROADCAST_STOP:
        status = "⏹️ STOPPED"
    else:
        status = "✅ COMPLETED"
    
    try:
        await context.bot.edit_message_text(
            chat_id=BROADCAST_CHAT_ID,
            message_id=BROADCAST_MSG_ID,
            text=f"📢 *BROADCAST {status}*\n\n"
                 f"📨 Sent: {BROADCAST_STATS['sent']}\n"
                 f"❌ Failed: {BROADCAST_STATS['failed']}\n"
                 f"🚷 Blocked: {BROADCAST_STATS['blocked']}\n"
                 f"📊 Total: {total_users}\n"
                 f"📌 Status: {status}\n\n"
                 f"👑 *Developer:* @{DEVELOPER_USERNAME}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="close")]
            ])
        )
    except:
        pass
    
    logger.info(f"📢 Broadcast {status}: Sent {BROADCAST_STATS['sent']}, Failed {BROADCAST_STATS['failed']}, Blocked {BROADCAST_STATS['blocked']}, Total {total_users}")


async def stop_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop ongoing broadcast"""
    global BROADCAST_STOP
    
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admins can stop broadcast!")
        return
    
    if not BROADCAST_ACTIVE:
        await update.message.reply_text("ℹ️ No broadcast is running.")
        return
    
    BROADCAST_STOP = True
    await update.message.reply_text("⏹️ *Stopping broadcast...*", parse_mode=ParseMode.MARKDOWN)


async def broadcast_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show live broadcast stats"""
    query = update.callback_query
    await query.answer()
    
    if not BROADCAST_ACTIVE:
        await query.edit_message_text("ℹ️ No broadcast is running.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="close")]]))
        return
    
    total = BROADCAST_STATS["total"]
    sent = BROADCAST_STATS["sent"]
    failed = BROADCAST_STATS["failed"]
    blocked = BROADCAST_STATS["blocked"]
    processed = sent + failed + blocked
    progress = int(processed / total * 100) if total > 0 else 0
    
    await query.edit_message_text(
        f"📊 *LIVE BROADCAST STATS*\n\n"
        f"📨 Sent: `{sent}`\n"
        f"❌ Failed: `{failed}`\n"
        f"🚷 Blocked: `{blocked}`\n"
        f"📊 Total: `{total}`\n"
        f"📌 Processed: `{processed}`\n"
        f"⏳ Progress: `{progress}%`\n"
        f"🔄 Status: {'🛑 STOPPING' if BROADCAST_STOP else '🟢 RUNNING'}\n\n"
        f"📊 Progress Bar:\n"
        f"[{'█' * int(progress/5)}{'░' * (20 - int(progress/5))}] {progress}%",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data="broadcast_stats")],
            [InlineKeyboardButton("⏹️ STOP", callback_data="stop_broadcast")],
            [InlineKeyboardButton("🔙 Back", callback_data="close")]
        ])
    )


# ==================== BLOCK NUMBER ====================
async def block_number_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await update.message.reply_text("🚫 *Enter number to block:*\nExample: `9876543210`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_cancel_keyboard())
    return ASKING_BLOCK_NUMBER


async def block_number_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    text = update.message.text.strip()
    if text == "❌ Cancel":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_admin_keyboard())
        return ConversationHandler.END
    number = ''.join(filter(str.isdigit, text))
    if len(number) < 10:
        await update.message.reply_text("❌ Invalid number!", reply_markup=get_cancel_keyboard())
        return ASKING_BLOCK_NUMBER
    mongo.save_blocked_number(number, {"blocked_by": update.effective_user.id, "reason": "Blocked by admin", "date": datetime.now().isoformat()})
    await update.message.reply_text(f"✅ Number blocked: `{number}`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())
    return ConversationHandler.END


# ==================== UNBLOCK NUMBER ====================
async def unblock_number_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await update.message.reply_text("✅ *Enter number to unblock:*\nExample: `9876543210`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_cancel_keyboard())
    return ASKING_UNBLOCK_NUMBER


async def unblock_number_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    text = update.message.text.strip()
    if text == "❌ Cancel":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_admin_keyboard())
        return ConversationHandler.END
    number = ''.join(filter(str.isdigit, text))
    blocked = mongo.get_blocked_number(number)
    if blocked:
        mongo.remove_blocked_number(number)
        await update.message.reply_text(f"✅ Number unblocked: `{number}`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())
    else:
        await update.message.reply_text(f"❌ Number not found in block list", reply_markup=get_admin_keyboard())
    return ConversationHandler.END


# ==================== SET REFERRAL COINS ====================
async def set_referral_coins_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await update.message.reply_text(f"💰 *Enter referral coins amount:*\nCurrent: {settings['referral_coins']}\nExample: `15`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_cancel_keyboard())
    return ASKING_REFERRAL_AMOUNT


async def set_referral_coins_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    text = update.message.text.strip()
    if text == "❌ Cancel":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_admin_keyboard())
        return ConversationHandler.END
    try:
        amount = int(text)
        if amount < 0:
            raise ValueError
        settings["referral_coins"] = amount
        mongo.save_setting("referral_coins", amount)
        await update.message.reply_text(f"✅ Referral coins set to: {amount}", reply_markup=get_admin_keyboard())
    except:
        await update.message.reply_text("❌ Invalid amount!", reply_markup=get_cancel_keyboard())
        return ASKING_REFERRAL_AMOUNT
    return ConversationHandler.END


# ==================== ADD ADMIN ====================
async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Only owner can add admins!")
        return ConversationHandler.END
    await update.message.reply_text("👑 *Enter user ID or @username to add as admin:*", parse_mode=ParseMode.MARKDOWN, reply_markup=get_cancel_keyboard())
    return ASKING_ADD_ADMIN


async def add_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return ConversationHandler.END
    text = update.message.text.strip()
    if text == "❌ Cancel":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_admin_keyboard())
        return ConversationHandler.END
    user_id = find_user_by_identifier(text)
    if user_id:
        user = get_user(user_id)
        user["is_admin"] = True
        mongo.save_user(user)
        await update.message.reply_text(f"✅ Admin added: `{user_id}`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())
    else:
        await update.message.reply_text(f"❌ User not found: `{text}`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())
    return ConversationHandler.END


# ==================== REMOVE ADMIN ====================
async def remove_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("❌ Only owner can remove admins!")
        return ConversationHandler.END
    await update.message.reply_text("👑 *Enter user ID or @username to remove from admin:*", parse_mode=ParseMode.MARKDOWN, reply_markup=get_cancel_keyboard())
    return ASKING_REMOVE_ADMIN


async def remove_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return ConversationHandler.END
    text = update.message.text.strip()
    if text == "❌ Cancel":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_admin_keyboard())
        return ConversationHandler.END
    user_id = find_user_by_identifier(text)
    if user_id and user_id not in OWNER_IDS:
        user = get_user(user_id)
        user["is_admin"] = False
        mongo.save_user(user)
        await update.message.reply_text(f"✅ Admin removed: `{user_id}`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())
    else:
        await update.message.reply_text(f"❌ User not found or is owner", reply_markup=get_admin_keyboard())
    return ConversationHandler.END


# ==================== ADD COINS ====================
async def add_coins_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    await update.message.reply_text("💎 *Enter user ID or @username to add coins:*", parse_mode=ParseMode.MARKDOWN, reply_markup=get_cancel_keyboard())
    return ASKING_ADD_COINS_USER


async def add_coins_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    text = update.message.text.strip()
    if text == "❌ Cancel":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_admin_keyboard())
        return ConversationHandler.END
    user_id = find_user_by_identifier(text)
    if user_id:
        context.user_data["add_coins_user"] = user_id
        await update.message.reply_text("💎 *Enter amount of coins to add:*\nExample: `50`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_cancel_keyboard())
        return ASKING_ADD_COINS_AMOUNT
    else:
        await update.message.reply_text(f"❌ User not found: `{text}`", reply_markup=get_admin_keyboard())
        return ConversationHandler.END


async def add_coins_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    text = update.message.text.strip()
    if text == "❌ Cancel":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_admin_keyboard())
        return ConversationHandler.END
    try:
        amount = int(text)
        if amount <= 0:
            raise ValueError
        user_id = context.user_data.get("add_coins_user")
        if user_id:
            add_coins(user_id, amount)
            await update.message.reply_text(f"✅ Added {amount} coins to user `{user_id}`", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())
        else:
            await update.message.reply_text("❌ Error: User not found", reply_markup=get_admin_keyboard())
    except:
        await update.message.reply_text("❌ Invalid amount!", reply_markup=get_cancel_keyboard())
        return ASKING_ADD_COINS_AMOUNT
    return ConversationHandler.END


# ==================== KEY STATS ====================
async def key_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admins can view key stats!")
        return
    all_keys = mongo.get_all_keys()
    total = len(all_keys)
    used = sum(1 for k in all_keys if k.get("is_used", False))
    unused = total - used
    types = {}
    for key in all_keys:
        t = key.get("key_type", "NORMAL")
        if t not in types:
            types[t] = {"total": 0, "used": 0}
        types[t]["total"] += 1
        if key.get("is_used", False):
            types[t]["used"] += 1
    text = f"📊 *KEY STATISTICS*\n\n🔑 Total: {total}\n✅ Used: {used}\n🆕 Unused: {unused}\n\n*By Type:*"
    for t, stats in types.items():
        text += f"\n• `{t}`: {stats['used']}/{stats['total']} used"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())


# ==================== EXIT ADMIN ====================
async def exit_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("✅ Exited Admin Panel", reply_markup=get_main_keyboard(update.effective_user.id))


async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user_id = update.effective_user.id
    await update.message.reply_text("❌ Cancelled", reply_markup=get_main_keyboard(user_id))
    return ConversationHandler.END


async def back_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_admin(user_id):
        await update.message.reply_text("🔙 Back to Admin", reply_markup=get_admin_keyboard())
    else:
        await update.message.reply_text("🔙 Back to Menu", reply_markup=get_main_keyboard(user_id))
    return ConversationHandler.END


# ==================== MANDATORY CHANNEL ADMIN ====================
async def mandatory_channel_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admins can configure this!")
        return
    config = get_mandatory_channel_config()
    status = "🔴 OFF" if not config["enabled"] else "🟢 ON"
    channel_type = config.get("channel_type", "public")
    channel_type_display = "🔓 PUBLIC" if channel_type == "public" else "🔒 PRIVATE"

    keyboard = [
        [KeyboardButton("🔄 Toggle Mandatory Channel")],
        [KeyboardButton("📝 Set Channel Username (Public)")],
        [KeyboardButton("🔒 Set Private Channel ID")],
        [KeyboardButton(f"📢 Channel Type: {channel_type_display}")],
        [KeyboardButton("🔙 Back to Admin")]
    ]

    await update.message.reply_text(
        f"📢 *MANDATORY CHANNEL SETTINGS*\n\n"
        f"*Status:* {status}\n"
        f"*Type:* {channel_type_display}\n"
        f"*Channel Username:* @{config['username'] or 'Not Set'}\n"
        f"*Channel ID:* `{config['channel_id'] or 'Not Set'}`\n\n"
        f"*How it works:*\n"
        f"• PUBLIC: Add channel username (with @)\n"
        f"• PRIVATE: Add channel ID (numeric)\n"
        f"• Bot must be ADMIN in the channel!\n"
        f"• Users must join to use the bot.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return ASKING_SET_CHANNEL


async def handle_mandatory_channel_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    text = update.message.text

    if text == "🔙 Back to Admin":
        await update.message.reply_text("⚙️ *Admin Panel*", parse_mode=ParseMode.MARKDOWN, reply_markup=get_admin_keyboard())
        return ConversationHandler.END

    elif text == "🔄 Toggle Mandatory Channel":
        current = is_mandatory_channel_enabled()
        set_mandatory_channel_enabled(not current)
        status = "ON 🟢" if not current else "OFF 🔴"
        await update.message.reply_text(f"✅ Mandatory channel is now {status}", reply_markup=get_admin_keyboard())
        return ConversationHandler.END

    elif text == "📢 Channel Type: 🔓 PUBLIC" or text == "📢 Channel Type: 🔒 PRIVATE":
        current_type = get_mandatory_channel_type()
        new_type = "private" if current_type == "public" else "public"
        set_mandatory_channel_type(new_type)
        await update.message.reply_text(f"✅ Channel type changed to: {'PRIVATE 🔒' if new_type == 'private' else 'PUBLIC 🔓'}\n\nPlease update channel info accordingly.", reply_markup=get_admin_keyboard())
        return ConversationHandler.END

    elif text == "📝 Set Channel Username (Public)":
        await update.message.reply_text(
            "📝 *Enter channel username (without @) for PUBLIC channel:*\n\n"
            "Example: `my_channel`\n\n"
            "Make sure bot is ADMIN in this channel!\n\n"
            "Send /cancel to cancel.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_cancel_keyboard()
        )
        context.user_data["setting_channel_type"] = "username"
        return ASKING_SET_CHANNEL

    elif text == "🔒 Set Private Channel ID":
        await update.message.reply_text(
            "📝 *Enter PRIVATE channel ID:*\n\n"
            "Example: `-1001234567890`\n\n"
            "How to get channel ID:\n"
            "1. Add bot as admin to channel\n"
            "2. Forward any message from channel to @userinfobot\n"
            "3. Copy the channel ID (starts with -100)\n\n"
            "Send /cancel to cancel.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_cancel_keyboard()
        )
        context.user_data["setting_channel_type"] = "channel_id"
        return ASKING_SET_CHANNEL

    else:
        setting_type = context.user_data.get("setting_channel_type")
        if setting_type == "username":
            username = text.strip().lstrip('@')
            set_mandatory_channel(username=username)
            await update.message.reply_text(
                f"✅ Channel username set to: @{username}\n\n"
                f"Make sure bot is admin in @{username}!\n"
                f"Channel type: PUBLIC",
                reply_markup=get_admin_keyboard()
            )
        elif setting_type == "channel_id":
            try:
                channel_id = int(text.strip())
                set_mandatory_channel(channel_id=channel_id)
                await update.message.reply_text(
                    f"✅ Private channel ID set to: `{channel_id}`\n\n"
                    f"Make sure bot is admin in this channel!\n"
                    f"Channel type: PRIVATE",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=get_admin_keyboard()
                )
            except ValueError:
                await update.message.reply_text("❌ Invalid channel ID! Must be a number.", reply_markup=get_admin_keyboard())
        context.user_data.pop("setting_channel_type", None)
        return ConversationHandler.END


# ==================== CALLBACK HANDLERS ====================
async def broadcast_keys_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_")
    if len(parts) >= 4:
        key_type = parts[2]
        count = parts[3]
        credits = parts[4] if len(parts) > 4 else "0"
        unused = get_unused_keys(key_type)
        recent = unused[-int(count):] if len(unused) >= int(count) else unused
        if not recent:
            await query.edit_message_text("❌ No keys found to broadcast!")
            return
        keys_text = "\n".join([f"`{k['key']}`" for k in recent[:20]])
        msg = f"🔑 *NEW KEYS AVAILABLE!*\n\n📋 Type: `{key_type}`\n💰 Credits: {credits}\n🔢 Available: {len(recent)}\n\n*Sample Keys:*\n{keys_text}\n\nUse /redeem <key> to redeem!"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ YES, BROADCAST", callback_data=f"confirm_broadcast_{key_type}")],
            [InlineKeyboardButton("❌ NO, CANCEL", callback_data="close")]
        ])

        await query.edit_message_text(
            f"📢 *Broadcast these keys?*\n\nPreview:\n{msg[:400]}...",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        context.user_data["broadcast_keys"] = recent
        context.user_data["broadcast_key_type"] = key_type
        context.user_data["broadcast_credits"] = credits


async def confirm_broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key_type = context.user_data.get("broadcast_key_type", "NORMAL")
    keys = context.user_data.get("broadcast_keys", [])
    credits = context.user_data.get("broadcast_credits", 0)

    if not keys:
        await query.edit_message_text("❌ No keys to broadcast!")
        return

    keys_text = "\n".join([f"`{k['key']}`" for k in keys[:20]])
    msg = f"🔑 *NEW KEYS AVAILABLE!*\n\n📋 Type: `{key_type}`\n💰 Credits: {credits}\n🔢 Available: {len(keys)}\n\n*Sample Keys:*\n{keys_text}\n\nUse /redeem <key> to redeem!"

    await query.edit_message_text("📢 Broadcasting keys to all users...")

    success = 0
    failed = 0
    blocked = 0

    for user in mongo.get_all_users():
        uid = user['user_id']
        try:
            if user.get("is_blocked", False):
                blocked += 1
                continue
            await context.bot.send_message(uid, msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
            success += 1
        except Exception as e:
            failed += 1
            logger.error(f"Failed to broadcast keys to {uid}: {e}")
        await asyncio.sleep(0.05)

    await query.edit_message_text(
        f"✅ *Broadcast Complete!*\n"
        f"📨 Sent: {success}\n"
        f"❌ Failed: {failed}\n"
        f"🚷 Blocked: {blocked}\n"
        f"🔑 Keys broadcasted: {len(keys)}",
        parse_mode=ParseMode.MARKDOWN
    )

    context.user_data.pop("broadcast_keys", None)
    context.user_data.pop("broadcast_key_type", None)
    context.user_data.pop("broadcast_credits", None)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "close":
        await query.delete_message()
    elif query.data == "check_join":
        await check_join_callback(update, context)
    elif query.data.startswith("broadcast_keys_"):
        await broadcast_keys_callback(update, context)
    elif query.data.startswith("confirm_broadcast_"):
        await confirm_broadcast_callback(update, context)
    elif query.data.startswith("buy_"):
        coins = query.data.split("_")[1]
        prices = {"50": 30, "100": 50, "250": 120, "500": 200}
        text = f"💎 *Purchase {coins} Coins*\nAmount: ₹{prices.get(coins, 0)}\nUPI: `{UPI_ID}`\nContact: @{SUPPORT_USERNAME}"
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    elif query.data == "confirm_reset_credits":
        await confirm_reset_credits(update, context)
    elif query.data.startswith("maint_"):
        await handle_maintenance_callback(update, context)
    elif query.data == "stop_broadcast":
        global BROADCAST_STOP
        BROADCAST_STOP = True
        await query.edit_message_text("⏹️ *Stopping broadcast...*", parse_mode=ParseMode.MARKDOWN)
    elif query.data == "broadcast_stats":
        await broadcast_stats_callback(update, context)


async def all_users_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admins can view this!")
        return

    try:
        all_users = mongo.get_all_users()
        if not all_users:
            await update.message.reply_text("📊 *USER STATISTICS*\n\nNo users found in database.", parse_mode=ParseMode.MARKDOWN)
            return

        total_users = len(all_users)
        blocked_users = len([u for u in all_users if u.get("is_blocked", False)])
        admin_users = len([u for u in all_users if u.get("is_admin", False)])

        total_coins = sum(u.get("coins", 0) for u in all_users)
        total_searches = sum(u.get("total_searches", 0) for u in all_users)

        user_activity = mongo.get_daily_weekly_monthly_users()
        daily_active = user_activity.get("daily", 0)
        weekly_active = user_activity.get("weekly", 0)
        monthly_active = user_activity.get("monthly", 0)

        daily_percent = (daily_active / total_users * 100) if total_users > 0 else 0
        weekly_percent = (weekly_active / total_users * 100) if total_users > 0 else 0
        monthly_percent = (monthly_active / total_users * 100) if total_users > 0 else 0

        users_by_searches = sorted(all_users, key=lambda x: x.get("total_searches", 0), reverse=True)[:10]
        users_by_coins = sorted([u for u in all_users if not is_admin(u["user_id"])], 
                               key=lambda x: x.get("coins", 0), reverse=True)[:10]

        search_stats = mongo.get_global_search_stats()

        output = f"""\n📊 *COMPREHENSIVE USER STATISTICS*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n👥 *USER OVERVIEW*\n• Total Users: `{total_users}`\n• Blocked Users: `{blocked_users}`\n• Admin Users: `{admin_users}`\n\n📊 *ACTIVE USERS*\n• Daily Active: `{daily_active}` ({daily_percent:.1f}%)\n• Weekly Active: `{weekly_active}` ({weekly_percent:.1f}%)\n• Monthly Active: `{monthly_active}` ({monthly_percent:.1f}%)\n\n💰 *ECONOMY*\n• Total Coins: `{total_coins:,}`\n• Total Searches: `{total_searches:,}`\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🏆 *TOP 10 USERS (BY SEARCHES)*\n"""
        for i, user in enumerate(users_by_searches, 1):
            username = user.get("username", "No username")
            user_id = user["user_id"]
            searches = user.get("total_searches", 0)
            output += f"{i}. `{user_id}` - @{username}\n   🔍 {searches:,} searches\n"

        output += f"\n💰 *TOP 10 USERS (BY COINS)*\n"
        for i, user in enumerate(users_by_coins, 1):
            username = user.get("username", "No username")
            user_id = user["user_id"]
            coins = user.get("coins", 0)
            output += f"{i}. `{user_id}` - @{username}\n   💰 {coins:,} coins\n"

        output += f"""\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📈 *GLOBAL SEARCH STATS*\n• Total Searches: `{search_stats.get('total', 0):,}`\n• Today: `{search_stats.get('daily', 0):,}`\n• This Week: `{search_stats.get('weekly', 0):,}`\n• This Month: `{search_stats.get('monthly', 0):,}`\n\n🔍 *MOST SEARCHED SERVICES*\n"""
        for stat in search_stats.get("by_type", [])[:5]:
            search_type = stat.get("_id", "Unknown")
            count = stat.get("count", 0)
            output += f"• {search_type}: {count:,}\n"

        output += f"""\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👑 *Developer:* @{DEVELOPER_USERNAME}\n"""

        await send_long_message(update, output)
        await update.message.reply_text("✅ Stats generated!", reply_markup=get_admin_keyboard())

    except Exception as e:
        logger.error(f"Error in all_users_stats: {e}")
        await update.message.reply_text(f"❌ Error generating stats: {str(e)[:100]}", reply_markup=get_admin_keyboard())


async def all_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admins can view this!")
        return

    try:
        all_users_list = mongo.get_all_users()
        total = len(all_users_list)

        if total == 0:
            await update.message.reply_text("👥 No users found in database.", reply_markup=get_admin_keyboard())
            return

        text = f"👥 *TOTAL USERS:* {total}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        for i, user in enumerate(all_users_list[:30], 1):
            uid = user.get('user_id')
            username = user.get('username', 'No username')
            coins = user.get('coins', 0)
            searches = user.get('total_searches', 0)
            blocked = "🚷 " if user.get('is_blocked', False) else ""
            text += f"{i}. {blocked}`{uid}` - @{username}\n   💰 {coins} coins | 🔍 {searches}\n\n"

        if total > 30:
            text += f"\n_... and {total - 30} more users_"

        await send_long_message(update, text)
        await update.message.reply_text("✅ Done", reply_markup=get_admin_keyboard())

    except Exception as e:
        logger.error(f"Error in all_users_command: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}", reply_markup=get_admin_keyboard())


async def reset_credits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admins can reset credits!")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ YES, RESET ALL", callback_data="confirm_reset_credits")],
        [InlineKeyboardButton("❌ NO, CANCEL", callback_data="close")]
    ])

    await update.message.reply_text(
        "⚠️ *WARNING: RESET ALL CREDITS*\n\n"
        "This will set ALL user coins to ZERO.\n"
        "Users will only have their daily free limit.\n\n"
        "Are you sure?",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )


async def confirm_reset_credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.edit_message_text("❌ Only admins can reset credits!")
        return

    await query.edit_message_text("⏳ Resetting all user credits...")
    count = reset_all_credits()
    await query.edit_message_text(
        f"✅ *CREDITS RESET COMPLETE*\n\n"
        f"📊 Total users affected: `{count}`\n"
        f"💰 All coins set to 0\n"
        f"📅 Daily free limit: {settings['daily_limit']}\n\n"
        f"👑 *Developer:* @{DEVELOPER_USERNAME}",
        parse_mode=ParseMode.MARKDOWN
    )


# ==================== DETECT COINS ====================
async def detect_coins_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admins can use this!")
        return ConversationHandler.END

    await update.message.reply_text(
        "🔍 *DETECT COINS*\n\n"
        "Enter user ID or @username to detect their coins:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_cancel_keyboard()
    )
    return ASKING_DETECT_COINS_USER


async def detect_coins_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    text = update.message.text.strip()
    if text == "❌ Cancel":
        await update.message.reply_text("❌ Cancelled", reply_markup=get_admin_keyboard())
        return ConversationHandler.END

    user_id = find_user_by_identifier(text)

    if not user_id:
        await update.message.reply_text(
            f"❌ User not found: `{text}`\n\n"
            f"Try entering the numeric User ID directly.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_cancel_keyboard()
        )
        return ASKING_DETECT_COINS_USER

    user = get_user(user_id)
    username = user.get("username", "No username")
    coins = user.get("coins", 0)
    total_searches = user.get("total_searches", 0)

    context.user_data["detect_target_user"] = user_id

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➖ Deduct Coins", callback_data=f"deduct_coins_{user_id}")],
        [InlineKeyboardButton("➕ Add Coins", callback_data=f"add_coins_detect_{user_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="close")]
    ])

    await update.message.reply_text(
        f"🔍 *USER COINS DETECTED*\n\n"
        f"👤 User: `{user_id}`\n"
        f"📛 Username: @{username}\n"
        f"💰 Coins: `{coins}`\n"
        f"🔍 Total Searches: `{total_searches}`\n"
        f"📅 Joined: `{user.get('joined_date', 'Unknown')[:10]}`\n\n"
        f"Select an action below:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )
    return ConversationHandler.END


async def toggle_daily_free(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admins can do this!")
        return

    current = settings.get("daily_free_enabled", True)
    settings["daily_free_enabled"] = not current
    mongo.save_setting("daily_free_enabled", settings["daily_free_enabled"])

    status = "ENABLED 🟢" if settings["daily_free_enabled"] else "DISABLED 🔴"
    await update.message.reply_text(
        f"✅ Daily Free Searches are now {status}\n\n"
        f"Daily Limit: {settings['daily_limit']}",
        reply_markup=get_admin_keyboard()
    )


# ==================== ERROR HANDLER ====================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ An error occurred! Please try again later.")


# ==================== MAIN ====================
def main():
    load_settings()

    app = Application.builder().token(BOT_TOKEN).connect_timeout(30).read_timeout(30).write_timeout(30).build()

    # Search handlers
    search_handlers = [
        (MessageHandler(filters.Regex("^🔍 Indian Number$"), indian_number_button), ASKING_NUMBER, handle_indian_number),
        (MessageHandler(filters.Regex("^🆔 Indian Aadhar$"), indian_aadhar_button), ASKING_AADHAR, handle_indian_aadhar),
        (MessageHandler(filters.Regex("^🇵🇰 Pak Number$"), pak_number_button), ASKING_PAK_NUM, handle_pak_number),
        (MessageHandler(filters.Regex("^🪪 Pak CNIC$"), pak_cnic_button), ASKING_PAK_CNIC, handle_pak_cnic),
        (MessageHandler(filters.Regex("^🚔 Pak Police$"), pak_police_button), ASKING_PAK_POLICE, handle_pak_police),
        (MessageHandler(filters.Regex("^💰 GST Billing$"), gst_billing_button), ASKING_GST_BILLING, handle_gst_billing),
        (MessageHandler(filters.Regex("^📇 PAN to GST$"), pan_gst_button), ASKING_PAN_GST, handle_pan_gst),
        (MessageHandler(filters.Regex("^👨‍👩‍👧 Aadhar Family$"), aadhar_family_button), ASKING_AADHAR_FAMILY, handle_aadhar_family),
        (MessageHandler(filters.Regex("^📱 TG Info$"), tg_info_button), ASKING_TG_USERNAME, handle_tg_info),
    ]
    for entry, state, handler in search_handlers:
        app.add_handler(ConversationHandler(
            entry_points=[entry],
            states={state: [MessageHandler(filters.TEXT & ~filters.COMMAND, handler)]},
            fallbacks=[MessageHandler(filters.Regex("^❌ Cancel$"), cancel_operation), MessageHandler(filters.Regex("^🔙 Back$"), back_operation)]
        ))

    # Other conversations
    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🎫 Redeem Key$"), redeem_key_command), CommandHandler("redeem", redeem_key_command)],
        states={ASKING_REDEEM_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_redeem_key)]},
        fallbacks=[MessageHandler(filters.Regex("^❌ Cancel$"), cancel_operation)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🗑️ Revoke Single Key$"), revoke_single_key_start)],
        states={ASKING_REVOKE_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, revoke_single_key_input)]},
        fallbacks=[MessageHandler(filters.Regex("^❌ Cancel$"), cancel_operation)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🗑️ Revoke By Type$"), revoke_by_type_start)],
        states={ASKING_REVOKE_KEY_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, revoke_by_type_input)]},
        fallbacks=[MessageHandler(filters.Regex("^🔙 Back$"), back_operation)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🚷 Block User$"), block_user_start)],
        states={ASKING_BLOCK_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, block_user_input)]},
        fallbacks=[MessageHandler(filters.Regex("^❌ Cancel$"), cancel_operation)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^✅ Unblock User$"), unblock_user_start)],
        states={ASKING_UNBLOCK_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, unblock_user_input)]},
        fallbacks=[MessageHandler(filters.Regex("^❌ Cancel$"), cancel_operation)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📝 Update API URL$"), update_api_select)],
        states={
            ASKING_API_SELECT: [MessageHandler(filters.Regex("^📝 Update"), update_api_url_start), MessageHandler(filters.Regex("^🔙 Back$"), back_to_admin)],
            ASKING_API_UPDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_api_url_input)]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Cancel$"), cancel_operation), MessageHandler(filters.Regex("^🔙 Back$"), back_to_admin)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📢 Channel Settings$"), mandatory_channel_settings)],
        states={ASKING_SET_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mandatory_channel_input)]},
        fallbacks=[MessageHandler(filters.Regex("^🔙 Back$"), back_operation)]
    ))

    # Fixed broadcast handler - using filters.ALL to handle all message types
    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📢 Broadcast$"), broadcast_start)],
        states={ASKING_BROADCAST: [MessageHandler(filters.ALL & ~filters.COMMAND, broadcast_send)]},
        fallbacks=[MessageHandler(filters.Regex("^❌ Cancel$"), cancel_operation)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🚫 Block Number$"), block_number_start)],
        states={ASKING_BLOCK_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, block_number_input)]},
        fallbacks=[MessageHandler(filters.Regex("^❌ Cancel$"), cancel_operation)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^✅ Unblock Number$"), unblock_number_start)],
        states={ASKING_UNBLOCK_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, unblock_number_input)]},
        fallbacks=[MessageHandler(filters.Regex("^❌ Cancel$"), cancel_operation)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💰 Set Referral Coins$"), set_referral_coins_start)],
        states={ASKING_REFERRAL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_referral_coins_input)]},
        fallbacks=[MessageHandler(filters.Regex("^❌ Cancel$"), cancel_operation)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^👑 Add Admin$"), add_admin_start)],
        states={ASKING_ADD_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_admin_input)]},
        fallbacks=[MessageHandler(filters.Regex("^❌ Cancel$"), cancel_operation)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^👑 Remove Admin$"), remove_admin_start)],
        states={ASKING_REMOVE_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_admin_input)]},
        fallbacks=[MessageHandler(filters.Regex("^❌ Cancel$"), cancel_operation)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💎 Add Coins$"), add_coins_start)],
        states={
            ASKING_ADD_COINS_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_coins_user_input)],
            ASKING_ADD_COINS_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_coins_amount_input)]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ Cancel$"), cancel_operation)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📊 Set Daily Limit$"), set_daily_limit_start)],
        states={ASKING_SET_DAILY_LIMIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_daily_limit_input)]},
        fallbacks=[MessageHandler(filters.Regex("^❌ Cancel$"), cancel_operation)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔧 Maintenance$"), maintenance_menu)],
        states={ASKING_MAINTENANCE_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_maintenance_message_input)]},
        fallbacks=[MessageHandler(filters.Regex("^❌ Cancel$"), cancel_operation)]
    ))

    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔍 Detect Coins$"), detect_coins_start)],
        states={ASKING_DETECT_COINS_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, detect_coins_user_input)]},
        fallbacks=[MessageHandler(filters.Regex("^❌ Cancel$"), cancel_operation)]
    ))

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", my_stats))
    app.add_handler(CommandHandler("coins", my_coins))
    app.add_handler(CommandHandler("referral", referral_link_command))
    app.add_handler(CommandHandler("buy", buy_coins))
    app.add_handler(CommandHandler("num", num_command))
    app.add_handler(CommandHandler("aadhar", aadhar_command))
    app.add_handler(CommandHandler("gen", generate_keys_command))
    app.add_handler(CommandHandler("key_stats", key_stats_command))
    app.add_handler(CommandHandler("system", system_info_command))
    app.add_handler(CommandHandler("history", search_history_command))
    app.add_handler(CommandHandler("revoke", revoke_all_unused))
    app.add_handler(CommandHandler("maintenance", maintenance_mode_command))
    app.add_handler(CommandHandler("toggle_daily", toggle_daily_free))
    app.add_handler(CommandHandler("approve", approve_group_command))
    app.add_handler(CommandHandler("reject", reject_group_command))
    app.add_handler(CommandHandler("revoke_approval", revoke_approval_command))
    app.add_handler(CommandHandler("id", id_command))
    app.add_handler(CommandHandler("stop_broadcast", stop_broadcast))

    # Admin menu handlers
    app.add_handler(MessageHandler(filters.Regex("^⚙️ Admin Panel$"), admin_panel))
    app.add_handler(MessageHandler(filters.Regex("^⚙️ API Settings$"), api_settings_menu))
    app.add_handler(MessageHandler(filters.Regex("^📊 API Status$"), api_status))
    app.add_handler(MessageHandler(filters.Regex("^📊 Bot Status$"), bot_status))
    app.add_handler(MessageHandler(filters.Regex("^👥 All Users$"), all_users_command))
    app.add_handler(MessageHandler(filters.Regex("^📊 All Users Stats$"), all_users_stats))
    app.add_handler(MessageHandler(filters.Regex("^📋 Blocked List$"), blocked_list))
    app.add_handler(MessageHandler(filters.Regex("^📋 Admin List$"), admin_list))
    app.add_handler(MessageHandler(filters.Regex("^🔛 Toggle Bot$"), toggle_bot))
    app.add_handler(MessageHandler(filters.Regex("^🔧 Maintenance$"), maintenance_menu))
    app.add_handler(MessageHandler(filters.Regex("^🔧 Enable$"), handle_maintenance_menu))
    app.add_handler(MessageHandler(filters.Regex("^✅ Disable$"), handle_maintenance_menu))
    app.add_handler(MessageHandler(filters.Regex("^📝 Set Message$"), set_maintenance_message_start))
    app.add_handler(MessageHandler(filters.Regex("^🔑 Generate Keys$"), generate_keys_command))
    app.add_handler(MessageHandler(filters.Regex("^📋 Key Stats$"), key_stats_command))
    app.add_handler(MessageHandler(filters.Regex("^🗑️ Revoke Keys$"), revoke_keys_menu))
    app.add_handler(MessageHandler(filters.Regex("^🗑️ Revoke All Unused$"), revoke_all_unused))
    app.add_handler(MessageHandler(filters.Regex("^📋 Unused Keys$"), show_unused_keys))
    app.add_handler(MessageHandler(filters.Regex("^🚷 Blocked Users$"), show_blocked_users))
    app.add_handler(MessageHandler(filters.Regex("^📢 Channel Settings$"), mandatory_channel_settings))
    app.add_handler(MessageHandler(filters.Regex("^💰 Reset All Credits$"), reset_credits_command))
    app.add_handler(MessageHandler(filters.Regex("^🔍 Detect Coins$"), detect_coins_start))
    app.add_handler(MessageHandler(filters.Regex("^🔄 Toggle Daily Free$"), toggle_daily_free))
    app.add_handler(MessageHandler(filters.Regex("^📋 Pending Approvals$"), show_pending_approvals))
    app.add_handler(MessageHandler(filters.Regex("^✅ Approved Groups$"), show_approved_groups))
    app.add_handler(MessageHandler(filters.Regex("^🔙 Exit Admin$"), exit_admin))
    app.add_handler(MessageHandler(filters.Regex("^🔙 Back to Admin$"), back_to_admin))

    # User menu handlers
    app.add_handler(MessageHandler(filters.Regex("^💎 My Coins$"), my_coins))
    app.add_handler(MessageHandler(filters.Regex("^🔗 Referral$"), referral_link_command))
    app.add_handler(MessageHandler(filters.Regex("^📊 Stats$"), my_stats))
    app.add_handler(MessageHandler(filters.Regex("^🖥️ System Info$"), system_info_command))
    app.add_handler(MessageHandler(filters.Regex("^❓ Help$"), help_command))
    app.add_handler(MessageHandler(filters.Regex("^📜 History$"), search_history_command))
    app.add_handler(MessageHandler(filters.Regex("^💰 Buy Coins$"), buy_coins))

    # API toggle
    app.add_handler(MessageHandler(filters.Regex(r"^(🟢|🔴) (Indian Number|Indian Aadhar|Pakistan Number|Pakistan CNIC|Pakistan Police|GST Billing|PAN to GST|Aadhar Family|TG Info)$"), toggle_api_handler))

    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_error_handler(error_handler)

    logger.info("✅ Bot started successfully!")
    logger.info(f"Version: {BOT_VERSION}")
    logger.info(f"Maintenance Mode: {'ON' if MAINTENANCE_MODE else 'OFF'}")
    logger.info(f"Maintenance Message: {MAINTENANCE_MESSAGE[:50]}...")
    logger.info(f"Mandatory Channel: {'ON' if MANDATORY_CHANNEL_ENABLED else 'OFF'} ({get_mandatory_channel_type()})")
    logger.info(f"Daily Free: {'ON' if settings.get('daily_free_enabled', True) else 'OFF'}")
    logger.info(f"Approved Groups: {len(APPROVED_GROUPS)}, Pending: {len(PENDING_APPROVALS)}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()