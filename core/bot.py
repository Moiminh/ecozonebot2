# Trong file bot/core/bot.py

@bot.event
async def on_message(message: nextcord.Message):
    logger.debug(f"ON_MESSAGE: Received message: '{message.content}' from {message.author.name} ({message.author.id}) in G:{message.guild.id if message.guild else 'DM'}/C:{message.channel.id}")

    if message.author.bot:
        logger.debug(f"ON_MESSAGE: Message from bot {message.author.name}, ignoring.")
        return

    if not message.guild: 
        logger.debug(f"ON_MESSAGE: DM message from {message.author.name}. Processing commands.")
        await bot.process_commands(message)
        logger.debug(f"ON_MESSAGE: Finished processing DM for {message.author.name}.")
        return

    content = message.content.strip()
    if not content:
        logger.debug(f"ON_MESSAGE: Empty content after strip, ignoring.")
        return

    guild_config = get_guild_config(message.guild.id)
    active_bare_channels = guild_config.get("bare_command_active_channels", [])
    
    should_process_this_message_as_command = False 

    if message.channel.id in active_bare_channels and not content.startswith(COMMAND_PREFIX):
        logger.debug(f"ON_MESSAGE: Auto-channel detected for '{message.channel.id}', no prefix. Attempting bare command: '{content}'")
        parts = content.split(maxsplit=1) 
        command_candidate = parts[0].lower() # Chuyển lệnh tắt thành chữ thường

        if command_candidate in BARE_COMMAND_MAP: # So sánh với các key chữ thường trong map
            actual_command_name = BARE_COMMAND_MAP[command_candidate]
            args_for_bare_command = parts[1] if len(parts) > 1 else ""
            
            if bot.get_command(actual_command_name): 
                message.content = f"{COMMAND_PREFIX}{actual_command_name} {args_for_bare_command}".strip()
                should_process_this_message_as_command = True
                logger.info(f"ON_MESSAGE: Valid bare command '{command_candidate}' by {message.author.name}. Transformed to: '{message.content}'. Flagged for processing.")
            else:
                logger.warning(f"ON_MESSAGE: Bare command '{command_candidate}' maps to UNKNOWN prefix command '{actual_command_name}'. Ignoring.")
        else:
            if len(content.split()) <= 3: 
                 logger.debug(f"ON_MESSAGE: Potential invalid bare command '{command_candidate}' by {message.author.name} in auto-channel. Sending warning.")
                 await try_send(message.channel, content=f"{ICON_ERROR} Lệnh tắt `{command_candidate}` không hợp lệ hoặc không được hỗ trợ. Dùng `/menu` hoặc `{COMMAND_PREFIX}help`.")
            # else: logger.debug(f"ON_MESSAGE: Content '{content}' in auto-channel not a recognized bare command. Treating as normal chat.")
    
    elif content.startswith(COMMAND_PREFIX):
        logger.debug(f"ON_MESSAGE: Message from {message.author.name} has prefix '{COMMAND_PREFIX}'. Flagged for processing: '{message.content}'")
        should_process_this_message_as_command = True
    
    if should_process_this_message_as_command:
        logger.debug(f"ON_MESSAGE: FINAL DECISION - WILL CALL bot.process_commands for: '{message.content}' by {message.author.name}")
        await bot.process_commands(message)
        logger.debug(f"ON_MESSAGE: FINAL DECISION - FINISHED bot.process_commands for: '{message.content}' by {message.author.name}")
    # else: logger.debug(f"ON_MESSAGE: FINAL DECISION - Message '{content}' WILL NOT be processed as a command by {message.author.name}.")
