import spotipy
from io import BytesIO
from spotipy.oauth2 import SpotifyOAuth
from time import sleep
from time import time
from PIL import Image, ImageDraw, ImageFont
import requests
import subprocess

CLIENT_ID="Client ID Here"
CLIENT_SECRET="Client Secret Here"

lastUrl = ""
lastSong = ""
LOCAL_PATH = "Path to this Folder"

def PrintException():
    print("error")

def getImg(url):
    res = requests.get(url)
    return Image.open(BytesIO(res.content))

def areSimilar(colors, dist):
    if abs(colors[0] - colors[1]) <= dist:
        return abs(colors[0] - colors[2]) <= dist
    return False

def isInRange(color1, color2, target):
    return abs(color1[0] - color2[0]) >= target or abs(color1[1] - color2[1]) >= target or abs(color1[2] - color2[2]) >= target

def sortSecond(val):
    return val[1]

def isBright(color, threshold):
    return color[0] > threshold or color[1] > threshold or color[2] > threshold

def getImgColor(img):
    try:
        colors = []
        pixels = img.load()
        width, height = img.size
        for y in range(round(height/5)):
            for x in range(round(width/5)):
                r, g, b = pixels[round(x*5), round(y*5)]
                curColors = [r, g, b]
                if len(colors) == 0 and isBright(curColors, 150):
                    colors.append([[r, g, b], 1])
                else:
                    count = 0
                    for i in range(len(colors)):
                        if isInRange(curColors, colors[i][0], 70):
                            count += 1
                        else: 
                            colors[i][1] += 1
                    if count == len(colors) and isBright(curColors, 90):
                        colors.append([[r, g, b], 1])
        colors.sort(key=sortSecond, reverse=True)
        if (len(colors) == 0): return (120, 120, 120)
        return colors[0][0]
    except Exception as e:
        PrintException()

def convertPixel(oldColor, newColor):
    returnColor = [0, 0, 0, 255]
    highest = 0
    highestIndex = 0
    for i in range(len(newColor)):
        if newColor[i] > highest:
            highestIndex = i
            highest = newColor[i]
    for i in range(len(newColor)):
        if i == highestIndex:
            returnColor[i] = oldColor[i]
        else:
            returnColor[i] = newColor[i]/(newColor[highestIndex]/oldColor[highestIndex])
    return returnColor

def changeWallpaper(url, smallUrl, songName, albumName, artistName, albumChange):
    startTime = time() 
    img = getImg(url)
    defaultImage = Image.open('./dualWallpaper/dualMonitorWallpaperNew.png')
    widthD, heightD = defaultImage.size
    widthI, heightI = img.size
    offsetHeight = (heightD / 2) - (heightI / 2)
    # div widthI by 2 if single monitor
    offsetWidth = (widthD / 2) -  (widthI) - 960
    pixels = img.load()
    color = getImgColor(getImg(smallUrl))
    print("finished setup in " + str(time() - startTime))
    
    W = 1500
    H = 1000
    tempImage = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ft = ImageFont.truetype('./fonts/bebas_neue/BebasNeue-Regular.ttf', 50)
    draw = ImageDraw.Draw(tempImage) 

    _, _, artistW, artistH = draw.textbbox((0, 0), artistName, font=ft)
    draw.text(((W-artistW) / 2, (H - artistH) / 2 + artistH), artistName, fill=(225, 225, 225), font=ft)

    _, _, songW, songH = draw.textbbox((0, 0), songName, font=ft)
    draw.text(((W-songW) / 2, (H - songH) / 2 - songH), songName, fill=(225, 225, 225), font=ft)

    _, _, albumW, albumH = draw.textbbox((0, 0), albumName, font=ft)
    draw.text(((W-albumW) / 2, (H - albumH) / 2), albumName, fill=(225, 225, 225), font=ft)
    tempImage = tempImage.rotate(-46, expand=1)
    rotW, rotH = tempImage.size
    defaultImage.paste(tempImage, (1920 + 1280 - round(rotW/2), round(1440/2) - round(rotH/2)), tempImage)
    rTest, gTest, bTest, aTest = defaultImage.split()
    rTest = rTest.point(lambda i: i * (color[0]/220))
    gTest = gTest.point(lambda i: i * (color[1]/220))
    bTest = bTest.point(lambda i: i * (color[2]/220))
    defaultImage = Image.merge('RGB', (rTest, gTest, bTest))
    print("finished color grade in " + str(time() - startTime))

    # add album cover to center of image
    savePixels = defaultImage.load()
    for x in range(widthI):
        for y in range(heightI):
            savePixels[x + offsetWidth, y + offsetHeight] = pixels[x, y]

    print("finished adding album cover in " + str(time() - startTime))

    defaultImage.save('wallpaperNew.jpg', compression_level=0)
    subprocess.call(["powershell.exe", '-ExecutionPolicy', 'Unrestricted', "-File", LOCAL_PATH + "wallpaperChange.ps1", LOCAL_PATH + "wallpaperNew.jpg"])
    print("Wallpaper Changed in " + str(time() - startTime))
    print("|---------------------|")

while True:
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                       client_secret=CLIENT_SECRET,
                                                       redirect_uri="http://localhost/redirect",
                                                       scope=["user-read-currently-playing", "user-read-playback-state"]))
        while True:
            songInfo = sp.current_user_playing_track()

            artists = songInfo["item"]["artists"]
            artistNames = []
            for i in range(len(artists)):
                artistNames.append(artists[i]["name"])
            artistName = ', '.join(artistNames)

            albumName = songInfo["item"]["album"]["name"]

            songName = songInfo["item"]["name"]

            albumCover = songInfo["item"]["album"]["images"]
            albumCoverUrl = albumCover[0]["url"]
            isPlaying = sp.current_playback()["is_playing"]
            if ((albumCoverUrl != lastUrl) or (songName != lastSong)) and isPlaying:
                changeWallpaper(albumCoverUrl, albumCover[2]["url"], songName, albumName, artistName, lastUrl != albumCoverUrl)
                lastUrl = albumCoverUrl
                lastSong = songName
            elif lastUrl != "paused" and not isPlaying:
                lastUrl = "paused"
                subprocess.call(["powershell.exe", '-ExecutionPolicy', 'Unrestricted', "-File", LOCAL_PATH + "wallpaperChange.ps1", LOCAL_PATH + "dualWallpaper/dualMonitorPaused.png"])
            sleep(0.8)
    except Exception as e:
        # print(e)
        if lastUrl != "paused":
            lastUrl = "paused"
            subprocess.call(["powershell.exe", '-ExecutionPolicy', 'Unrestricted', "-File", LOCAL_PATH + "wallpaperChange.ps1", LOCAL_PATH + "dualWallpaper/dualMonitorPaused.png"])
        pass
