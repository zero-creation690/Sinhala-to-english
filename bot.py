import os
import logging
from pathlib import Path
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS
import tempfile
from pydub import AudioSegment

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot credentials
API_ID = 20288994
API_HASH = "d702614912f1ad370a0d18786002adbf"
BOT_TOKEN = "8062010233:AAExAW3Z-kpT17OTUXg0GQkCVsc7qnDUbXQ"
LOG_CHANNEL = -1002897456594
OWNER_ID = 8304706556

# Initialize bot
app = Client(
    "sinhala_dubbing_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Initialize translator
translator = Translator()

async def download_audio(message: Message) -> str:
    """Download audio/voice message from Telegram"""
    try:
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, "input_audio.ogg")
        await message.download(file_path)
        return file_path
    except Exception as e:
        logger.error(f"Error downloading audio: {e}")
        raise

def convert_to_wav(input_path: str) -> str:
    """Convert audio to WAV format for speech recognition"""
    try:
        audio = AudioSegment.from_file(input_path)
        wav_path = input_path.replace(".ogg", ".wav")
        audio.export(wav_path, format="wav")
        return wav_path
    except Exception as e:
        logger.error(f"Error converting audio: {e}")
        raise

def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio to English text"""
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="en-US")
            return text
    except sr.UnknownValueError:
        raise Exception("Could not understand the audio")
    except sr.RequestError as e:
        raise Exception(f"Speech recognition error: {e}")

def translate_to_sinhala(text: str) -> str:
    """Translate English text to Sinhala"""
    try:
        translation = translator.translate(text, src='en', dest='si')
        return translation.text
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise

def generate_sinhala_audio(text: str, output_path: str):
    """Generate Sinhala audio from text"""
    try:
        tts = gTTS(text=text, lang='si', slow=False)
        tts.save(output_path)
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise

async def process_audio(message: Message):
    """Main processing pipeline"""
    status_msg = await message.reply_text("🎧 Processing your audio...\n⏳ Step 1/4: Downloading...")
    
    try:
        # Step 1: Download audio
        audio_path = await download_audio(message)
        await status_msg.edit_text("🎧 Processing your audio...\n✅ Step 1/4: Downloaded\n⏳ Step 2/4: Transcribing...")
        
        # Step 2: Convert and transcribe
        wav_path = convert_to_wav(audio_path)
        english_text = transcribe_audio(wav_path)
        await status_msg.edit_text(
            f"🎧 Processing your audio...\n✅ Step 1/4: Downloaded\n✅ Step 2/4: Transcribed\n\n📝 English: {english_text}\n\n⏳ Step 3/4: Translating..."
        )
        
        # Step 3: Translate
        sinhala_text = translate_to_sinhala(english_text)
        await status_msg.edit_text(
            f"🎧 Processing your audio...\n✅ Step 1/4: Downloaded\n✅ Step 2/4: Transcribed\n✅ Step 3/4: Translated\n\n📝 English: {english_text}\n🇱🇰 Sinhala: {sinhala_text}\n\n⏳ Step 4/4: Generating audio..."
        )
        
        # Step 4: Generate Sinhala audio
        output_audio = audio_path.replace(".ogg", "_sinhala.mp3")
        generate_sinhala_audio(sinhala_text, output_audio)
        
        # Send dubbed audio
        await message.reply_voice(
            voice=output_audio,
            caption=f"🎙️ **Sinhala Dubbed Audio**\n\n📝 Original: {english_text}\n\n🇱🇰 Translation: {sinhala_text}"
        )
        
        await status_msg.delete()
        
        # Log to channel
        try:
            await app.send_message(
                LOG_CHANNEL,
                f"📊 **New Dubbing Request**\n\n👤 User: {message.from_user.mention}\n📝 English: {english_text}\n🇱🇰 Sinhala: {sinhala_text}"
            )
        except:
            pass
        
        # Cleanup
        for file in [audio_path, wav_path, output_audio]:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Processing error: {e}")
        await status_msg.edit_text(f"❌ Error: {str(e)}\n\nPlease try again with a clear English voice message.")

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    """Handle /start command"""
    await message.reply_text(
        "🤖 **English → Sinhala Dubbing Bot**\n\n"
        "Send me any English voice message and I'll dub it in Sinhala! 🎙️\n\n"
        "**How to use:**\n"
        "1️⃣ Record or send an English voice message\n"
        "2️⃣ Wait for processing (takes a few seconds)\n"
        "3️⃣ Receive your Sinhala dubbed audio! 🇱🇰\n\n"
        "**Features:**\n"
        "✅ Automatic speech recognition\n"
        "✅ English to Sinhala translation\n"
        "✅ Natural Sinhala voice synthesis\n"
        "✅ Fast processing\n\n"
        "Just send a voice message to get started! 🎧"
    )

@app.on_message(filters.voice | filters.audio)
async def handle_audio(client, message: Message):
    """Handle voice and audio messages"""
    await process_audio(message)

@app.on_message(filters.command("help"))
async def help_command(client, message: Message):
    """Handle /help command"""
    await message.reply_text(
        "📖 **How to Use This Bot**\n\n"
        "1️⃣ Send or record an English voice message\n"
        "2️⃣ The bot will:\n"
        "   • Transcribe your English audio\n"
        "   • Translate it to Sinhala\n"
        "   • Generate natural Sinhala audio\n"
        "3️⃣ You'll receive the dubbed version!\n\n"
        "**Tips for best results:**\n"
        "🎤 Speak clearly and at moderate pace\n"
        "🔇 Record in a quiet environment\n"
        "🗣️ Use simple, clear English\n\n"
        "**Commands:**\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n\n"
        "Have questions? Contact the owner! 💬"
    )

@app.on_message(filters.command("stats") & filters.user(OWNER_ID))
async def stats_command(client, message: Message):
    """Show bot statistics (owner only)"""
    await message.reply_text(
        "📊 **Bot Statistics**\n\n"
        "🤖 Status: Running\n"
        "✅ All systems operational\n\n"
        "Features:\n"
        "• Speech Recognition: Active\n"
        "• Translation: Active\n"
        "• TTS Generation: Active"
    )

def main():
    """Start the bot"""
    logger.info("Starting English → Sinhala Dubbing Bot...")
    app.run()

if __name__ == "__main__":
    main()
