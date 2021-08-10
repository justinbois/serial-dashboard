board_urls = [
    "https://raw.githubusercontent.com/arduino/ArduinoCore-avr/master/boards.txt",
    "https://raw.githubusercontent.com/arduino/ArduinoCore-samd/master/boards.txt",
    "https://raw.githubusercontent.com/sparkfun/Arduino_Boards/master/sparkfun/avr/boards.txt",
    "https://raw.githubusercontent.com/sparkfun/Arduino_Boards/master/sparkfun/samd/boards.txt",
    "https://git.ccmob.net/marcel/framework-arduino-samd-adafruit/-/raw/330cb4e652175b64ce4b0a7814cb1973768e0a09/boards.txt",
    "https://raw.githubusercontent.com/adafruit/Adafruit_Arduino_Boards/master/boards.txt",
]

vid_pid_boards = {
    "2341:0041": "Arduino Yún",
    "2341:8041": "Arduino Yún",
    "2A03:0041": "Arduino Yún",
    "2A03:8041": "Arduino Yún",
    "2341:0043": "Arduino Uno",
    "2341:0001": "Arduino Uno",
    "2A03:0043": "Arduino Uno",
    "2341:0243": "Arduino Uno",
    "2341:0010": "Arduino Mega, Duemilanove or Diecimila",
    "2341:0042": "Arduino Mega, Duemilanove or Diecimila",
    "2A03:0010": "Arduino Mega, Duemilanove or Diecimila",
    "2A03:0042": "Arduino Mega, Duemilanove or Diecimila",
    "2341:0210": "Arduino Mega, Duemilanove or Diecimila",
    "2341:0242": "Arduino Mega, Duemilanove or Diecimila",
    "2341:003f": "Arduino Mega ADK",
    "2341:0044": "Arduino Mega ADK",
    "2A03:003f": "Arduino Mega ADK",
    "2A03:0044": "Arduino Mega ADK",
    "2341:0036": "Arduino Leonardo",
    "2341:8036": "Arduino Leonardo",
    "2A03:0036": "Arduino Leonardo",
    "2A03:8036": "Arduino Leonardo",
    "2a03:0040": "Arduino Leonardo ETH",
    "2a03:8040": "Arduino Leonardo ETH",
    "2341:0037": "Arduino Micro",
    "2341:8037": "Arduino Micro",
    "2A03:0037": "Arduino Micro",
    "2A03:8037": "Arduino Micro",
    "2341:003C": "Arduino Esplora",
    "2341:803C": "Arduino Esplora",
    "2A03:003C": "Arduino Esplora",
    "2A03:803C": "Arduino Esplora",
    "1B4F:9207": "Arduino Mini",
    "1B4F:9208": "Arduino Mini",
    "2341:0038": "LilyPad Arduino",
    "2341:8038": "LilyPad Arduino",
    "2A03:0038": "LilyPad Arduino",
    "2A03:8038": "LilyPad Arduino",
    "2341:0039": "Arduino Robot Motor",
    "2341:8039": "Arduino Robot Motor",
    "2A03:0039": "Arduino Robot Motor",
    "2A03:8039": "Arduino Robot Motor",
    "239A:8011": "Either Arduino Gemma or Adafruit Feather 328P",
    "2a03:0050": "Arduino Yún Mini",
    "2a03:8050": "Arduino Yún Mini",
    "2a03:0056": "Arduino Industrial 101",
    "2a03:8056": "Arduino Industrial 101",
    "2a03:0001": "Linino One",
    "2a03:8001": "Linino One",
    "2A03:0057": "Arduino Uno WiFi",
    "2341:0237": "Arduino Micro",
    "2341:8237": "Arduino Micro",
    "03eb:2157": "Arduino Zero (Programming Port)",
    "2341:804d": "Arduino Zero (Native USB Port)",
    "2341:004d": "Arduino Zero (Native USB Port)",
    "2341:824d": "Arduino Zero (Native USB Port)",
    "2341:024d": "Arduino Zero (Native USB Port)",
    "2341:804e": "Arduino MKR1000",
    "2341:004e": "Arduino MKR1000",
    "2341:824e": "Arduino MKR1000",
    "2341:024e": "Arduino MKR1000",
    "2341:804f": "Arduino MKRZERO",
    "2341:004f": "Arduino MKRZERO",
    "2341:8054": "Arduino MKR WiFi 1010",
    "2341:0054": "Arduino MKR WiFi 1010",
    "2341:8057": "Arduino NANO 33 IoT",
    "2341:0057": "Arduino NANO 33 IoT",
    "2341:8050": "Arduino MKR FOX 1200",
    "2341:0050": "Arduino MKR FOX 1200",
    "2341:8053": "Arduino MKR WAN 1300",
    "2341:0053": "Arduino MKR WAN 1300",
    "2341:8059": "Arduino MKR WAN 1310",
    "2341:0059": "Arduino MKR WAN 1310",
    "2341:8052": "Arduino MKR GSM 1400",
    "2341:0052": "Arduino MKR GSM 1400",
    "2341:8055": "Arduino MKR NB 1500",
    "2341:0055": "Arduino MKR NB 1500",
    "2341:8056": "Arduino MKR Vidor 4000",
    "2341:0056": "Arduino MKR Vidor 4000",
    "239A:8018": "Adafruit Circuit Playground Express",
    "239A:0018": "Adafruit Circuit Playground Express",
    "03eb:2111": "Arduino M0 Pro (Programming Port)",
    "2a03:004d": "Arduino M0 Pro (Native USB Port)",
    "2a03:804d": "Arduino M0 Pro (Native USB Port)",
    "2a03:004f": "Arduino M0 Pro (Native USB Port)",
    "2a03:804f": "Arduino M0 Pro (Native USB Port)",
    "2a03:004e": "Arduino M0",
    "2a03:804e": "Arduino M0",
    "10C4:EA70": "Arduino Tian (MIPS Console port)",
    "1B4F:2B74": "SparkFun RedBoard",
    "1B4F:2B75": "SparkFun RedBoard",
    "1B4F:F100": "SparkFun Pro Micro",
    "1B4F:F101": "SparkFun Pro Micro",
    "1B4F:514D": "Qduino Mini",
    "1B4F:516D": "Qduino Mini",
    "1B4F:0110": "SparkFun Digital Sandbox",
    "1B4F:8D21": "SparkFun SAMD21 Pro RF 1W",
    "1B4F:0D21": "SparkFun SAMD21 Mini Breakout",
    "1B4F:0100": "LilyPad LilyMini",
    "1B4F:0101": "LilyPad LilyMini",
    "1B4F:9D0E": "SparkFun 9DoF Razor IMU M0",
    "1B4F:9D0F": "SparkFun 9DoF Razor IMU M0",
    "1B4F:214F": "SparkFun SAMD21 Pro RF",
    "1B4F:215F": "SparkFun SAMD21 Pro RF",
    "1B4F:3ABA": "SparkFun SAMD21 Pro RF 1W",
    "1B4F:0015": "SparkFun RedBoard Turbo",
    "1B4F:F015": "SparkFun RedBoard Turbo",
    "1B4F:0016": "SparkFun SAMD51 Thing Plus",
    "1B4F:F016": "SparkFun SAMD51 Thing Plus",
    "1B4F:0019": "SparkFun Qwiic Micro",
    "1B4F:F019": "SparkFun Qwiic Micro",
    "1B4F:0020": "SparkFun SAMD51 MicroMod",
    "1B4F:F020": "SparkFun SAMD51 MicroMod",
    "239A:800B": "Adafruit Feather M0",
    "239A:000B": "Adafruit Feather M0",
    "239A:0015": "Adafruit Feather M0",
    "239A:801B": "Adafruit Feather M0 Express",
    "239A:001B": "Adafruit Feather M0 Express",
    "239A:8014": "Adafruit M0 Radio (Native USB Port)",
    "239A:0014": "Adafruit M0 Radio (Native USB Port)",
    "239A:8013": "Adafruit Metro M0 Express",
    "239A:0013": "Adafruit Metro M0 Express",
    "239A:0019": "Adafruit Circuit Playground Express",
    "239A:801C": "Adafruit Gemma M0",
    "239A:001C": "Adafruit Gemma M0",
    "239A:801E": "Adafruit Trinket M0",
    "239A:001E": "Adafruit Trinket M0",
    "239A:800F": "Adafruit ItsyBitsy M0",
    "239A:000F": "Adafruit ItsyBitsy M0",
    "239A:8012": "Adafruit ItsyBitsy M0",
    "239A:DEAD": "Adafruit Hallowing M0",
    "239A:D1ED": "Adafruit Hallowing M0",
    "239A:B000": "Adafruit Hallowing M0",
    "239A:802D": "Adafruit Crickit M0",
    "239A:002D": "Adafruit Crickit M0",
    "239A:8020": "Adafruit Metro M4 (SAMD51)",
    "239A:0020": "Adafruit Metro M4 (SAMD51)",
    "239A:8031": "Adafruit Grand Central M4 (SAMD51)",
    "239A:0031": "Adafruit Grand Central M4 (SAMD51)",
    "239A:0032": "Adafruit Grand Central M4 (SAMD51)",
    "239A:802B": "Adafruit ItsyBitsy M4 (SAMD51)",
    "239A:002B": "Adafruit ItsyBitsy M4 (SAMD51)",
    "239A:8022": "Adafruit Feather M4 Express (SAMD51)",
    "239A:0022": "Adafruit Feather M4 Express (SAMD51)",
    "239A:802F": "Adafruit Trellis M4 (SAMD51)",
    "239A:002F": "Adafruit Trellis M4 (SAMD51)",
    "239A:0030": "Adafruit Trellis M4 (SAMD51)",
    "239A:8035": "Adafruit PyPortal M4 (SAMD51)",
    "239A:0035": "Adafruit PyPortal M4 (SAMD51)",
    "239A:8053": "Adafruit PyPortal M4 Titano (SAMD51)",
    "239A:8033": "Adafruit pyBadge M4 Express (SAMD51)",
    "239A:0033": "Adafruit pyBadge M4 Express (SAMD51)",
    "239A:8037": "Adafruit Metro M4 AirLift Lite (SAMD51)",
    "239A:0037": "Adafruit Metro M4 AirLift Lite (SAMD51)",
    "239A:803D": "Adafruit PyGamer M4 Express (SAMD51)",
    "239A:003D": "Adafruit PyGamer M4 Express (SAMD51)",
    "239A:803E": "Adafruit PyGamer M4 Express (SAMD51)",
    "239A:8041": "Adafruit PyGamer Advance M4 (SAMD51)",
    "239A:0041": "Adafruit PyGamer Advance M4 (SAMD51)",
    "239A:8042": "Adafruit PyGamer Advance M4 (SAMD51)",
    "239A:8043": "Adafruit pyBadge AirLift M4 (SAMD51)",
    "239A:8047": "Adafruit MONSTER M4SK (SAMD51)",
    "239A:0047": "Adafruit MONSTER M4SK (SAMD51)",
    "239A:8048": "Adafruit MONSTER M4SK (SAMD51)",
    "239A:8049": "Adafruit Hallowing M4 (SAMD51)",
    "239A:0049": "Adafruit Hallowing M4 (SAMD51)",
    "239A:804A": "Adafruit Hallowing M4 (SAMD51)",
    "239A:8004": "Adafruit Flora",
    "239A:800C": "Adafruit Feather 32u4",
    "239A:000E": "Adafruit ItsyBitsy 32u4 5V 16MHz",
    "239A:000D": "Adafruit ItsyBitsy 32u4 3V 8MHz",
    "239A:800A": "Adafruit Bluefruit Micro",
    "239A:8001": "Adafruit 32u4 Breakout",
    "16C0:0483": "Teensy 4.0",
}


