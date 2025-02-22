#-------------------------------------------------------------------------------
# Name:        Button
# Purpose:     Interactive GUI elements using pygame
#
# Author:      gehmd
#
# Created:     05/04/2019
#-------------------------------------------------------------------------------
import math; #sqrt, pi
from enum import Enum;

import pygame;
from pygame import Vector2;

from Colors import *;

class draw:
    def aaline(surface, color, start_pos, end_pos, width = 1, blend = 1, pygameEnds = True):
        polygonToLineDist = 0;

        if not isinstance(start_pos, Vector2):
            start_pos = Vector2(start_pos);

        if not isinstance(end_pos, Vector2):
            end_pos = Vector2(end_pos);

        if width < 1:
            return pygame.Rect(start_pos[0], start_pos[1], 0, 0);

        elif width == 1:
            return pygame.draw.aaline(surface, color, start_pos, end_pos, blend);

        elif width > 1:
            result = [];

            #draw inner area
            perpUnit = (end_pos - start_pos).rotate(90).normalize();

            if pygameEnds:
                #replicate pygame's endcap behavior
                if abs(perpUnit.x) >= abs(perpUnit.y):
                    perpUnit = Vector2(1, 0);
                else:
                    perpUnit = Vector2(0, 1);

            polyUnit = perpUnit * (width / 2 - polygonToLineDist);

            result.append(pygame.draw.polygon(surface, color, [start_pos + polyUnit, end_pos + polyUnit, end_pos - polyUnit, start_pos - polyUnit], 0));

            #draw outer aa area
            perpUnit *= (width / 2);

            points = [start_pos + perpUnit, end_pos + perpUnit, end_pos - perpUnit, start_pos - perpUnit];

            for i in range(len(points)):
                result.append(pygame.draw.aaline(surface, color, points[i], points[(i + 1) % len(points)], blend));

##            #if even, draw a line to fill a gap
##            if not width % 2:
##                if perpUnit.x >= perpUnit.y:
##                    result.append(pygame.draw.line(surface, color, points[0], points[1], 3));
##                else:
##                    result.append(pygame.draw.line(surface, color, points[0], points[1], 3));

            return result[0].unionall(result[1:]);

    def aalines(surface, color, closed, points, width = 1, blend = 1, pygameEnds = True):
        polygonToLineDist = 0;

        if not isinstance(points, list):
            points = list(points);

        for i in range(len(points)):
            if not isinstance(points[i], Vector2):
                points[i] = Vector2(points[i]);

        if width < 1:
            return pygame.Rect(points[0].x, points[0].y, 0, 0);

        elif width == 1:
            return pygame.draw.aalines(surface, color, closed, points, blend);

        elif width > 1:
            if closed:
                points.append(points[0]);

            #reverse direction of first normal
            perpUnits = [(points[0] - points[1]).rotate(-90).normalize(), ];

            if closed:
                adjVec = width / 2 * perpUnits[0].rotate(180).normalize();

                points[-1] = points[-1] + (adjVec[0], adjVec[1]);
                #TODO adjust first point

            for i, p in enumerate(points[1:-1]):
                #because points is being sliced, i will be 1 less than p's index in the unsliced points
                #TODO slerp not always right
                perpUnits.append((p - points[i]).slerp(points[i + 2] - p, .5).rotate(90).normalize());
                #perpUnits.append((((points[i] + points[i + 2]) / 2) - p).rotate(-90).normalize());

                #debug draws
                tempVec = ((p - points[i]).rotate(90).normalize());
                tempVec *= (width / 2) - polygonToLineDist;

                pygame.draw.line(surface, RED, tempVec + p, p - tempVec);

                tempVec = ((points[i + 2] - p).rotate(90).normalize());
                tempVec *= (width / 2) - polygonToLineDist;

                pygame.draw.line(surface, BLUE, tempVec + p, p - tempVec);

            perpUnits.append((points[-1] - points[-2]).rotate(90).normalize());

            if pygameEnds:
                #replicate pygame's endcap behavior only for the first and last points
                if abs(perpUnits[0].x) >= abs(perpUnits[0].y):
                    perpUnits[0] = Vector2(1, 0);
                else:
                    perpUnits[0] = Vector2(0, 1);

                #reverse direction of first normal
                perpUnits[0] = -perpUnits[0];

                if abs(perpUnits[-1].x) >= abs(perpUnits[-1].y):
                    perpUnits[-1] = Vector2(1, 0);
                else:
                    perpUnits[-1] = Vector2(0, 1);

                if closed:
                    perpUnits[-1] = -perpUnits[-1];

            polyUnits = [u * (width / 2 - polygonToLineDist) for u in perpUnits];

            polyPoints = [p + polyUnits[i] for i, p in enumerate(points)];
            polyPoints.extend([p - polyUnits[-(i + 1)] for i, p in enumerate(reversed(points))]);

            for p, col in zip(polyPoints, [RED, ORANGE_RED, ORANGE, YELLOW, YELLOW_GREEN, GREEN, BLUE, ALICE_BLUE, PURPLE]):
                pygame.draw.circle(surface, col, (int(p[0]), int(p[1])), 10, 0);

            if not closed:
                pygame.draw.polygon(surface, color, polyPoints, 0);
            else:
                pygame.draw.polygon(surface, color, polyPoints, 1);
                pass;

            lineUnits = [u * (width / 2) for u in perpUnits];

            linePoints = [p + lineUnits[i] for i, p in enumerate(points)];
            linePoints.extend([p - lineUnits[-(i + 1)] for i, p in enumerate(reversed(points))]);

            pygame.draw.aalines(surface, color, closed, linePoints, blend);

