import pygame
from script import getHiloData
import math
import json
from datetime import datetime

pygame.init()

screen = pygame.display.set_mode((800, 480))
pygame.display.set_caption("Tide Display")

font = pygame.font.Font(None, 20)

USE_API = False

class chartBox:
    def __init__(self, left, top, right, bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

        self.targetPoints = []
        self.displayPoints = []

    def width(self):
        return self.right - self.left
    
    def height(self):
        return self.bottom - self.top
    
    def draw(self, screen, color):
        pygame.draw.rect(screen, color, (self.left, self.top, self.width(), self.height()), 2)

    def addPoint(self, hours, height, maxHours, minHeight, maxHeight):
        x = screenValue(hours, 0, maxHours, self.left, self.right)
        y = screenValue(height, minHeight, maxHeight, self.bottom, self.top)

        self.targetPoints.append((x, y))

    def buildGraph(self, data):
        self.targetPoints.clear()

        self.minHours = data[0]["hours"]
        self.maxHours = data[-1]["hours"]

        maxHeight = max(point["height"] for point in data) + .2
        minHeight = min(point["height"] for point in data) - .2

        for point in data:
            x = screenValue(point["hours"], self.minHours, self.maxHours, self.left, self.right)
            y = screenValue(point["height"], minHeight, maxHeight, self.bottom, self.top)

            self.targetPoints.append((x, y))

        self.displayPoints = [(x, self.bottom) for x, y in self.targetPoints]

    def drawCurrentLine(self, currentHours):
        if not (self.minHours <= currentHours <= self.maxHours):
            return
        x = screenValue(currentHours, self.minHours, self.maxHours, self.left, self.right)
        pygame.draw.line(screen, (255, 0, 0), (x, self.top), (x, self.bottom), 3)
        
        for i in range(len(self.displayPoints) - 1):
            x1, y1 = self.displayPoints[i]
            x2, y2 = self.displayPoints[i + 1]

            if x1 <= x <= x2:
                t = (x - x1) / (x2 - x1)
                y = lerp(y1, y2, t)
                pygame.draw.circle(screen, (255, 0, 0), (int(x), int(y)), 6)

chart1 = chartBox(70, 28, 390, 208)
chart2 = chartBox(420, 28, 740, 208)
chart3 = chartBox(70, 230, 740, 450)

def screenValue(value, dataMin, dataMax, screenMin, screenMax):
    return (value - dataMin) * (screenMax - screenMin) / (dataMax - dataMin) + screenMin

def lerp(a, b, t):
    return a + (b - a) * t

def drawLine(start, end, color):
    pygame.draw.line(screen, color, start, end, 2)

def drawChart(chart):
    for i in range(len(chart.displayPoints) - 3):
        p0 = chart.displayPoints[i]
        p1 = chart.displayPoints[i + 1]
        p2 = chart.displayPoints[i + 2]
        p3 = chart.displayPoints[i + 3]

        prev = p1

        steps = 10
        for j in range(1, steps + 1):
            t = j / steps
            curr = catmullRom(p0, p1, p2, p3, t)
            drawLine(prev, curr, (255, 255, 0))
            prev = curr

def loadData():
    if USE_API:
        data = getHiloData()
        return data
    return loadTestData("testPoints.json")

def catmullRom(p0, p1, p2, p3, t):
    t2 = t * t
    t3 = t2 * t

    x = 0.5 * (
        (2 * p1[0]) +
        (-p0[0] + p2[0]) * t +
        (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t2 +
        (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t3
    )

    y = 0.5 * (
        (2 * p1[1]) +
        (-p0[1] + p2[1]) * t +
        (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t2 +
        (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t3
    )

    return (x, y)

def tideBetween(start, end, steps=50):
    points = []
    for i in range(steps):
        t = i / steps
        smooth = (1 - math.cos(math.pi * t)) / 2

        height = (start["height"] + (end["height"] - start["height"]) * smooth)
        hours = (start["hours"] + (end["hours"] - start["hours"]) * t)

        points.append({"hours": hours, "height": height})
    return points

def makeDetailedTideData(events):
    detailed = []
    for i in range(len(events)-1):
        detailed += tideBetween(events[i], events[i+1])
    detailed.append(events[-1])
    return detailed

def saveTestData(filename, data):
    for point in data:
        if "time" in point and isinstance(point["time"], datetime):
            point["time"] = point["time"].isoformat()

    with open(filename, "w") as file:
        json.dump(data, file, indent=4)

def loadTestData(filename):
    with open(filename, "r") as file:
        data = json.load(file)
    for point in data:
        point["time"] = datetime.fromisoformat(point["time"])

    return data

def getCurrentTime(data):
    startTime = data[0]["time"]
    now = datetime.now()

    return (now - startTime).total_seconds() / 3600

def getCurrentHeight(data, currentHours):
    for i in range(len(data) - 1):
        p1 = data[i]
        p2 = data[i + 1]

        if p1["hours"] <= currentHours <= p2["hours"]:
            t = ((currentHours - p1["hours"]) / (p2["hours"] - p1["hours"]))
            return lerp(p1["height"], p2["height"], t)
        
    return data[-1]["height"]

def drawInfoPanel():
    pygame.draw.rect(screen, (60, 160, 220), (chart2.left, chart2.top, chart2.width(), chart2.height()))\
    
    third = chart2.height() // 3
    
    title = titleFont.render("Current height", True, (255, 255, 255))
    value = valueFont.render(f"{currentHeight:.2f} ft", True, (255, 255, 255))
    screen.blit(title, title.get_rect(center = (chart2.left + chart2.width() // 2, chart2.top + 18)))
    screen.blit(value, value.get_rect(center = (chart2.left + chart2.width() // 2, chart2.top + 45)))

    y = chart2.top + third - 5

    todayTitle = titleFont.render("TODAY", True, (230, 230, 30))
    screen.blit(todayTitle, todayTitle.get_rect(center = (chart2.left + chart2.width() // 2, y + 35)))

    highLabel = labelFont.render("High", True, (230, 230, 30))
    lowLabel = labelFont.render("Low", True, (230, 230, 30))
    highValue = valueFont.render(f"{todayHigh:.2f} ft", True, (230, 230, 30))
    lowValue = valueFont.render(f"{todayLow:.2f} ft", True, (230, 230, 30))

    screen.blit(highLabel, highLabel.get_rect(center = (chart2.left + chart2.width() // 4, y + 20)))
    screen.blit(lowLabel, lowLabel.get_rect(center = (chart2.left + chart2.width()*3 // 4, y + 20)))
    screen.blit(highValue, highValue.get_rect(center = (chart2.left + chart2.width() // 4, y + 50)))
    screen.blit(lowValue, lowValue.get_rect(center = (chart2.left + chart2.width()*3 // 4, y + 50)))

    y = chart2.top + third*2 - 5

    weekTitle = titleFont.render("WEEK", True, (120, 255, 120))
    screen.blit(weekTitle, weekTitle.get_rect(center = (chart2.left + chart2.width() // 2, y + 35)))

    weekHighLabel = labelFont.render("High", True, (120, 255, 120))
    weekLowLabel = labelFont.render("Low", True, (120, 255, 120))
    weekHighValue = valueFont.render(f"{weekHigh:.2f} ft", True, (120, 255, 120))
    weekLowValue = valueFont.render(f"{weekLow:.2f} ft", True, (120, 255, 120))

    screen.blit(weekHighLabel, weekHighLabel.get_rect(center = (chart2.left + chart2.width() // 4, y + 20)))
    screen.blit(weekLowLabel, weekLowLabel.get_rect(center = (chart2.left + chart2.width()*3 // 4, y + 20)))
    screen.blit(weekHighValue, weekHighValue.get_rect(center = (chart2.left + chart2.width() // 4, y + 50)))
    screen.blit(weekLowValue, weekLowValue.get_rect(center = (chart2.left + chart2.width()*3 // 4, y + 50)))

def drawAxisTicks(chart, tideData):
    heights = [point["height"] for point in tideData]
    displayMin = min(heights) - .5
    displayMax = max(heights) + .5
    numTicks = 6
    for i in range(numTicks + 1):
        height = displayMin + (displayMax - displayMin) * i / numTicks
        y = chart.bottom - (height - displayMin) / (displayMax - displayMin) * chart.height()
        drawLine((chart.left - 5, y), (chart.left, y), (55, 55, 55))
        drawLine((chart.left, y), (chart.right, y), (55, 55, 55))

        label = valueFont.render(f"{height:.1f}", True, (255, 255, 255, 100))
        screen.blit(label, (chart.left - 10 - label.get_width(), y - label.get_height() // 2))

def drawChartAxis():
    drawLine((chart1.left, chart1.top), (chart1.left, chart1.bottom), (180, 180, 180))
    drawLine((chart1.left, chart1.bottom), (chart1.right, chart1.bottom), (180, 180, 180))

    drawLine((chart3.left, chart3.top), (chart3.left, chart3.bottom), (180, 180, 180))
    drawLine((chart3.left, chart3.bottom), (chart3.right, chart3.bottom), (180, 180, 180))

    drawAxisTicks(chart1, todayData)
    drawAxisTicks(chart3, weekData)

def drawInfoLayout():
    drawInfoPanel()

    drawChart(chart1)
    drawChart(chart3)

    drawChartAxis()

    chart1.drawCurrentLine(currentHours)
    chart3.drawCurrentLine(currentHours)

hiloData = loadData()

todayData = [p for p in hiloData if p["hours"] <= 24]
weekData = [p for p in hiloData if p["hours"] <= 24 * 7]
monthData = hiloData

todayHigh = max(p["height"] for p in todayData)
todayLow = min(p["height"] for p in todayData)

weekHigh = max(p["height"] for p in weekData)
weekLow = min(p["height"] for p in weekData)

todayGraphData = makeDetailedTideData(todayData)

chart1.buildGraph(todayGraphData)
chart3.buildGraph(weekData)

clock = pygame.time.Clock()
titleFont = pygame.font.Font(None, 24)
valueFont = pygame.font.Font(None, 34)
labelFont = pygame.font.Font(None, 20)

currentHours = getCurrentTime(hiloData)
lastUpdate = pygame.time.get_ticks()

maxHours = max(t["hours"] for t in hiloData)
maxHeight = max(t["height"] for t in hiloData) + 0.2
minHeight = min(t["height"] for t in hiloData) - 0.2

currentHeight = getCurrentHeight(monthData, currentHours)

for chart in (chart1, chart2, chart3):
    chart.displayPoints = [(x, chart.bottom) for x, y in chart.targetPoints]

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    now = pygame.time.get_ticks()
    if now - lastUpdate >= 1000:
        currentHours = getCurrentTime(hiloData)
        lastUpdate = now

    currentHours = getCurrentTime(monthData)

    screen.fill((135, 190, 200))

    drawInfoLayout()

    for chart in (chart1, chart3):
        for i in range(len(chart.displayPoints)):
            dx, dy = chart.displayPoints[i]
            tx, ty = chart.targetPoints[i]

            chart.displayPoints[i] = (lerp(dx, tx, 0.05), lerp(dy, ty, 0.05))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
