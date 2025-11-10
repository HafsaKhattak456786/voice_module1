import streamlit as st
from gtts import gTTS
import speech_recognition as sr
import os
import random
import time
import threading
from io import BytesIO
import queue

# ---------------------------
# Data
# ---------------------------
braille_alphabet = {
    "A": {"dots": "dot 1", "pattern": ["●", "○", "○", "○", "○", "○"]},
    "B": {"dots": "dots 1 and 2", "pattern": ["●", "●", "○", "○", "○", "○"]},
    "C": {"dots": "dots 1 and 4", "pattern": ["●", "○", "○", "●", "○", "○"]},
    "D": {"dots": "dots 1, 4 and 5", "pattern": ["●", "○", "○", "●", "●", "○"]},
    "E": {"dots": "dots 1 and 5", "pattern": ["●", "○", "○", "○", "●", "○"]},
    "F": {"dots": "dots 1, 2 and 4", "pattern": ["●", "●", "○", "●", "○", "○"]},
    "G": {"dots": "dots 1, 2, 4 and 5", "pattern": ["●", "●", "○", "●", "●", "○"]},
    "H": {"dots": "dots 1, 2 and 5", "pattern": ["●", "●", "○", "○", "●", "○"]},
    "I": {"dots": "dots 2 and 4", "pattern": ["○", "●", "○", "●", "○", "○"]},
    "J": {"dots": "dots 2, 4 and 5", "pattern": ["○", "●", "○", "●", "●", "○"]},
    "K": {"dots": "dots 1 and 3", "pattern": ["●", "○", "●", "○", "○", "○"]},
    "L": {"dots": "dots 1, 2 and 3", "pattern": ["●", "●", "●", "○", "○", "○"]},
    "M": {"dots": "dots 1, 3 and 4", "pattern": ["●", "○", "●", "●", "○", "○"]},
    "N": {"dots": "dots 1, 3, 4 and 5", "pattern": ["●", "○", "●", "●", "●", "○"]},
    "O": {"dots": "dots 1, 3 and 5", "pattern": ["●", "○", "●", "○", "●", "○"]},
    "P": {"dots": "dots 1, 2, 3 and 4", "pattern": ["●", "●", "●", "●", "○", "○"]},
    "Q": {"dots": "dots 1, 2, 3, 4 and 5", "pattern": ["●", "●", "●", "●", "●", "○"]},
    "R": {"dots": "dots 1, 2, 3 and 5", "pattern": ["●", "●", "●", "○", "●", "○"]},
    "S": {"dots": "dots 2, 3 and 4", "pattern": ["○", "●", "●", "●", "○", "○"]},
    "T": {"dots": "dots 2, 3, 4 and 5", "pattern": ["○", "●", "●", "●", "●", "○"]},
    "U": {"dots": "dots 1, 3 and 6", "pattern": ["●", "○", "●", "○", "○", "●"]},
    "V": {"dots": "dots 1, 2, 3 and 6", "pattern": ["●", "●", "●", "○", "○", "●"]},
    "W": {"dots": "dots 2, 4, 5 and 6", "pattern": ["○", "●", "○", "●", "●", "●"]},
    "X": {"dots": "dots 1, 3, 4 and 6", "pattern": ["●", "○", "●", "●", "○", "●"]},
    "Y": {"dots": "dots 1, 3, 4, 5 and 6", "pattern": ["●", "○", "●", "●", "●", "●"]},
    "Z": {"dots": "dots 1, 3, 5 and 6", "pattern": ["●", "○", "●", "○", "●", "●"]}
}

