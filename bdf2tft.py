import sys          #Allows reading CLI arguments
import re

if len(sys.argv) < 2:
    print("USAGE: " + sys.argv[0] + " BDF filename without extension")
    exit
fontname = sys.argv[1]

bdf = open(fontname + ".bdf", 'r')
lines = bdf.readlines()


#LUT: each char can reference another in its bitmap, or have forced width, or have lines added on top
#To: Use bitmap from char ... / RL: Remove ... Lines / FW: Force width to
#compressCharTo = 
#compressCharRL = 
#compressCharFW = 
downhang = 1

bitmapData = "const uint8_t " + fontname + "_Bitmap[] PROGMEM = {\n\t// Bitmap Data:"     
#Cache for the first array in the H file
indexData = "const GFXglyph " + fontname + "_Glyphs[] PROGMEM = {\n	// bitmap  wid  hei  x    x    y\n  // Offset, th , ght, Adv, Ofs, Ofs"      
#Cache for the second array in the H file

onBitmapLine = 0
getpixsize = re.compile(r'PIXEL_SIZE (\-?\d+)')
getcharnum = re.compile(r'ENCODING (\-?\d+)')
getName = re.compile(r'STARTCHAR (.*)')
getWidth = re.compile(r'DWIDTH (\-?\d+) .*')
getBBX = re.compile(r'BBX (\-?\d+) (\-?\d+) (\-?\d+) (\-?\d+)')
startBitmap = re.compile(r'BITMAP')
endBitmap = re.compile(r'END')
binaryIndex = 0

charnum = 0
oldcharnum = 0
firstcharnum = 0
charName = ""
advance = 0
BBX_w = 0
BBX_h = 0
BBX_x = 0
BBX_y = 0

binaryChar = ""
fillCharUsed = False

for line in lines:
    if getpixsize.match(line):
        pixsize = getpixsize.search(line).group(1)
    
    if getcharnum.match(line):
        charnum = int(getcharnum.search(line).group(1))
        if oldcharnum == 0:
            firstcharnum = oldcharnum = charnum
        if oldcharnum != charnum:
            for i in range(int(oldcharnum)+1, int(charnum)):       #fill gap between non-consecutive chars
                indexData += "\n\t{ RPLCEwithpropsoffillchar }, // " + str(i)
                fillCharUsed = True
            oldcharnum = charnum
        
    
    if getName.match(line):
        charName = getName.search(line).group(1)
        
    if getWidth.match(line):
        advance = getWidth.search(line).group(1)
        
    if getBBX.match(line):
        BBX_w = int(getBBX.search(line).group(1))
        BBX_h = getBBX.search(line).group(2)
        BBX_x = getBBX.search(line).group(3)
        BBX_y = getBBX.search(line).group(4)
    
    if startBitmap.match(line):
        onBitmapLine = 1
    else:
        if endBitmap.match(line):
            if onBitmapLine != 0:  #We just finished reading a bitmap. Dump the binary cache!
                bitmapData += "\n\t"
                numbytes = int((len(binaryChar)+7)/8)    #How many bytes are required to store this bitmap?
                #for i in range(0, len(binaryChar) % 8)
                #    binaryChar += '0'                            #right-pad with zeros to finish a byte
                binaryChar = binaryChar.ljust(numbytes*8, '0')  #right-pad with zeros to finish a byte
                for i in range(numbytes):
                    bitmapData += "0b"
                    bitmapData += binaryChar[8*i:8*i+8]
                    bitmapData += ", "
                bitmapData += "// " + charName
                                    #      bitmapOffset, width, height, xAdvance, xOffset, yOffset
                indexData += "\n\t{   "
                indexData += str(binaryIndex).rjust(3, ' ') + ", "      #bitmapOffset
                indexData += str(BBX_w).rjust(3, ' ') + ", "      #width
                indexData += str(BBX_h).rjust(3, ' ') + ", "      #height
                indexData += str(advance).rjust(3, ' ') + ", "      #xAdvance
                indexData += str(BBX_x).rjust(3, ' ') + ", "      #xOffset
                BBX_y = -int(BBX_h)-int(BBX_y)
                indexData += str(BBX_y).rjust(3, ' ') + ", "      #yOffset
                indexData += " }, // " + charName
                
                binaryIndex += numbytes
                binaryChar = ""

            onBitmapLine = 0
        else:
            if onBitmapLine != 0:             #We are reading a bitmap!
                
                binaryChar += (bin(int(line, 16))[2:].zfill(len(line)*4-4))[:BBX_w]      
               
                #converts hex to binary with left-pad zeros, ltrimmed to BBX_w

bitmapData += "\n};"
indexData += "\n};"

hfile = open(fontname + ".h", 'w')
hfile.write(bitmapData + "\n\n" + indexData + "\nconst GFXfont " + fontname + " PROGMEM = {\n(uint8_t  *)" + fontname + "_Bitmap,(GFXglyph *)" + fontname + "_Glyphs, " + str(firstcharnum) + ", " + str(charnum) + ", " + pixsize + "};")

print("Your font has been saved as " + fontname + ".h")
if fillCharUsed == True:
    print('Your character range is non-consecutive. You need to open the .h file and\n replace "RPLCEwithpropsoffillchar" with the properties (6 numbers)\n of the character you wish to use for the invalid codepoints.')