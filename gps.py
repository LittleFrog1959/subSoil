# GPS test program.  Python 3 only
# D. Waine 17/05/2020

import serial
import curses
import sys
import time

names = [ \
        ['$GPGGA', 'UTC', 'Lat', 'Lat drctn', \
         'Lon', 'Lon drctn', 'Quality', \
        '# SVs', 'HDOP', 'Orth hgt', \
        'Units', 'Geoid sep', 'Units', \
        'Age', 'Ref ID', \
        'Checksum'], \
        ['$GPGSA', 'Mode 1', 'Mode 2', 'SVN 1', 'SVN 2', 'SVN 3', 'SVN 4', 'SVN 5', 'SVN 6', \
        'SVN 7', 'SVN 8', 'SVN 9', 'SVN 10', 'SVN 11', 'SVN 12', 'PDOP', 'HDOP', 'VDOP', \
        'Checksum'], \
        ['$GPRMC', 'UTC', 'Status', 'Lat', 'Lat drctn', 'Lon', 'Lon drctn', \
        'Speed', 'Heading', 'Date', 'Mag var', 'E/W', '???', \
        'Checksum'], \
        ['$GPVTG', 'Track-Tru', 'Units', 'Track-Mag', 'Units', 'Speed', 'Units', \
        'Speed', 'Units', '???', \
        'Checksum'], \
        ['$GPGSV', 'Msgs', 'Msg #', 'SVs', \
        '1 SV PRN', '1 Ele', '1 Az', '1 SNR', \
        '2 SV PRN', '2 Ele', '2 Az', '2 SNR', \
        '3 SV PRN', '3 Ele', '3 Az', '3 SNR', \
        '4 SV PRN', '4 Ele', '4 Az', '4 SNR', \
        'Checksum'] \
        ]

#Type 1 or Type 9. Null field when DGPS is not used.

#0: Fix not valid
#1: GPS fix
#2: Differential GPS fix, OmniSTAR VBS
#4: Real-Time Kinematic, fixed integers
#5: Real-Time Kinematic, float integers, OmniSTAR XP/HP or Location RTK

def main (screen):

    # Set up a couple of places to hold vital readings
    currentLat = None
    currentLon = None
    baseLat = None
    baseLon = None
    oldPlotRow = None
    oldPlotCol = None

    # Open the GPS device
    gps = serial.Serial('/dev/ttyUSB0', 9600)

    # This list will hold new command codes when
    # detected
    cmds = []

    # Print the static parts of the screen.  Go through each row in the
    # list printing the message type then a blank line then the field
    # name.
    for c in range (len(names)):
        name = names[c]
        for r in range (len(name)):
            if r == 0:
                screen.addstr (r, c * 25, name[r])
                # Add to the list of known commands and zero
                # the occourance number
                cmds = cmds + [[name[0], 0]]
            else:
                screen.addstr (r + 1, c * 25, name[r])
    screen.refresh ()

    # Loop forever
    while True:
        # Read a whole line of text from the GPS device but only proceeed
        # if the string starts with $
        while True:
            line = gps.readline ()
            # Convert the byte stream into a string
            line = line.decode ()
            if line[0] == '$':
                break

#        fd = open ("delme.txt", "a")
#        fd.write (line)
#        fd.close ()

        # Split the line into seperate fields held in a list
        fields = line.split (',')

        # The last entry in the fields list should have a "*"
        if fields[-1].find ('*') == -1:
            print ('Could not find checksum delimiter')
            time.sleep (5)
            sys.exit ()
        else:
            lastField = fields[-1].split ('*')
            fields[-1] = lastField[0]
            # Append the checksum but remove the /r/n
            fields = fields + [lastField[1][0:2]]

#        fd = open ("delme.txt", "a")
#        fd.write (str (fields))
#        fd.close ()

        # Scan the known command list and either add to the end
        # or bump the occourance counter

        # Find the correct command counter to bump.  Error if the
        # command is unknown
        foundCmd = False
        for i in range (len (cmds)):
            if (cmds[i][0] == fields[0]):
                cmds[i][1] += 1
                foundCmd = True
                # Now would be a good time to print the actual
                # field contents because we know what col we're on
#                if i == 4:
                row = 2
                for c in range (1, len (fields)):
                    # pad the trailing part of the field with spaces
                    # and limit to 12 chars overall
                    eField = (fields[c] + "            ")[0:12]
                    # If the sentence is a $GPGSV then use field
                    # 2 as an offset to the col to print at
                    if fields[0] == '$GPGSV':
                        col = (i*25) + ((int (fields[2]) - 1) * 4) + 10
                    else:
                        col = (i*25) + 10
                    screen.addstr (row, col , eField)
                    row += 1
                screen.refresh ()
                break

        if foundCmd == False:
            print ('Error:  Could not find command')
            time.sleep (1)
            sys.exit ()

        # Now print out the count of occourances
        for c in range (len(cmds)):
            screen.addstr (1, c * 25, str (cmds[c][1]))
        screen.refresh ()

        # Save vital readings from GPS device
        if fields[0] == '$GPGGA':
            currentLat = fields [2]
            currentLon = fields [4]

        # If we have a valid base setting then work out where to plot
        # position
        if baseLat != None:
            offsetLat = int ((float (currentLat) - float (baseLat)) * 100000)
            offsetLon = int ((float (currentLon) - float (baseLon)) * 100000)
            screen.addstr (30, 0, (str (offsetLat) + "          ")[0:10])
            screen.addstr (31, 0, (str (offsetLon) + "          ")[0:10])

            # Plot on screen
            plotRow = int (40 - (offsetLat / 10))
            plotCol = int (50 - (offsetLon / 10))
#            if oldPlotRow != None:
#                # Unplot the old place
#                screen.addstr (oldPlotRow, oldPlotCol, ' ')
            # Plot the new position
            try:
                screen.addstr (plotRow, plotCol, '*')
                oldPlotRow = plotRow
                oldPlotCol = plotCol
                screen.refresh ()
            except:
                fd = open ("delme.txt", "a")
                fd.write ('Error writing to screen')
                fd.write ('Row ' + str (plotRow) +' Col ' + str (plotCol) + '\r\n')
                fd.close ()

        # Check the keyboard
        ch = screen.getch ()
        if ch != curses.ERR:
            if ch == ord ('q'):
                sys.exit ()

            if ch == ord ('z'):
                # Load up the starting point for picture centre if
                # the currentLat is valid
                if currentLat != None:
                    baseLat = currentLat
                    baseLon = currentLon

if __name__ == '__main__':
    # Open the screen as a curses device
    screen = curses.initscr ()
    curses.noecho ()
    curses.cbreak ()
    screen.nodelay (True)       # keyboard check is non-blocking
    curses.wrapper (main)

