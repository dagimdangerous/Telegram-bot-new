

#!/usr/bin/env python3
"""
🤖 SMART ASSISTANT BOT
With Memory, Images, and Clean Formatting
"""

import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import html

# --- CONFIGURATION ---
import os
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Debug: Print to see if variables loaded (remove after testing)
print(f"Token loaded: {TELEGRAM_TOKEN is not None}")
print(f"API Key loaded: {OPENROUTER_API_KEY is not None}")

# --- MEMORY SYSTEM ---
conversation_history = {}

def get_memory(user_id):
    """Get or create memory for a user"""
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    return conversation_history[user_id]

def add_to_memory(user_id, role, content):
    """Add a message to conversation history"""
    memory = get_memory(user_id)
    memory.append({"role": role, "content": content})
    # Keep only last 10 messages to save memory
    if len(memory) > 10:
        memory.pop(0)

def format_memory_for_prompt(user_id):
    """Format conversation history for the prompt"""
    memory = get_memory(user_id)
    if not memory:
        return ""
    
    formatted = "\nPrevious conversation:\n"
    for msg in memory:
        if msg["role"] == "user":
            formatted += f"User: {msg['content']}\n"
        else:
            formatted += f"Assistant: {msg['content']}\n"
    return formatted

# --- BEHAVIOR SETTINGS ---
SYSTEM_PROMPT = """You are a tech savy, philosopher, scientist, all in one and friendly assistant. 
You remember previous conversations and build on them.
You give warm, thoughtful responses.
Use emojis SPARINGLY - only for titles and section headers."""
TEMPERATURE = 1.3
MAX_TOKENS = 800
MODEL = "openrouter/free"

# --- SETUP ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- OPENROUTER API ---
def call_openrouter(user_id, prompt):
    """Send prompt to OpenRouter with memory context"""
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Get conversation history
    memory_text = format_memory_for_prompt(user_id)
    
    # Build the full prompt with memory
    full_prompt = f"{memory_text}\nUser: {prompt}"
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": full_prompt}
        ],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=4)
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data["choices"][0]["message"]["content"]
            
            # Save to memory
            add_to_memory(user_id, "user", prompt)
            add_to_memory(user_id, "assistant", ai_response)
            
            return ai_response
        else:
            return f"Error: {response.status_code}"
            
    except Exception as e:
        return f"Connection error: {str(e)}"

# --- IMAGE HANDLER ---
def generate_image(prompt):
    """Generate an image using OpenRouter's image models (if available)"""
    # Note: OpenRouter's free tier has limited image models
    # This is a placeholder for when you add image capabilities
    return "Image generation coming soon! 🎨"

# --- FORMAT RESPONSES ---
def format_response(text):
    """Format the response with nice structure"""
    # This is where you can add custom formatting
    
    # If the response is short, just return it
    if len(text) < 100:
        return text
    
    # For longer responses, add some structure
    lines = text.split('\n')
    formatted = []
    
    for line in lines:
        # If line looks like a title (short, no punctuation at end)
        if len(line) < 60 and not line.endswith(('.', '!', '?')) and line:
            formatted.append(f"\n🌟 {line}\n")
        else:
            formatted.append(line)
    
    return '\n'.join(formatted)

# --- TELEGRAM HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    
    # Initialize memory for this user
    get_memory(user_id)
    
    welcome = f"""
🌟 WELCOME {first_name.upper()}!

🤖 I'm your Smart Assistant with:
• Memory - I remember our conversations
• Knowledge - I can answer any question
• Images - Coming soon!

📝 HOW TO USE ME:
• Just type any question
• Ask me to remember things
• I'll keep track of our chat

What would you like to know today?
"""
    await update.message.reply_text(welcome)

async def clear_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear conversation memory for the user"""
    user_id = update.effective_user.id
    if user_id in conversation_history:
        conversation_history[user_id] = []
        await update.message.reply_text("🧹 Memory cleared! We're starting fresh.")
    else:
        await update.message.reply_text("No memory to clear!")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = """
🤖 SMART ASSISTANT BOT

FEATURES:
• 🧠 Conversation Memory
• 💬 Natural Language Processing
• 📚 General Knowledge
• 🎨 Image Generation (coming soon)

TECHNOLOGY:
• Python & python-telegram-bot
• OpenRouter AI
• Meta Llama 3.2 3B

COMMANDS:
/start - Welcome
/about - About this bot
/clear - Clear memory
/help - Show help

Created by [Your Name]
"""
    await update.message.reply_text(about_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📚 HOW TO USE THIS BOT

💬 CHAT:
• Send any message to chat
• I remember our conversation

🧠 MEMORY:
• I remember the last 10 messages
• Use /clear to reset memory

🎨 FEATURES:
• Answer questions
• Provide explanations
• Give advice
• Have conversations

❓ EXAMPLE QUESTIONS:
• "What is AI?"
• "Explain quantum physics"
• "Give me study tips"
• "Tell me a story"

Just start typing!
"""
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text.strip()
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Check for image generation request (simple detection)
    if any(word in user_message.lower() for word in ['generate image', 'create image', 'draw', 'make an image']):
        await update.message.reply_text("🎨 Image generation is coming soon! Stay tuned.")
        return
    
    # Get AI response with memory
    response = call_openrouter(user_id, user_message)
    
    # Format the response
    formatted_response = format_response(response)
    
    # Send the response
    await update.message.reply_text(formatted_response)

# --- MAIN ---

def main():
    print("🤖 Starting Smart Assistant Bot...")
    print(f"🧠 Memory: Enabled")
    print(f"📊 Temperature: {TEMPERATURE}")
    print(f"📝 Max Tokens: {MAX_TOKENS}")
    print(f"🔮 Model: {MODEL}")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("clear", clear_memory))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Bot is running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