def fetch_boards_file(url):
    """Fetch a boards.txt configuration file from a URL.

    Parameters
    ----------
    url : str
        URL from which to request boards.txt file.

    Returns
    -------
    output : list of strs or None
        If successful, returns a list of strings containing the lines
        of the boards.txt file. If unsuccessful, returns None.
    """
    try:
        f = requests.get(url)
        return f.text.split("\n")
    except:
        return None


def known_boards(boards_files):
    """Generate dictionary of known boards from boards.txt files.

    Parameters
    ----------
    boards_files : list of strs
        List of boards.txt files that contain VID and PIDs of boards

    Returns
    -------
    output : dict
        Dictionary where each key is a string representing VID:PID and
        each value if a string with the name of the corresponding board.
    """
    # Adjust inputted boards files for convenience
    if type(boards_files) == str:
        boards_files = [boards_files]
    elif boards_files is None:
        boards_files = []
    elif type(boards_files) == tuple:
        boards_files = list(boards_files)
    else:
        raise RuntimeError("Erroneous input of `boards_files`.")

    # Convert file content to text
    boards_txt = []
    for board in boards_files:
        with open(board, "r") as f:
            boards_txt.append(f.readlines())

    # Read in Arduino, Sparkfun, and Adafruit boards
    for board_url in board_urls:
        txt = fetch_boards_file(board_url)
        if txt is not None:
            boards_txt.append(txt)

    boards = {}

    for lines in boards_txt:
        i = 0
        while i < len(lines):
            while i < len(lines) and ".name" not in lines[i]:
                i += 1

            if i < len(lines):
                name = lines[i][lines[i].rfind("=") + 1 :].rstrip()

            while i < len(lines) and "vid." not in lines[i]:
                i += 1

            while i < len(lines) and ("vid" in lines[i] or "pid" in lines[i]):
                vid = lines[i][lines[i].rfind("x") + 1 :].rstrip()
                i += 1
                pid = lines[i][lines[i].rfind("x") + 1 :].rstrip()
                vid_pid = vid + ":" + pid
                if vid_pid in boards:
                    if type(boards[vid_pid]) == list:
                        if vid_pid not in boards[vid_pid]:
                            boards[vid_pid].append(name)
                    elif boards[vid_pid] != name:
                        boards[vid_pid] = [boards[vid_pid], name]
                else:
                    boards[vid_pid] = name

                i += 1

    return boards