braille_numbers = {
    "1": {"dots": "same as letter A, dot 1", "pattern": ["●", "○", "○", "○", "○", "○"]},
    "2": {"dots": "same as letter B, dots 1 and 2", "pattern": ["●", "●", "○", "○", "○", "○"]},
    "3": {"dots": "same as letter C, dots 1 and 4", "pattern": ["●", "○", "○", "●", "○", "○"]},
    "4": {"dots": "same as letter D, dots 1, 4 and 5", "pattern": ["●", "○", "○", "●", "●", "○"]},
    "5": {"dots": "same as letter E, dots 1 and 5", "pattern": ["●", "○", "○", "○", "●", "○"]},
    "6": {"dots": "same as letter F, dots 1, 2 and 4", "pattern": ["●", "●", "○", "●", "○", "○"]},
    "7": {"dots": "same as letter G, dots 1, 2, 4 and 5", "pattern": ["●", "●", "○", "●", "●", "○"]},
    "8": {"dots": "same as letter H, dots 1, 2 and 5", "pattern": ["●", "●", "○", "○", "●", "○"]},
    "9": {"dots": "same as letter I, dots 2 and 4", "pattern": ["○", "●", "○", "●", "○", "○"]},
    "0": {"dots": "same as letter J, dots 2, 4 and 5", "pattern": ["○", "●", "○", "●", "●", "○"]}
}

# Voice commands mapping
VOICE_COMMANDS = {
    "introduction": ["introduction", "intro", "start", "begin", "welcome", "main menu", "home", "menu"],
    "rules": ["rules", "basic rules", "rule", "how does braille work", "explain rules"],
    "grid": ["grid", "cell", "structure", "layout", "show grid"],
    "alphabet": ["alphabet", "letters", "learn alphabet", "show alphabet", "letter"],
    "numbers": ["numbers", "digits", "learn numbers", "show numbers", "number"],
    "help": ["help", "commands", "what can I say", "voice commands"],
    "repeat": ["repeat", "say again", "once more", "again"],
    "next": ["next", "continue", "next lesson", "forward"],
    "previous": ["previous", "back", "go back", "last lesson", "backward"],
    "main_menu": ["main menu", "go to main menu", "home", "return to start"]
}

# ---------------------------
# Session State Initialization
# ---------------------------
if 'current_lesson' not in st.session_state:
    st.session_state.current_lesson = "introduction"
if 'last_spoken_text' not in st.session_state:
    st.session_state.last_spoken_text = ""
if 'alphabet_lesson_index' not in st.session_state:
    st.session_state.alphabet_lesson_index = 0
if 'lesson_content_spoken' not in st.session_state:
    st.session_state.lesson_content_spoken = False
if 'auto_play_enabled' not in st.session_state:
    st.session_state.auto_play_enabled = True
if 'last_command_time' not in st.session_state:
    st.session_state.last_command_time = 0

