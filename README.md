# Telegram Auto-Posting & Giveaway Bot 🎉  

A simple yet powerful Telegram bot for auto-posting and running giveaways, built using `pyTelegramBotAPI`. This bot is designed for a single admin user and supports scheduled posts, giveaways with participant tracking, and mandatory subscriptions for entering giveaways.  

## Features 🚀  

### ✅ Auto-Posting  
- Store user data in `data/db.txt`.  
- Add channels to the bot.  
- Write a post, attach an image, select channels, and schedule a time for posting.  
- The bot will publish the post in all selected channels at the scheduled time.  

### 🎁 Giveaways  
- Create a giveaway with:  
  - Giveaway text  
  - Giveaway image  
  - A participation button (shows participant count)  
  - The number of winners  
  - A deadline or a required number of participants  
  - **Optional:** A mandatory subscription to a channel before participating  
- The bot randomly selects winners and announces them in the channel.  
- Winners receive a private message with prize details.  
- An inline button **"Claim Prize"** directs winners to a link provided during giveaway setup.  

### 📜 Commands
 - /start	Start the bot and view commands
- /addchannel	Add a new channel
 - /post	Create and schedule a post
 - /giveaway	Start a giveaway
 - /stats	View bot statistics

### 📄 License
This project is licensed under the MIT License. Feel free to contribute or modify it as needed!

