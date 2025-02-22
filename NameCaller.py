#-------------------------------------------------------------------------------
# Name:        NameCaller
# Purpose:
#
# Author:      Dustin
#
# Created:     12/08/2018
# Copyright:   (c) Dustin 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python
#python3.5

import random;
import time;
import pygame;
import sys;

import Button;

from enum import Enum;

if sys.platform == "win32":
    from ctypes import windll;

    def stickToTop():
        hwnd = pygame.display.get_wm_info()["window"];

        windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 2 | 1);

class NameState(Enum):
    BLACK = (0, 0, 0);
    GREEN = (0, 255, 0);
    RED = (255, 0, 0);
    ABSENT = (64, 64, 64);

def queryNewList():
    sortie = [];
    fileName = input("Enter the filename: ").strip() + ".txt";
##    fileName = "nctest.txt";

    try:
        infile = open(fileName);
    except:
        print("No such file exists.");
        return sortie;

    for l in infile:
        line = l.strip();

        if line:
            sortie.append(line);

    infile.close();

    return sortie;

def expandWindim(windim, namesLen, font):
    return (windim[0], windim[1] + (int(namesLen * font.size("0")[0] / windim[0]) + 1) * font.get_height());

def pick(nameIndex, names, colors):
    if nameIndex >= 0 and colors[nameIndex] is not NameState.GREEN and colors[nameIndex] is not NameState.ABSENT:
        colors[nameIndex] = NameState.RED;

    count = 0;

    while True:
        i = random.randrange(0, len(names));
        count += 1;

        if colors[i] is not NameState.GREEN and colors[i] is not NameState.ABSENT and i is not nameIndex:
            name = names[i];
            nameIndex = i;
            break;

        if count > len(names) * 10:
            name = "";
            nameIndex = -1;
            break;

    return name, nameIndex;

def main():
    windim = (350, 150);
    expWindim = (350, 150);

    pygame.display.init();
    pygame.font.init();
    screen = pygame.display.set_mode(windim);

    smallFont = pygame.font.SysFont("Arial", 14);
    smallFontHeight = smallFont.get_height();
    halfSmallFontHeight = smallFontHeight / 2;

    medFont = pygame.font.SysFont("Arial", 20, bold=True);
    medFontHeight = medFont.get_height();
    halfMedFontHeight = medFontHeight / 2;

    largeFont = pygame.font.SysFont("Arial", 36);
    largeFontHeight = largeFont.get_height();
    halfLargeFontHeight = largeFontHeight / 2;

    done = False;
    displayHelp = False;
    displayNames = False;
    buttons = {"pick" : Button.Button(10, 10, 40, 40, (128, 128, 128), smallFont.render("Pick", False, (0, 0, 0))), \
               "green" : Button.Button(60, 10, 40, 40, (128, 128, 128), smallFont.render("Green", False, (0, 0, 0))), \
               "absent" : Button.Button(110, 10, 40, 40, (128, 128, 128), smallFont.render("Absent", False, (0, 0, 0))), \
               "list" : Button.Button(160, 10, 40, 40, (128, 128, 128), smallFont.render("List", False, (0, 0, 0))), \
               "load" : Button.Button(210, 10, 40, 40, (128, 128, 128), smallFont.render("Load", False, (0, 0, 0))), \
               "save" : Button.Button(260, 10, 40, 40, (128, 128, 128), smallFont.render("Save", False, (0, 0, 0))), \
               "reset" : Button.Button(310, 10, 40, 40, (128, 128, 128), smallFont.render("Reset", False, (0, 0, 0)))};

    name = "";
    nameIndex = -1;
    names = queryNewList();
    namesLen = 0;
    for n in names:
        namesLen += len(n) + 1;
    colors = [NameState.BLACK, ] * len(names);
    expWindim = expandWindim(windim, namesLen, medFont);

    if sys.platform == "win32":
        stickToTop();

    while not done:
        screen.fill((255, 128, 64));

        events = pygame.event.get();

        for e in events:
            if e.type is pygame.QUIT:
                done = True;
            elif e.type is pygame.KEYDOWN:
                if e.key is pygame.K_ESCAPE:
                    done = True;
            elif e.type is pygame.MOUSEBUTTONUP:
                if e.button is 1:
                    if buttons["pick"].checkClick(e.pos):
                        name, nameIndex = pick(nameIndex, names, colors);
                    elif buttons["green"].checkClick(e.pos):
                        if nameIndex >= 0:
                            colors[nameIndex] = NameState.GREEN;
                    elif buttons["absent"].checkClick(e.pos):
                       if nameIndex >= 0:
                           colors[nameIndex] = NameState.ABSENT;
                    elif buttons["list"].checkClick(e.pos):
                        if displayNames:
                            pygame.display.set_mode(windim);
                        else:
                            pygame.display.set_mode(expWindim);

                        displayNames = not displayNames;
                    elif buttons["load"].checkClick(e.pos):
                        name = "";
                        nameIndex = -1;
                        names = queryNewList();
                        namesLen = 0;
                        for n in names:
                            namesLen += len(n) + 1;
                        colors = [NameState.BLACK, ] * len(names);
                        expWindim = expandWindim(windim, namesLen, medFont);
                    elif buttons["save"].checkClick(e.pos):
                        greenNames = "";
                        blackNames = "";
                        redNames = "";
                        absentNames = ""

                        for i in range(len(names)):
                            if colors[i] is NameState.GREEN:
                                greenNames += names[i] + "\n";
                            elif colors[i] is NameState.BLACK:
                                blackNames += names[i] + "\n";
                            elif colors[i] is NameState.RED:
                                redNames += names[i] + "\n";
                            elif colors[i] is NameState.ABSENT:
                                absentNames += names[i] + "\n";

                        ts = time.localtime();

                        outfile = open("nc_report" + \
                                        str(ts.tm_year) + '_' + str(ts.tm_mon) + '_' + str(ts.tm_mday) + '_' +\
                                        str(ts.tm_hour) + '_' + str(ts.tm_min) + ".txt", 'w');

                        outfile.write("[GREEN]\n");
                        outfile.write(greenNames);

                        outfile.write("\n[BLACK]\n");
                        outfile.write(blackNames);

                        outfile.write("\n[RED]\n");
                        outfile.write(redNames);

                        outfile.write("\n[ABSENT]\n");
                        outfile.write(absentNames);

                        print("Wrote file: " + outfile.name);

                        outfile.close();

                    elif buttons["reset"].checkClick(e.pos):
                        name = "";
                        nameIndex = -1;
                        colors = [NameState.BLACK, ] * len(names);

        for button in buttons.values():
            button.draw(screen);

        if name:
            screen.blit(largeFont.render(name, False, colors[nameIndex].value), ((windim[0] / 2) - (largeFont.size(name)[0] / 2), (windim[1] / 2) - (halfLargeFontHeight / 2)));

        if displayNames:
            adjX = 0;
            adjY = 0;

            for i in range(len(names)):
                screen.blit(medFont.render(names[i], False, colors[i].value), (adjX, windim[1] + adjY));

                adjX += medFont.size(names[i] + " ")[0] + halfMedFontHeight;

                if i < len(names) - 1 and adjX + medFont.size(names[i + 1] + " ")[0] > windim[0]:
                    adjX = 0;
                    adjY += medFontHeight;

        pygame.display.flip();

    pygame.font.quit();
    pygame.display.quit();

if __name__ == '__main__':
    main()