# ---------------------------
# Helper Functions
# ---------------------------
def speak(text, auto_play=None):
    """Generate speech with gTTS and play in Streamlit"""
    if auto_play is None:
        auto_play = st.session_state.auto_play_enabled
    
    st.session_state.last_spoken_text = text
    try:
        tts = gTTS(text, lang='en', slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        st.audio(fp, format="audio/mp3", autoplay=auto_play)
        return text
    except Exception as e:
        st.error(f"Speech generation failed: {e}")
        return text

def create_braille_grid(pattern, letter=""):
    """Create visual braille grid representation with high contrast"""
    dots = pattern if isinstance(pattern, list) else ["○", "○", "○", "○", "○", "○"]
    
    # Convert symbols to high contrast
    display_dots = []
    for dot in dots:
        if dot == "●":
            display_dots.append("🔵")  # Blue filled circle for raised dots
        else:
            display_dots.append("⬜")   # White square for empty positions
    
    grid_html = f"""
    <div style="text-align: center; margin: 15px; padding: 15px; background-color: #ffffff; border: 4px solid #000000; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);">
        <h3 style="margin-bottom: 15px; color: #000000; font-weight: bold; font-size: 18px;">{letter}</h3>
        <div style="display: inline-block; background-color: #f0f0f0; border: 3px solid #333; padding: 20px; border-radius: 12px;">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 32px;">
                <div style="text-align: center; padding: 5px;">{display_dots[0]}</div>
                <div style="text-align: center; padding: 5px;">{display_dots[3]}</div>
                <div style="text-align: center; padding: 5px;">{display_dots[1]}</div>
                <div style="text-align: center; padding: 5px;">{display_dots[4]}</div>
                <div style="text-align: center; padding: 5px;">{display_dots[2]}</div>
                <div style="text-align: center; padding: 5px;">{display_dots[5]}</div>
            </div>
            <div style="font-size: 16px; margin-top: 12px; color: #000; font-weight: bold; font-family: monospace;">
                <div style="margin-bottom: 3px;">1&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;4</div>
                <div style="margin-bottom: 3px;">2&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;5</div>
                <div>3&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;6</div>
            </div>
        </div>
    </div>
    """
    return grid_html

def listen_for_voice():
    """Listen for a single voice command"""
    try:
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        
        with sr.Microphone() as source:
            st.info("🎤 Listening... Please speak now!")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            # Listen for audio
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=6)
            
        st.info("Processing your command...")
        command = recognizer.recognize_google(audio).lower()
        
        if command:
            st.success(f"✅ Heard: '{command}'")
            return command
        else:
            st.warning("No command detected")
            return None
            
    except sr.WaitTimeoutError:
        st.warning("⏰ Timeout - No speech detected")
        return None
    except sr.UnknownValueError:
        st.warning("🤔 Could not understand the speech")
        return None
    except sr.RequestError as e:
        st.error(f"❌ Speech service error: {e}")
        return None
    except Exception as e:
        st.error(f"❌ Microphone error: {e}")
        return None

def process_voice_command(command):
    """Process the voice command and return appropriate action"""
    if not command:
        return None
    
    command = command.lower().strip()
    
    # Check each command category
    for action, keywords in VOICE_COMMANDS.items():
        for keyword in keywords:
            if keyword in command:
                return action
    
    # Check for specific alphabet lesson requests
    if "lesson" in command:
        try:
            words = command.split()
            for i, word in enumerate(words):
                if word == "lesson" and i + 1 < len(words):
                    try:
                        lesson_num = int(words[i + 1])
                        if 1 <= lesson_num <= 9:
                            st.session_state.alphabet_lesson_index = lesson_num - 1
                            return "alphabet"
                    except:
                        continue
        except:
            pass
    
    return "unknown"

def execute_voice_command(action):
    """Execute the voice command action"""
    current_time = time.time()
    
    # Prevent rapid command execution
    if current_time - st.session_state.last_command_time < 1:
        return False
    
    st.session_state.last_command_time = current_time
    
    if action == "repeat" and st.session_state.last_spoken_text:
        speak(st.session_state.last_spoken_text)
        return False
    elif action == "next" and st.session_state.current_lesson == "alphabet":
        if st.session_state.alphabet_lesson_index < 8:
            st.session_state.alphabet_lesson_index += 1
            st.session_state.lesson_content_spoken = False
            return True
        else:
            speak("This is the last alphabet lesson")
            return False
    elif action == "previous" and st.session_state.current_lesson == "alphabet":
        if st.session_state.alphabet_lesson_index > 0:
            st.session_state.alphabet_lesson_index -= 1
            st.session_state.lesson_content_spoken = False
            return True
        else:
            speak("This is the first alphabet lesson")
            return False
    elif action in ["introduction", "rules", "grid", "alphabet", "numbers", "help", "main_menu"]:
        if action == "main_menu":
            action = "introduction"
        
        if action != st.session_state.current_lesson:
            st.session_state.current_lesson = action
            st.session_state.lesson_content_spoken = False
            return True
        else:
            # Same lesson, just repeat
            st.session_state.lesson_content_spoken = False
            return True
    elif action == "unknown":
        speak("Sorry, I didn't understand that command. Say 'help' to hear available commands.")
        return False
    
    return False

