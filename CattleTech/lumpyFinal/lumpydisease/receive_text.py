import telepot

# Replace 'YOUR_BOT_API_TOKEN' with your actual bot token
# bot = telepot.Bot('7173027390:AAGtrjBgTKzadlpGBjJbkVO8qw_y9F6y_Ng')
bot = telepot.Bot('7336448383:AAG9biC3i8SCf86IJEjMRpwLdpmyZgzRffQ')

# Get updates (messages) from the Telegram bot
response = bot.getUpdates()
print(response)
# Process the received messages
for message in response:
    content_type = message['message']['chat']['type']
    chat_id = message['message']['chat']['id']
    print(chat_id)

    # Check if the message is a text message
    if content_type == 'private' and 'text' in message['message']:
        text = message['message']['text']
        # Process the text message as per your requirements
        print(text)
