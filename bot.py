import logging
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from meta_ai_api import MetaAI

# Set up logging to track issues
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MetaAI API
ai = MetaAI()

# Cache to store user messages and their AI responses
message_cache = {}

# Dictionary for throttling user messages (rate-limiting)
user_last_message_time = {}

# Dictionary to store user data (id and name)
user_data = {}

# Function to handle the '/start' command
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id  # Get the user's unique ID
    user_name = update.message.from_user.first_name  # Get the user's first name

    # Check if the user is already in the dictionary
    if user_id not in user_data:
        # If new user, store their name in the dictionary
        user_data[user_id] = {'name': user_name}
        greeting = f"Hello {user_name}! Welcome to the AI chatbot."
    else:
        # If user is already in the dictionary, greet them by name
        greeting = f"Welcome back, {user_data[user_id]['name']}!"

    # Send the greeting message to the user
    await update.message.reply_text(greeting)

# Function to handle the '/help' command
async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "I'm your AI chatbot! You can ask me anything, and I'll try my best to answer.\n\n"
        "Just type your question and I'll reply with information I find!"
    )

# Function to handle incoming messages
async def handle_message(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text  # Get user's message
    user_id = update.message.from_user.id
    current_time = time.time()

    # Throttling - Check if the user has sent a message too quickly
    if user_id in user_last_message_time:
        time_diff = current_time - user_last_message_time[user_id]
        if time_diff < 2:  # Allow a maximum of 1 message every 2 seconds
            await update.message.reply_text("Please wait a moment before sending another message.")
            return

    # Update the last message time for the user
    user_last_message_time[user_id] = current_time

    # Check if the response is cached
    if user_message in message_cache:
        response_data = message_cache[user_message]
    else:
        response_data = ai.prompt(message=user_message)  # Get AI's response
        message_cache[user_message] = response_data  # Cache the result

    message = response_data.get('message', '')
    sources = response_data.get('sources', [])
    media = response_data.get('media', [])

    # Build the response without the "Answer:" label
    reply_message = message  # Directly use the AI's response message

    # If sources are not empty, include them in the message as a bullet point list
    if sources:
        reply_message += "\n\n*Sources:*\n" + "\n".join([f"• [{source['title']}]({source['link']})" for source in sources])

    # If media is not empty, include media information in the message
    if media:
        reply_message += "\n\n*Media:*\n" + "\n".join(media)

    # Log the user message and AI response
    logger.info(f"User: {user_message}")
    logger.info(f"AI Response: {message}")

    # Send the response message to the user using Markdown formatting
    await update.message.reply_text(reply_message, parse_mode="Markdown")

# Error handler to catch and log errors
async def error_handler(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def main():
    # Replace with your actual Telegram bot API key
    bot_token = "7785010346:AAEj-oMHqSONpvvtQtd1r2BJU1RKxVoCW-8"  # Your API Key here
    
    # Initialize the Application with your bot's token
    application = Application.builder().token(bot_token).build()

    # Add command handler for '/start'
    application.add_handler(CommandHandler("start", start))

    # Add command handler for '/help'
    application.add_handler(CommandHandler("help", help_command))

    # Add message handler for text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Add error handler to log any errors
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