def get_voice_help():
    """Return help text for voice commands"""
    return """
    Voice Commands Available:
    
    Navigation:
    • "Introduction" or "Main Menu" - Go to start
    • "Rules" - Learn basic Braille rules
    • "Grid" - See the Braille cell structure
    • "Alphabet" - Learn letters with visual grids
    • "Numbers" - Learn digits with visual grids
    
    Controls:
    • "Next" - Go to next lesson (in alphabet)
    • "Previous" - Go to previous lesson (in alphabet)
    • "Repeat" - Hear current content again
    • "Help" - Hear this menu
    
    Special:
    • "Lesson 1", "Lesson 2", etc. - Jump to specific alphabet lesson
    
    Visual Guide: Blue circles show raised dots, white squares show empty positions.
    This app works for both sighted and blind users.
    """

# ---------------------------
# Lessons
# ---------------------------
def introduction():
    return """Welcome to the Voice-Driven Braille Learning System.
    This app works for both sighted and blind users.
    
    Braille is a system of raised dots that can be felt with the fingers.
    It was invented by Louis Braille in 1824 to help the blind read and write.
    
    Available lessons: Say Rules, Grid, Alphabet, Numbers, or Help.
    You can also use the buttons if you prefer visual navigation."""

def braille_rules():
    return """Each Braille cell has six dot positions, arranged in two columns of three.
    Dots are numbered from top to bottom, left to right.
    Left column is dots 1, 2, 3. Right column is dots 4, 5, 6.
    
    In the visual display: Blue circles show raised dots you can feel. 
    White squares show empty positions with no dots.
    
    Say Grid to see the structure, Alphabet to learn letters, or Main Menu to go back."""

def braille_grid_demo():
    return """This is the BRAILLE CELL structure: 
    The cell is a 2 by 3 grid with 6 positions.
    Position 1 is top-left, position 4 is top-right.
    Position 2 is middle-left, position 5 is middle-right.
    Position 3 is bottom-left, position 6 is bottom-right.
    
    Visual guide: Blue circles show raised dots. White squares show empty positions.
    All Braille letters and numbers use combinations of these 6 positions.
    
    Say Alphabet to learn letters, or Main Menu to go back."""

def alphabet_lessons():
    lessons = []
    letters = list(braille_alphabet.items())
    for i in range(0, len(letters), 3):
        group = letters[i:i+3]
        lesson_text = f"Alphabet Lesson {i//3 + 1} of {len(letters)//3 + 1}. "
        lesson_text += " ".join([f"Letter {letter} uses {data['dots']}." for letter, data in group])
        lesson_text += " Say Next for next lesson, Previous to go back, or Repeat to hear again."
        lessons.append((lesson_text, group))
    return lessons