class _UIBase:
    """Base class for UI elements."""

    def __init__(self, pos, width, height, color):
        """pos is a tuple of (x, y)
        width and height are in pixels
        color is a tuple of (r, g, b)
        """

        self.pos = Vector2(pos);
        self.color = color;
        self.width = width;
        self.height = height;
        #used for quick bounds checking
        self._pos2 = self.pos + (self.width, self.height);
        #used for refreshing expensive calculations
        self._dirty = True;

    def setPos(self, newPos):
        """Change the position of the UI element

        newPos is a tuple (x, y)
        """

        self.pos = Vector2(newPos);
        self._pos2 = self.pos + (self.width, self.height);

    def setColor(self, col):
        """Set the color for this element"""

        self.color = col;

    def markDirty(self):
        """Flag element as needing recalculating"""

        self._dirty = True;

    def wasClicked(self, pos):
        """Is pos within the element's area?

        pos is a tuple (x, y)

        Return a boolean value whether or not pos was within the element's area.
        """

        if self.pos[0] < pos[0] < self._pos2[0]:
            if self.pos[1] < pos[1] < self._pos2[1]:
                return True;

        return False;

    def getValue(self):
        """Return the value of this element."""

        raise NotImplementedError;

    def setValue(self, val):
        """Set the value of this element.

        val is the value to set this element to
        """

        raise NotImplementedError;

    def draw(self, screen):
        """Draw this element on the specified pygame.Surface object.

        screen is a pygame.Surface object
        """

        raise NotImplementedError;

class ArrowCurve(Enum):
    """Enum is determine which direction Arrows curve"""

    CURVE_LEFT = -1;
    CURVE_RIGHT = 1;

    def opposite(self):
        if self == ArrowCurve["CURVE_LEFT"]:
            return ArrowCurve["CURVE_RIGHT"];
        elif self == ArrowCurve["CURVE_RIGHT"]:
            return ArrowCurve["CURVE_LEFT"];

class Arrow(_UIBase):
    """An arrow between two points"""

    def __init__(self, srcPos, dstPos, lineWidth = 1, color = BLACK, curveFactor = 0, curveDir = ArrowCurve.CURVE_LEFT):
        """srcPos is a tuple of (x, y)
        dstPos is a tuple of (x, y)
        lineWidth is in pixels
        color is a tuple of (r, g, b) (default (0, 0, 0))
        curveFactor is either zero or a positive integer
        curveDir is a value from ArrowCurve
        """

        srcPos = Vector2(srcPos);
        dstPos = Vector2(dstPos);

        #calculate a perpendicular unit vertor
        midpoint = srcPos.lerp(dstPos, .5);
        perpVec = (dstPos - srcPos).rotate(90);
        vecLen = perpVec.length();
        perpUnitVec = perpVec.normalize();

        #calculate the two other points of the rectangle around the arrow
        p3 = (midpoint + perpUnitVec) * (vecLen / 2);
        p4 = (midpoint - perpUnitVec) * (vecLen / 2);

        #calculate the lower left corner, width and height of the rectangle around the arrow
        pos = Vector2(min(srcPos[0], dstPos[0], p3[0], p4[0]), min(srcPos[1], dstPos[1], p3[1], p4[1]));
        width = max(abs(srcPos[0] - dstPos[0]), abs(p3[0] - p4[0]), 20);
        height = max(abs(srcPos[1] - dstPos[1]), abs(p3[1] - p4[1]), 20);

        _UIBase.__init__(self, pos, width, height, color);
        self._src = srcPos - pos;
        self._dst = dstPos - pos;
        self.lineWidth = lineWidth;
        self._curveFactor = (curveFactor if curveFactor % 2 else (curveFactor + 1)) if curveFactor > 0 else 0;
        self.curveDir = curveDir;
        self._points = [];
        self._dirty = True;

    def setPos(self, newPos):
        """Change the position of the UI element

        newPos is a tuple (x, y)
        """

        _UIBase.setPos(self, newPos);

        self.markDirty();

    def setLineWidth(self, width):
        """Set the width in pixels for this Arrow

        width is a positive non-zero integer
        """

        self.lineWidth = width;

        self.markDirty();

    def setCurveFactor(self, curveFactor):
        """Change the curve factor for this arrow

        factor is a positive number for how curved the arrow will be, 0 is no curving
        """

        self._curveFactor = (curveFactor if curveFactor % 2 else (curveFactor + 1)) if curveFactor > 0 else 0;

        self.markDirty();

    def getCurveFactor(self):
        """Returns the curveFactor of the arrow, may not be the same value given in the constructor"""

        return self._curveFactor;

    def setCurveDir(self, direct):
        """Set the direction for the curve of the arrow

        direct is a value from ArrowCurve
        """

        self.curveDir = direct;

        self.markDirty();

    def getCurveDir(self):
        """Return the enum of type ArrowCurve for this arrow"""

        return self.curveDir;

    def isCloseTo(self, arrow, threshold = 25, returnDist = False):
        """Determine if this arrow is in proximity to another arrow

        threshold is distance in pixels
        returnDist is a flag to return a tuple containing a bool for closeness and the shortest distance that is under the threshold
        """

        dists = [p1.distance_squared_to(p2) for p1 in [(self.pos + self._src), (self.pos + self._dst)] for p2 in [(arrow.pos + arrow._src), (arrow.pos + arrow._dst)]];
        threshold = threshold ** 2;

        #TODO add in checking for proximity to line against src and dst for both arrows

        if returnDist:
            return (min(dists) <= threshold, min(dists));
        else:
            return min(dists) <= threshold;

    def compare(self, arrow):
        """Compare this arrow to another arrow and return a list of distances between the arrows source and dest"""

        dists = [p1.distance_squared_to(p2) for p1 in [(self.pos + self._src), (self.pos + self._dst)] for p2 in [(arrow.pos + arrow._src), (arrow.pos + arrow._dst)]];

        return list(map(math.sqrt, dists));

    def draw(self, screen):
        """Draw this Arrow on the specified pygame.Surface object.

        screen is a pygame.Surface object
        """

        if self._dirty:
            h = 10 * math.sqrt(3);
            w = 10;

            #calculate a perpendicular unit vector
            unit = (self._dst - self._src).normalize();
            perpUnit = unit.rotate(90);

            #first point is true source
            self._points = [self._src + self.pos, ];

            #common calculation, only do once
            halfCurveFactor = self._curveFactor // 2;

            #the higher the curveFactor, the more points will be used to draw the curve and the more curved it will be
            for i in range(self._curveFactor):
                #interpolation factor based on length along the arrow
                interpFact = (i + 1) / (self._curveFactor + 1);

                if i < halfCurveFactor:
                    #first half of the curve
                    self._points.append((self.pos + self._src).slerp(self._dst + self.pos, interpFact) + perpUnit * self.curveDir.value * self._curveFactor * (i + 1));
                    #horizontal offset based on length along the arrow
                    #print(i + 1);
                elif i == halfCurveFactor:
                    #middle of the curve
                    self._points.append((self.pos + self._src).slerp(self._dst + self.pos, interpFact) + perpUnit * self.curveDir.value * self._curveFactor * (i + .5));
                    #horizontal offset based on length along the arrow
                    #print(i + .5);
                else:
                    #last half of the curve
                    self._points.append((self.pos + self._src).slerp(self._dst + self.pos, interpFact) + perpUnit * self.curveDir.value * self._curveFactor * (i - (i - halfCurveFactor) - (i - (self._curveFactor + 1) // 2)));
                    #horizontal offset based on length along the arrow
                    #print(i - (i - halfCurveFactor) - (i - (self._curveFactor + 1) // 2));

            #last point is true dest
            self._points.append(self._dst + self.pos);

            #if this is a curved arrow
            if self._curveFactor:
                #recalculate unit and perpUnit based on last segment of the arrow
                unit = (self._points[-1] - self._points[-2]).normalize();
                perpUnit = unit.rotate(90);

            #calculate the "side" points of the arrow
            self.p1 = self._dst + self.pos - (unit * h) + (perpUnit * w);
            self.p2 = self._dst + self.pos - (unit * h) - (perpUnit * w);
            self._dirty = False;

        #draw the lines of the arrow
        #TODO could use draw.aalines, non-straight arrows look better, but aalines has no width argument, 5th arg is blend flag
        #would have to calculate and draw multiple lines to re-implement lineWidth
        #note: only outermost lines would have to be aalines, other should be lines or maybe filled rect
        #pygame.draw.lines(screen, self.color, False, self._points, self.lineWidth);

        for i in range(len(self._points) - 1):
            draw.aaline(screen, self.color, self._points[i], self._points[i + 1], self.lineWidth);
            pass;

        #debug draw
##        for p in self._points:
##            pygame.draw.circle(screen, self.color, (int(p[0]), int(p[1])), 3);
##            pass;

        pygame.draw.line(screen, self.color, self._dst + self.pos, self.p1, self.lineWidth);
        pygame.draw.line(screen, self.color, self._dst + self.pos, self.p2, self.lineWidth);

class MultiArrow(Arrow):
    def __init__(self, srcPos, dstPos, lineWidth = 1, color  =BLACK, numArrows = 2):
        """srcPos is a tuple of (x, y)
        dstPos is a tuple of (x, y)
        lineWidth is in pixels
        color is a tuple of (r, g, b) (default (0, 0, 0))
        numArrows is the number of sets of "side" points, should be greater than 1
        """

        srcPos = Vector2(srcPos);
        dstPos = Vector2(dstPos);

        Arrow.__init__(self, srcPos, dstPos, lineWidth, color);

        self._arrowList = [];
        lineVec = dstPos - srcPos;

        for i in range(1, numArrows):
            mult = i / numArrows;

            self._arrowList.append(Arrow(srcPos, srcPos + (lineVec * mult), lineWidth, color));

    def setPos(self, newPos):
        """Change the position of the UI element

        newPos is a tuple (x, y)
        """

        diff = self.pos - newPos;

        Arrow.setPos(self, newPos);

        for arrow in self._arrowList:
            arrow.setPos(arrow.pos - diff);

    def draw(self, screen):
        """Draw this Arrow on the specified pygame.Surface object.

        screen is a pygame.Surface object
        """

        Arrow.draw(self, screen);

        for arrow in self._arrowList:
            arrow.draw(screen);

        #debug draw
##        pygame.draw.circle(screen, GREEN, self._src + self.pos, 6);
##        pygame.draw.circle(screen, RED, self._dst + self.pos, 4);

class Label(_UIBase):
    """A class for rendered text."""

    def __init__(self, pos, text, font, color = BLACK):
        """pos is a tuple of (x, y)
        text is a string to be rendered
        font is a pygame.Font or pygame.SysFont object
        color is a tuple of (r, g, b) (default (0, 0, 0))
        """

        size = font.size(text);

        _UIBase.__init__(self, pos, size[0], size[1], color);
        self._text = text;
        self.font = font;
        self._surf = None;
        self._dirty = True;

    def getValue(self):
        """Return the string being rendered."""

        return self._text;

    def setValue(self, val):
        """Set the text to be rendered.

        val is a string
        """

        self._text = val;

        self.markDirty();

##    def markDirty(self):
##        """Flag Label as needing redrawn"""
##
##        self._dirty = True;

    def draw(self, screen):
        """Draw the Label's text on the specified pygame.Surface object.

        screen is a pygame.Surface object
        """

        if self._dirty:
            self._surf = self.font.render(self._text, True, self.color);

        screen.blit(self._surf, self.pos);

class Button(Label):
    """A class for rendered text within a rectangle."""

    #how many pixels away from the text should the rectangle be
    textPadding = 10;

    def __init__(self, pos, width, height, text, font, color = BLACK):
        """pos is a tuple of (x, y)
        width and height are in pixels
        text is a string to be rendered
        font is a pygame.Font or pygame.SysFont object
        color is a tuple of (r, g, b) (default (0, 0, 0))
        """

        Label.__init__(self, pos, text, font, color);
        #reset width and height to the specified values
        self.width = width;
        self.height = height;
        self._pos2 = self.pos + (self.width, self.height);

    def draw(self, screen):
        """Draw the Button's text and rectangle on the specified pygame.Surface object.

        screen is a pygame.Surface object
        """

        pygame.draw.rect(screen, self.color, self.pos[:] + [self.width, self.height], 2);

        if self._dirty or self._surf == None:
            self._surf = self.font.render(self._text, True, self.color);

        screen.blit(self._surf, self.pos.elementwise() + Button.textPadding);

class Slider(_UIBase):
    """A class for a slider with a list of values."""

    def __init__(self, pos, width, height, values, font, color = BLACK):
        """pos is a tuple of (x, y)
        width and height are in pixels
        values is a list of values that the slider can set to
        font is a pygame.Font or pygame.SysFont object
        color is a tuple of (r, g, b) (default (0, 0, 0))

        the initial value is the first one in values
        """

        _UIBase.__init__(self, pos, width, height, color);
        self._values = values;
        self.font = font;
        self._tickWidth = self.width / len(self._values);
        self.color = color;

        self._curVal = 0;

        minVal = str(self._values[0]);
        maxVal = str(self._values[-1]);

        self._minLabel = Label(self.pos - (font.size(minVal)[0], -self.height / 2), minVal, font, self.color);
        self._maxLabel = Label(self.pos + (self.width, self.height / 2), maxVal, font, self.color);
        self._curValLabel = Label(self.pos, str(self._values[self._curVal]), font, self.color);

        sliderPos = self._getSliderPos();

        self._curValLabel.pos = sliderPos - (self._curValLabel.width / 2, self._curValLabel.height);

    def setPos(self, newPos):
        """Change the position of the Slider

        newPos is a tuple (x, y)
        """

        _UIBase.setPos(self, newPos);

        self._minLabel.setPos(self.pos - (self.font.size(str(self._values[0]))[0], -self.height / 2));
        self._maxLabel.setPos(self.pos + (self.width, self.height / 2));

        sliderPos = self._getSliderPos();

        self._curValLabel.setPos(sliderPos - (self._curValLabel.width / 2, self._curValLabel.height));

    def wasClicked(self, pos):
        """Does the specified pos fall within the area of the sliding reactangle.

        pos is a tuple (x, y)

        Return a boolean value whether or not pos was within the element's area.
        """

        sliderPos = self._getSliderPos();

        if sliderPos[0] < pos[0] < sliderPos[0] + self._tickWidth:
            if sliderPos[1] < pos[1] < sliderPos[1] + self.height:
                return True;

        return False;

    def getValue(self):
        """Get the value the slider is set to."""

        return self._values[self._curVal];

    def setValue(self, val):
        """Switch the value of the slider to the specified value.

        Return a True/False value on whether the slider was changed to the specified value

        val is one of the values passed into the constructor for this Slider
        """

        if val in self._values:
            self._curVal = self._values.index(val);

            sliderPos = self._getSliderPos();

            self._curValLabel.setPos(sliderPos - (self._curValLabel.width / 2, self._curValLabel.height));
            self._curValLabel.setValue(str(self._values[self._curVal]));
            return True;

        return False;

    def incValue(self, num):
        """Adjust the slider a number of ticks.

        num is a integer, negative values move left, positive values move right
        """

        self._curVal += num;

        if self._curVal < 0:
            self._curVal = 0;

        elif self._curVal >= len(self._values):
            self._curVal = len(self._values) - 1;

        sliderPos = self._getSliderPos();

        self._curValLabel.setPos(sliderPos - (self._curValLabel.width / 2, self._curValLabel.height));
        self._curValLabel.setValue(str(self._values[self._curVal]));

    def _getSliderPos(self):
        return self.pos + (self._curVal * self._tickWidth, 0);

    def slidingMode(self, screen, fillColor = WHITE):
        """Control the slider with the mouse
        Assumes that a mouse button is held down when entering this function
        Exits when Escape is pressed or a mouse button is let go
        """

        while True:
            screen.fill(fillColor);

            events = pygame.event.get();

            for e in events:
                #key was pressed
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        return;

                #mouse button was released
                elif e.type == pygame.MOUSEBUTTONUP:
                    return;

                #mouse was moved
                elif e.type == pygame.MOUSEMOTION:
                    #e.rel is an (x, y) of the difference between the new mouse position and the old mouse positions
                    if e.rel[0] < 0:
                        self.incValue(-1);

                    elif e.rel[0] > 0:
                        self.incValue(1);

            self.draw(screen);

            #update the pygame screen
            pygame.display.flip();

    def draw(self, screen):
        """Draw the Slider on the specified pygame.Surface object.

        screen is a pygame.Surface object

        The screen will be locked for multiple draw calls and then unlocked when finished
        """

        #draw the text of the slider
        self._minLabel.draw(screen);
        self._maxLabel.draw(screen);
        self._curValLabel.draw(screen);

        #lock the pygame.Surface for faster multiple small draws
        screen.lock();

        #draw the horizontal line
        pygame.draw.line(screen, self.color, self.pos + (0, self.height / 2), self.pos + (self.width, self.height / 2), 2);

        #draw the vertical ticks
        for i in range(len(self._values)):
            pygame.draw.line(screen, self.color, self.pos + (i * self._tickWidth, 0), self.pos + (i * self._tickWidth, self.height), 2);

        #draw the slider
        pygame.draw.rect(screen, self.color, self._getSliderPos()[:] + [self._tickWidth, self.height]);

        #unlock the pygame.Surface
        screen.unlock();

class Input(Label):
    """A class for getting user keyboard input."""

    #a list of all the keys that produce common characters
    CHARACTERS = [i for i in range(pygame.K_EXCLAIM, pygame.K_AT + 1)] + [i for i in range(pygame.K_LEFTBRACKET, pygame.K_z + 1)] + [i for i in range(pygame.K_KP0, pygame.K_KP_PLUS + 1)] + [pygame.K_KP_EQUALS, ];
    #a list of all the keys that should produce different output when Capslock is on or Shift is held down
    MODCHARACTERS = {pygame.K_BACKQUOTE: "~", pygame.K_1: "!", pygame.K_2: "@", pygame.K_3: "#", pygame.K_4: "$", pygame.K_5: "%", pygame.K_6: "^", pygame.K_7: "&", pygame.K_8: "*", pygame.K_9: "(",
                        pygame.K_0: ")", pygame.K_MINUS: "_", pygame.K_EQUALS: "+", pygame.K_LEFTBRACKET: "{", pygame.K_RIGHTBRACKET: "}", pygame.K_BACKSLASH: "|", pygame.K_SEMICOLON: ":",
                        pygame.K_QUOTE: "\"", pygame.K_COMMA: "<", pygame.K_PERIOD: ">", pygame.K_SLASH: "?"};
    #how many pixels away from the text should the rectangle be
    textPadding = 10;

    def __init__(self, pos, width, height, font, color = BLACK):
        """pos is a tuple of (x, y)
        width and height are in pixels
        font is a pygame.Font or pygame.SysFont object
        color is a tuple of (r, g, b) (default (0, 0, 0))
        """

        Label.__init__(self, pos, "", font, color);
        self.width = width;
        self.height = height;
        self._pos2 = self.pos + (self.width, self.height);
        self._aniTimer = 0;
        self._clock = pygame.time.Clock();
        self._label = None;

    def setPos(self, newPos):
        """Change the position of the UI element

        newPos is a tuple (x, y)
        """

        diff = self.pos - newPos;

        Label.setPos(self, newPos);

        if self._label != None:
            self._label.setPos(self._label.pos - diff);

    def getValue(self):
        """Return the text of this element."""

        return self._text;

    def setValue(self, val):
        """Set the text inside this element.

        val is a string to be rendered
        """

        self._text = str(val);
        self._dirty = True;

    def setLabel(self, text):
        """Set a Label to be display with this Input

        text can either be a string or a Label
        if text is a string, the label will automatically be positioned about the Input
        if text is not a string or Label or is None, the label will be disabled
        """

        if isinstance(text, str):
            self._label = Label(self.pos - (0, self.font.get_height()), text, self.font, self.color);
        elif isinstance(text, Label):
            self._label = text;
        else:
            self._label = None;

        self.markDirty();

    def inputMode(self, screen, fillColor = WHITE):
        """Capture keyboard events until return(enter), escape or a mouse button is pressed

        screen is a pygame.Surface object
        fillColor is what color the rest of the screen will be filled with, while capturing input (default (255, 255, 255))

        modifies text of this element
        """

        while True:
            screen.fill(fillColor);

            events = pygame.event.get();

            #process events
            for e in events:
                #a key was pressed
                if e.type == pygame.KEYDOWN:
                    #if the key pressed was a typeable character
                    if e.key in self.CHARACTERS:
                        keyName = pygame.key.name(e.key);
                        mods = pygame.key.get_mods();

                        #if either shift key or caps lock is pressed and the key is a letter
                        if (mods & (pygame.KMOD_SHIFT | pygame.KMOD_CAPS)) and keyName.isalpha():
                            self._text += keyName.upper();
                        #if either shift key is pressed and the key is a "special" key with an alternate value
                        elif mods & pygame.KMOD_SHIFT and e.key in self.MODCHARACTERS:
                            self._text += self.MODCHARACTERS[e.key];
                        #used for the keypad keys: "[1]"
                        elif keyName.startswith("[") and len(keyName) > 1:
                            self._text += keyName[1];
                        else:
                            self._text += keyName;

                        self._dirty = True;
                    elif e.key == pygame.K_SPACE:
                        self._text += " ";
                        self._dirty = True;
                    elif e.key == pygame.K_BACKSPACE:
                        #chop off last character
                        self._text = self._text[:-1];
                        self._dirty = True;
                    elif e.key == pygame.K_RETURN or e.key == pygame.K_KP_ENTER or e.key == pygame.K_ESCAPE:
                        return;
                #mouse button clicked
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    return;

            #timer for the blinking cursor
            self._aniTimer += self._clock.tick();

            self.draw(screen);

            #draw the cursor for only 500ms
            if self._aniTimer < 500:
                fontWidth = self.font.size(self._text)[0];
                pygame.draw.line(screen, self.color, self.pos + (self.textPadding + fontWidth, self.textPadding), self.pos + (self.textPadding + fontWidth, self.height - self.textPadding), 1);
            elif self._aniTimer > 1000:
                self._aniTimer = 0;

            #update the pygame screen
            pygame.display.flip();

    def draw(self, screen):
        """Draw the Input's rectangle and text on the specified pygame.Surface object.

        screen is a pygame.Surface object
        """

        pygame.draw.rect(screen, self.color, self.pos[:] + [self.width, self.height], 2);

        if self._dirty:
            self._surf = self.font.render(self._text, True, self.color);
            self._dirty = False;

        if self._label != None:
            self._label.draw(screen);

        screen.blit(self._surf, self.pos.elementwise() + self.textPadding);

class UIManager:
    """A class to categorize and selectively interact with and draw UI elements."""

    def __init__(self, elemDict = {}):
        """elemDict is a dictionary of string: UI elements"""

        self._elems = elemDict;
        #None is the key for the master category
        self._cats = {None: []};
        #categories that have been warned about not existing
        self._warnings = [];

        for name in self._elems.keys():
            self._cats[None].append(name);

    def adjPos(self, adj):
        """Adjust the position of all GUI elements in this UIManager

        adj is a tuple of (xAdj, yAdj)"""

        for elem in self._elems.values():
            elem.setPos(elem.pos + adj);

    def addElement(self, name, element, categories = None):
        """Add an element to this UIManager.

        name is a string, a unique name for this UI element
        element is an instance of a class derived from _UIBase
        categories can be a string or a list of strings of categories this element will belong to
        """

        self._elems[name] = element;

        #add name to master category
        self._cats[None].append(name);

        if isinstance(categories, (list, tuple)):
            for cat in categories:
                self.addToCategory(name, cat);
        else:
            self.addToCategory(name, categories);

    def addToCategory(self, name, category):
        """Add an existing UI element to a category.

        name is the name of a UI element already added to this UIManager
        category is a string containing a category name
        """

        if category in self._cats:
            self._cats[category].append(name);
        else:
            self._cats[category] = [name, ];

    def clearElements(self):
        """Removes all UI elements and categories from this UIManager."""

        self._elems = [];
        self._cats = {None: []};

    def fetchCategories(self, categories, modifier):
        """Get a list of names of UI elements belonging to the categories specified with the modifier applied.

        categories is a list of strings containing category names, non-existant categories will be ignored with a warning
        modifier is one of ["union", "or", "intersect", "and", "difference", "xor", "complement", "not"]

        returns a list of objects derived from _UIBase
        """

        result = [];
        #a temporary list used for filtering bad categories
        temp = [];

        for cat in categories:
            if cat in self._cats:
                temp.append(cat);
            elif cat not in self._warnings:
                print("Warning: \"" + cat + "\" is not a category in this " + self.__class__.__name__);
                self._warnings.append(cat);

        categories = temp;

        #get names that are in any categories given
        if modifier == "union" or modifier == "or":
            result = self._cats[categories[0]].copy();

            for cat in categories[1:]:
                result.extend(self._cats[cat]);

        #get names that are only in all categories given
        elif modifier == "intersect" or modifier == "and":
            for name in self._cats[categories[0]]:
                found = True;

                for cat in categories[1:]:
                    if not name in self._cats[cat]:
                        found = False;
                        break;

                if found:
                    result.append(name);

        #get names that are in the first category but not any other categories given
        elif modifier == "difference":
            for name in self._cats[categories[0]]:
                found = False;

                for cat in categories[1:]:
                    if name in self._cats[cat]:
                        found = True;
                        break;

                if not found:
                    result.append(name);

        #get names that are only in one of the categories given
        elif modifier == "xor":
            union = self.fetchCategories(categories, "or");
            intersect = self.fetchCategories(categories, "and");

            for name in union:
                if not name in intersect:
                    result.append(name);

        #get names that are not in the given categories
        elif modifier == "complement" or modifier == "not":
            result = self.fetchCategories([None, ] + categories, "difference");

        return result;

    def leftClickOn(self, categories = None, modifier = None):
        """Captures events until a UI element is left clicked on with the mouse.

        categories is a string or a list of strings containing category names
        modifier can be None or one of ["union", "or", "intersect", "and", "difference", "xor", "complement", "not"] (default None)

        returns the name of the button clicked

        if modifier is supplied, categories must be a list of strings
        """

        while True:
            events = pygame.event.get();

            #process events
            for e in events:
                if e.type == pygame.QUIT:
                    return None;

                #a key was pressed
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        return None;

                elif e.type == pygame.MOUSEBUTTONUP:
                    #left mouse button was clicked
                    if e.button == 1:
                        if modifier != None:
                            #fetch modified categories
                            for name in self.fetchCategories(categories, modifier):
                                if self._elems[name].wasClicked(e.pos):
                                    return name;
                        else:
                            #fetch category given
                            for name in self._cats[categories]:
                                if self._elems[name].wasClicked(e.pos):
                                    return name;

    def draw(self, screen, categories = None, modifier = None):
        """Draw this element on the specified pygame.Surface object.

        screen is a pygame.Surface object
        categories is a string or a list of strings containing category names
        modifier can be None or one of ["union", "or", "intersect", "and", "difference", "xor", "complement", "not"] (default None)

        if modifier is supplied, category must be a list
        """

        if modifier != None:
            #fetch modified categories
            for name in self.fetchCategories(categories, modifier):
                self._elems[name].draw(screen);
        else:
            #fetch category given
            for name in self._cats[categories]:
                self._elems[name].draw(screen);

if __name__ == '__main__':
    #start basic pygame modules
    pygame.display.init();
    pygame.font.init();

    #haves keys repeat KeyDown events
    pygame.key.set_repeat(250, 50);

    #set window size
    screen = pygame.display.set_mode((700, 750));

    #font used to display text
    TestFont = pygame.font.SysFont("Arial", 16);

    #region test Label
    testLabel = Label((150, 100), "test", TestFont);
    #endregion

    #region test Button
    button = Button((100, 100), 40, 40, "TestClick", TestFont);

    #check coordinates in Button.wasClicked
    print("Testing Button");
    print(button.wasClicked((120, 120)));   #true
    print(button.wasClicked((90, 90)));     #false
    print(button.wasClicked((140, 140)));   #false
    print(button.wasClicked((139, 139)));   #true
    print(button.wasClicked((120, 90)));    #false
    print(button.wasClicked((140, 120)));   #false
    print();
    #endregion

    #region test UIManager
    uiMan = UIManager();

    uiMan.addElement("Test01", Button((40, 100), 100, 50, "testing01", TestFont), ["1", "odd", "prime"]);
    uiMan.addElement("Test02", Button((40, 150), 100, 50, "testing02", TestFont), ["2", "even", "prime"]);
    uiMan.addElement("Test03", Button((40, 200), 100, 50, "testing03", TestFont), ["3", "odd", "prime"]);
    uiMan.addElement("Test04", Button((40, 250), 100, 50, "testing04", TestFont), ["4", "even"]);
    uiMan.addElement("Test05", Button((40, 300), 100, 50, "testing05", TestFont), ["5", "odd", "prime"]);
    uiMan.addElement("Test06", Button((40, 350), 100, 50, "testing06", TestFont), ["6", "even"]);
    uiMan.addElement("Test07", Button((40, 400), 100, 50, "testing07", TestFont), ["7", "odd", "prime"]);
    uiMan.addElement("Test08", Button((40, 450), 100, 50, "testing08", TestFont), ["8", "even"]);
    uiMan.addElement("Test09", Button((40, 500), 100, 50, "testing09", TestFont), ["9", "odd"]);
    uiMan.addElement("Test10", Button((40, 550), 100, 50, "testing10", TestFont), ["10", "even", ">9"]);
    uiMan.addElement("Test11", Button((40, 600), 100, 50, "testing11", TestFont), ["11", "odd", "prime", ">9"]);
    uiMan.addElement("Test12", Button((40, 650), 100, 50, "testing12", TestFont), ["12", "even", ">9"]);
    uiMan.addElement("Test13", Button((40, 700), 100, 50, "testing13", TestFont), ["13", "odd", "prime", ">9"]);

    #test UIManager categories
    print("Testing UIManager");
    print("3 or 4 ", uiMan.fetchCategories(["3", "4"], "union"));                                       #3 and 4
    print("even and prime ", uiMan.fetchCategories(["even", "prime"], "and"));                          #2
    print("odd but not prime ", uiMan.fetchCategories(["odd", "prime"], "difference"));                 #9
    print("prime but not even nor 5 ", uiMan.fetchCategories(["prime", "even", "5"], "difference"));    #1 3 7 11 13
    print("even xor >9 ", uiMan.fetchCategories(["even", ">9"], "xor"));                                #2 4 6 8 11 13
    print("not even", uiMan.fetchCategories(["even", ], "not"));                                        #1 3 5 7 9 11 13
    print("not even nor prime", uiMan.fetchCategories(["even", "prime"], "not"));                       #9
    print();
    #endregion

    #region test Slider
    testSlider = Slider((20, 20), 300, 50, range(10, 21, 1), TestFont);
    testSlider2 = Slider((360, 20), 300, 50, ["a", "b", "c", "d", "e", "f"], TestFont);

    print("Testing Slider");
    print(testSlider.wasClicked((21, 21)));     #true
    print(testSlider2.wasClicked((659, 45)));   #false
    print();
    #endregion

    #region test Input
    testInput = Input((160, 300), 100, 40, TestFont);
    testInput.setValue("Test");
    testInput.setLabel("Test Input");

    print("Testing Input");
    print(testInput.getValue() == "Test");  #true
    print();
    #endregion

    #region test Arrow
    testArrows = [
                    Arrow((200, 150), (300, 150), color = RED),
                    Arrow((200, 200), (250, 250), color = BLUE),
                    Arrow((300, 200), (300, 250), color = GREEN),
                    Arrow((375, 250), (350, 150), color = YELLOW),

                    Arrow((390, 390), (350, 350), 3),
                    Arrow((290, 290), (330, 330), 3),
                    Arrow((290, 390), (330, 350), 3),
                    Arrow((390, 290), (350, 330), 3),

                    Arrow((290, 340), (330, 340), 3),

                    Arrow((350, 500), (390, 540), 3),
                    Arrow((330, 480), (290, 440), 3),
                    Arrow((330, 500), (290, 540), 3),
                    Arrow((350, 480), (390, 440), 3)
                ];

    print("Are Red and Blue Arrows close?", "yes" if testArrows[0].isCloseTo(testArrows[1], 50) else "no"); #yes
    print("Are Blue and Green Arrows close?", "yes" if testArrows[1].isCloseTo(testArrows[2], 50) else "no"); #yes
    print("Are Red and Green Arrows close?", "yes" if testArrows[0].isCloseTo(testArrows[2], 50) else "no"); #yes
    print("Are Red and Yellow Arrows close?", "yes" if testArrows[0].isCloseTo(testArrows[3], 50) else "no"); #yes
    print("Are Blue and Yellow Arrows close?", "yes" if testArrows[1].isCloseTo(testArrows[3], 50) else "no"); #no
    print("Are Green and Yellow Arrows close?", "yes" if testArrows[2].isCloseTo(testArrows[3], 50) else "no"); #no

    testMultiArrow = MultiArrow((500, 500), (450, 600), numArrows = 5);
    testMultiArrow2 = MultiArrow((400, 400), (550, 500), numArrows = 10);
    #endregion

    #region speed test
    #perform a speed test for Arrow.Compare
##    clock = pygame.time.Clock();
##
##    clock.tick();
##
##    for i in range(100000):
##        Arrow(Vector2(i, i), Vector2(100 + i, 100 + i), 1, BLACK).compare(Arrow(Vector2(42 + i, 39 - i), Vector2(128 - i, 225 - i), 1, BLACK));
##
##    print("msec passed", clock.tick());
    #endregion

    done = False;

    while not done:
        #fill the screen with a color
        screen.fill(GRAY);

        events = pygame.event.get();

        #event processing
        for e in events:
            if e.type == pygame.QUIT:
                done = True;
            #a key was pressed
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    done = True;

                elif e.key == pygame.K_LEFT:
                    #decrement the sliders
                    testSlider.incValue(-1);
                    testSlider2.incValue(-1);

                elif e.key == pygame.K_RIGHT:
                    #increment the sliders
                    testSlider.incValue(1);
                    testSlider2.incValue(1);

                elif e.key == pygame.K_UP:
                    #move the elements up
                    testLabel.setPos((testLabel.pos[0], testLabel.pos[1] - 1));
                    testSlider.setPos((testSlider.pos[0], testSlider.pos[1] - 1));
                    testSlider2.setPos((testSlider2.pos[0], testSlider2.pos[1] - 1));
                    testInput.setPos((testInput.pos[0], testInput.pos[1] - 1));

                    for arrow in testArrows:
                        arrow.setPos((arrow.pos[0], arrow.pos[1] - 1));

                    testMultiArrow.setPos((testMultiArrow.pos[0], testMultiArrow.pos[1] - 1));
                    testMultiArrow2.setPos((testMultiArrow2.pos[0], testMultiArrow2.pos[1] - 1));
                    uiMan.adjPos((0, -1));
                    pass;

                elif e.key == pygame.K_DOWN:
                    #move the elements down
                    testLabel.setPos((testLabel.pos[0], testLabel.pos[1] + 1));
                    testSlider.setPos((testSlider.pos[0], testSlider.pos[1] + 1));
                    testSlider2.setPos((testSlider2.pos[0], testSlider2.pos[1] + 1));
                    testInput.setPos((testInput.pos[0], testInput.pos[1] + 1));

                    for arrow in testArrows:
                        arrow.setPos((arrow.pos[0], arrow.pos[1] + 1));

                    testMultiArrow.setPos((testMultiArrow.pos[0], testMultiArrow.pos[1] + 1));
                    testMultiArrow2.setPos((testMultiArrow2.pos[0], testMultiArrow2.pos[1] + 1));
                    uiMan.adjPos((0, 1));
                    pass;

                elif e.key == pygame.K_PERIOD:
                    #move the elements right
                    testMultiArrow.setPos((testMultiArrow.pos[0] + 1, testMultiArrow.pos[1]));

                elif e.key == pygame.K_COMMA:
                    #move the elements left
                    testMultiArrow.setPos((testMultiArrow.pos[0] - 1, testMultiArrow.pos[1]));

                elif e.key == pygame.K_l:
                    #use uiMan to only draw/detect clicks on elements it controls
                    uiMan.draw(screen);
                    pygame.display.flip();

                    uiMan.leftClickOn();

                elif e.key == pygame.K_i:
                    #pass control to testInput to collect keyboard input
                    testInput.setLabel(None);

                    testInput.inputMode(screen);

        #region test aalines
        width = 50;

        Label((300, 550), "pygame", TestFont).draw(screen);
        pygame.draw.line(screen, SADDLE_BROWN, (300, 600), (450, 650), width);
        pygame.draw.line(screen, BEIGE, (350, 550), (200, 400), width);
        #pygame.draw.circle(screen, SADDLE_BROWN, (400, 600), 5);

        Label((200, 550), "Button", TestFont).draw(screen);
        draw.aaline(screen, SADDLE_BROWN, (200, 600), (350, 650), width);
        draw.aaline(screen, BEIGE, (250, 550), (100, 400), width);
        #pygame.draw.circle(screen, SADDLE_BROWN, (200, 600), 5);

        aaWidth = width;

        points = [(600, 600), (500, 600), (400, 400), (500, 450)];
        draw.aalines(screen, SADDLE_BROWN, True, points, aaWidth, pygameEnds=True);

##        diffPoints = [p - (-50, 200) for p in points];
##        draw.aalines(screen, VIOLET, False, diffPoints, aaWidth, pygameEnds = False);

        for p in points:
            pygame.draw.circle(screen, LIME, (int(p[0]), int(p[1])), 10, 0);
        #endregion

        for arrow in testArrows:
            arrow.draw(screen);

        src = (500, 200);
        dst = (600, 300);

        adj = Vector2(10, -10)

        for index, color in enumerate([BLUE, GREEN, RED, PURPLE, ORANGE, FUCHSIA, PINK, LIME, DARK_GRAY, DARK_KHAKI]):
            Arrow(index * adj + src, index * adj + dst, 1, color = color, curveFactor = index, curveDir = ArrowCurve.CURVE_LEFT).draw(screen);
            Arrow(index * -adj + src, index * -adj + dst, 1, color = color, curveFactor = index, curveDir = ArrowCurve.CURVE_RIGHT).draw(screen);
            pass;

        #used for debugging arrow positions
##        pygame.draw.circle(screen, ORANGE, (190, 450), 5);
##        pygame.draw.circle(screen, ORANGE, (290, 490), 5);
##        pygame.draw.circle(screen, CYAN, (410, 470), 5);
##        pygame.draw.circle(screen, CYAN, (510, 510), 5);
##        pygame.draw.circle(screen, LIGHT_SALMON, (300, 300), 5);
##        pygame.draw.circle(screen, LIGHT_SALMON, (310, 610), 5);
##        pygame.draw.circle(screen, DARK_GREEN, (300, 250), 5);
##        pygame.draw.circle(screen, DARK_GREEN, (350, 400), 5);

        testMultiArrow.draw(screen);
        testMultiArrow2.draw(screen);

        uiMan.draw(screen);

        testLabel.draw(screen);

        testSlider.draw(screen);
        testSlider2.draw(screen);

        testInput.draw(screen);

        #update the pygame screen
        pygame.display.flip();

    #unload the pygame modules that were started
    pygame.font.quit();
    pygame.display.quit();