def numbers_lesson():
    text = """Numbers in Braille use the same patterns as letters A to J.
    Before writing any number, you must add the number sign, which uses dots 3, 4, 5, and 6.
    
    Visual guide: Blue circles show raised dots. White squares show empty positions.
    Here are the numbers: """
    
    number_list = []
    for num, data in braille_numbers.items():
        text += f"Number {num} uses {data['dots']}. "
        number_list.append((num, data))
    
    text += "You can see all visual grids below. Say Main Menu to return to start."
    return text, number_list

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(
    page_title="Voice-Driven Braille Learning System", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🎤📘 Voice-Driven Braille Learning System")
st.markdown("### **Accessible for Both Sighted and Blind Users**")

# Voice Input Section (Prominent)
st.markdown("---")
st.markdown("## 🎤 Voice Control")

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    if st.button("🎤 **LISTEN FOR VOICE COMMAND**", key="voice_listen", use_container_width=True):
        command = listen_for_voice()
        if command:
            action = process_voice_command(command)
            if action:
                needs_rerun = execute_voice_command(action)
                if needs_rerun:
                    time.sleep(0.5)  # Small delay for better UX
                    st.rerun()

with col2:
    if st.button("🔄 Repeat", key="repeat_btn"):
        if st.session_state.last_spoken_text:
            speak(st.session_state.last_spoken_text)

with col3:
    if st.button("🏠 Home", key="home_btn"):
        st.session_state.current_lesson = "introduction"
        st.session_state.lesson_content_spoken = False
        st.rerun()

# Sidebar Controls for Visual Navigation
with st.sidebar:
    st.header("📱 Visual Navigation")
    st.markdown("*For sighted users*")
    
    # Audio Control
    st.session_state.auto_play_enabled = st.checkbox("Auto-play Audio", value=st.session_state.auto_play_enabled)
    
    # Manual Navigation
    st.subheader("Quick Navigation")
    lesson_choice = st.selectbox(
        "Choose Lesson:",
        ["introduction", "rules", "grid", "alphabet", "numbers", "help"],
        index=["introduction", "rules", "grid", "alphabet", "numbers", "help"].index(st.session_state.current_lesson),
        key="lesson_selector"
    )
    
    if lesson_choice != st.session_state.current_lesson:
        st.session_state.current_lesson = lesson_choice
        st.session_state.lesson_content_spoken = False
        st.rerun()

# Current lesson indicator
st.markdown(f"**📍 Current Lesson: {st.session_state.current_lesson.replace('_', ' ').title()}**")

# Voice Commands Reference
with st.expander("🎤 Voice Commands Reference", expanded=False):
    st.markdown("""
    **Navigation Commands:**
    - "Introduction" or "Main Menu" → Go to start
    - "Rules" → Learn Braille basics
    - "Grid" → See cell structure
    - "Alphabet" → Learn letters
    - "Numbers" → Learn digits
    
    **Control Commands:**
    - "Next" → Next lesson (in alphabet)
    - "Previous" → Previous lesson (in alphabet)  
    - "Repeat" → Hear current content again
    - "Help" → Hear all commands
    
    **Special Commands:**
    - "Lesson 1", "Lesson 2", etc. → Jump to specific alphabet lesson
    """)

# Main Content Display
st.markdown("---")

if st.session_state.current_lesson == "introduction":
    text = introduction()
    st.markdown("### 🏠 Welcome")
    st.write(text)
    if not st.session_state.lesson_content_spoken:
        speak(text)
        st.session_state.lesson_content_spoken = True

elif st.session_state.current_lesson == "rules":
    text = braille_rules()
    st.markdown("### 📋 Braille Rules")
    st.write(text)
    if not st.session_state.lesson_content_spoken:
        speak(text)
        st.session_state.lesson_content_spoken = True

elif st.session_state.current_lesson == "grid":
    text = braille_grid_demo()
    st.markdown("### 🔢 Braille Grid Structure")
    st.write(text)
    
    # Show empty grid with high contrast
    empty_grid = create_braille_grid(["○", "○", "○", "○", "○", "○"], "Empty Braille Cell")
    st.markdown(empty_grid, unsafe_allow_html=True)
    
    st.markdown("### **Visual Guide for All Users:**")
    st.markdown("- 🔵 **Blue circles** = Raised dots (tactile bumps)")
    st.markdown("- ⬜ **White squares** = Empty positions (flat surface)")
    st.markdown("- **Layout:** Left column (1,2,3) | Right column (4,5,6)")
    
    if not st.session_state.lesson_content_spoken:
        speak(text)
        st.session_state.lesson_content_spoken = True

elif st.session_state.current_lesson == "alphabet":
    st.markdown("### 🔤 Alphabet Lessons with Visual Grids")
    lessons = alphabet_lessons()
    
    current_idx = st.session_state.alphabet_lesson_index
    if current_idx < len(lessons):
        text, group = lessons[current_idx]
        st.write(f"**Lesson {current_idx + 1} of {len(lessons)}**")
        st.write(text)
        
        # Display visual grids for this lesson
        cols = st.columns(3)
        for i, (letter, data) in enumerate(group):
            with cols[i]:
                grid_html = create_braille_grid(data['pattern'], f"Letter {letter}")
                st.markdown(grid_html, unsafe_allow_html=True)
                st.markdown(f"**{letter}:** {data['dots']}")
        
        st.markdown("### **Visual Guide:**")
        st.markdown("- 🔵 **Blue circles** = Raised dots")
        st.markdown("- ⬜ **White squares** = Empty positions")
        
        if not st.session_state.lesson_content_spoken:
            speak(text)
            st.session_state.lesson_content_spoken = True
        
        # Navigation buttons for visual users
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ Previous", key="prev_alphabet", disabled=(current_idx == 0)):
                st.session_state.alphabet_lesson_index -= 1
                st.session_state.lesson_content_spoken = False
                st.rerun()
        with col2:
            st.write(f"**Lesson {current_idx + 1} of {len(lessons)}**")
        with col3:
            if st.button("➡️ Next", key="next_alphabet", disabled=(current_idx == len(lessons) - 1)):
                st.session_state.alphabet_lesson_index += 1
                st.session_state.lesson_content_spoken = False
                st.rerun()

elif st.session_state.current_lesson == "numbers":
    st.markdown("### 🔢 Numbers in Braille with Visual Grids")
    text, number_list = numbers_lesson()
    st.write(text)
    
    # Display number sign first
    st.markdown("### Number Sign (Required before any number):")
    number_sign_pattern = ["○", "○", "●", "●", "●", "●"]  # dots 3,4,5,6
    number_sign_grid = create_braille_grid(number_sign_pattern, "Number Sign")
    st.markdown(number_sign_grid, unsafe_allow_html=True)
    st.markdown("**Number Sign:** dots 3, 4, 5, and 6")
    
    st.markdown("### Numbers 0-9:")
    # Display numbers in rows of 5
    for i in range(0, len(number_list), 5):
        cols = st.columns(5)
        for j, col in enumerate(cols):
            if i + j < len(number_list):
                num, data = number_list[i + j]
                with col:
                    grid_html = create_braille_grid(data['pattern'], f"Number {num}")
                    st.markdown(grid_html, unsafe_allow_html=True)
                    st.markdown(f"**{num}:** {data['dots'][:25]}...")
    
    st.markdown("### **Visual Guide:**")
    st.markdown("- 🔵 **Blue circles** = Raised dots")
    st.markdown("- ⬜ **White squares** = Empty positions")
    
    if not st.session_state.lesson_content_spoken:
        speak(text)
        st.session_state.lesson_content_spoken = True

elif st.session_state.current_lesson == "help":
    help_text = get_voice_help()
    st.markdown("### ❓ Voice Commands Help")
    st.info(help_text)
    if not st.session_state.lesson_content_spoken:
        speak(help_text)
        st.session_state.lesson_content_spoken = True

# Footer with important info
st.markdown("---")
st.markdown("### 💡 **How to Use This App**")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**🎤 For Voice Control:**")
    st.markdown("1. Click the blue 'LISTEN FOR VOICE COMMAND' button")
    st.markdown("2. Wait for 'Listening...' message")
    st.markdown("3. Speak clearly: 'Rules', 'Alphabet', 'Next', etc.")
    st.markdown("4. Wait for confirmation and navigation")

with col2:
    st.markdown("**👀 For Visual Control:**")
    st.markdown("1. Use the sidebar dropdown to select lessons")
    st.markdown("2. Click navigation buttons (Previous/Next)")
    st.markdown("3. Use 'Repeat' and 'Home' buttons as needed")
    st.markdown("4. Toggle auto-play audio on/off")

# Status information
status_text = f"📍 **Status:** {st.session_state.current_lesson.replace('_', ' ').title()}"
if st.session_state.current_lesson == "alphabet":
    status_text += f" | Lesson {st.session_state.alphabet_lesson_index + 1} of 9"
st.markdown(status_text)