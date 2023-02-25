import math
import os

from convolutionScan import Scan
from cloudVisionDirect import OCR
from collections import Counter
import re
import statistics
import json
from companion import library

class Engine():
    def __init__(self, debug=None, live=False):
        # TODO: add top half am bottom half pm
        calendarGrid = Scan(imageName="C4", debugPath=debug).grid
        ocr = OCR(debugPath=debug,  live=live).text
        # print(ocr)
        # print(calendarGrid)
        textMap = [[[] for i in range(len(calendarGrid[0])+1)] for j in range(len(calendarGrid)+1)]
        monthCtr = Counter()
        months = {'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'}
        errorReadings = []

        for item in ocr:
            # 1. Find what rows the text spans
            startRow = -1
            endRow = -1
            for i, row in enumerate(calendarGrid):
                if item['days'][0][0][1] <= row[0].top_left.y and startRow == -1:
                    startRow = i
                if item['days'][0][1][1] <= row[0].top_left.y and endRow == -1:
                    endRow = i
            if startRow == -1: startRow = len(calendarGrid)
            if endRow == -1: endRow = len(calendarGrid)

            if debug:
                with open(f'{debug}/log.txt', 'a', encoding="utf-8") as f:
                    f.write(f"{item['text']} spans rows {startRow} - {endRow}\n")
                    # print(item['text'],"spans rows",startRow, "-",endRow)

            # 2. Find what columns the text spans
            startCol = -1
            endCol = -1
            for j, days in enumerate(calendarGrid[0]):
                if item['days'][0][0][0] <= days.top_left.x and startCol == -1:
                    startCol = j
                if item['days'][0][1][0] <= days.top_left.x and endCol == -1:
                    endCol = j
            if startCol == -1: startCol = len(calendarGrid[0])
            if endCol == -1: endCol = len(calendarGrid[0])

            if debug:
                with open(f'{debug}/log.txt', 'a', encoding="utf-8") as f:
                    f.write(f"{item['text']} spans cols {startCol} - {endCol}\n")
                    # print(item['text'],"spans cols", startCol, "-", endCol)

            # 3. put the words in the correct day
            for i in range(startRow,endRow+1):
                for j in range(startCol,endCol+1):
                    textMap[i][j].append(' '.join(item['text']))

            # 4. predict what day of the moth it is
            pureText = re.sub(r'[^\w\s]', '', ''.join(item['text']))
            if pureText.strip().isnumeric() and len(pureText.strip()) < 3:
                localDistanceError = float('inf')
                dayAnswer = []
                for i, row in enumerate(calendarGrid):
                    for j, day in enumerate(row):
                        # get the distance from the current grid number
                        distance = math.hypot(day.top_left.x - item['days'][0][0][0], day.top_left.y - item['days'][0][0][1])
                        if distance < localDistanceError:
                            dayAnswer = [i,j]
                            localDistanceError = distance

                calendarGrid[dayAnswer[0]][dayAnswer[1]].dayOfMonth = int(pureText.strip())
                calendarGrid[dayAnswer[0]][dayAnswer[1]].prediction_error = localDistanceError
                if localDistanceError != float('inf'): errorReadings.append(localDistanceError)


        # 5. update the month counter
        monthList = []
        for row in textMap:
            for day in row:
                for words in day:
                    wordSplit = words.split(' ')
                    for word in wordSplit:
                        if word.lower() in months:
                            monthList.append(word.lower())

        monthCtr.update(monthList)
        try:
            monthEstimate = monthCtr.most_common(1)[0][0]
            with open(f'{debug}/log.txt', 'a') as f:
                f.write(f"Month Counters: {monthCtr}\n")
                f.write(f"Month Estimate: {monthEstimate}\n")
        except:
            monthEstimate = "None"
            if debug:
                with open(f'{debug}/log.txt', 'a') as f:
                    f.write(f"ERROR: no month estimate\n")



        # get the confidence that is the right month
        averageError = statistics.mean(errorReadings)

        # Find the initial confidence
        for i, row in enumerate(calendarGrid):
            for j, day in enumerate(row):
                if day.dayOfMonth == -1:
                    day.confidence = 0
                    continue
                confidence = 0
                total = 0
                # 1. find the average distance from the number
                if day.prediction_error <= averageError:
                    confidence += 1
                total += 1

                # 2. look in all possible directions
                if i > 0:
                    if calendarGrid[i-1][j].dayOfMonth == day.dayOfMonth - 7:
                        confidence += 1
                    total += 1
                if i < len(calendarGrid)-1:
                    if calendarGrid[i + 1][j].dayOfMonth == day.dayOfMonth + 7:
                        confidence += 1
                    total += 1
                if j > 0:
                    if calendarGrid[i][j-1].dayOfMonth == day.dayOfMonth - 1:
                        confidence += 1
                    total += 1
                if j < len(calendarGrid[0])-1:
                    if calendarGrid[i][j+1].dayOfMonth == day.dayOfMonth + 1:
                        confidence += 1
                    total += 1
                day.confidence = confidence/total

        # Backfill days with low confidence
        visited = set()
        cntr = 0
        while len(visited) < len(calendarGrid)*len(calendarGrid[0]) and cntr < len(calendarGrid)*len(calendarGrid[0]):
            for i, row in enumerate(calendarGrid):
                for j, day in enumerate(row):
                    if str(f"{i}{j}") not in visited:
                        if day.confidence >= 0.5:
                            visited.add(f"{i}{j}")
                            cntr += 1
                        else:
                            predictions = []
                            if i > 0:
                                if calendarGrid[i - 1][j].confidence >= 0.5:
                                    predictions.append(calendarGrid[i - 1][j].dayOfMonth + 7)
                            if i < len(calendarGrid) - 1:
                                if calendarGrid[i + 1][j].confidence >= 0.5:
                                    predictions.append(calendarGrid[i + 1][j].dayOfMonth - 7)
                            if j > 0:
                                if calendarGrid[i][j - 1].confidence >= 0.5:
                                    predictions.append(calendarGrid[i][j - 1].dayOfMonth + 1)
                            if j < len(calendarGrid[0]) - 1:
                                if calendarGrid[i][j + 1].confidence >= 0.5:
                                    predictions.append(calendarGrid[i][j + 1].dayOfMonth - 1)

                            predCounter = Counter(predictions)
                            if len(predictions) >= 2 and len(predCounter) == 1:
                                day.dayOfMonth = predCounter.most_common(1)[0][0]
                                visited.add(f"{i}{j}")
            cntr += 1
        # for row in textMap:
        #     print(row)
        # Create JSON string
        jsonDict = {"Month":monthEstimate}
        if debug:
            with open(f'{debug}/log.txt', 'a') as f:
                f.write("\n")
                for i, row in enumerate(calendarGrid):
                    for j, day in enumerate(row):
                        if day.dayOfMonth != -1:
                            jsonDict[f"Day {day.dayOfMonth}"] = [word for word in textMap[i+1][j+1] if(word != str(day.dayOfMonth))]
                        f.write(f"{day} - ")
                    f.write("\n")
        else:
            for i, row in enumerate(calendarGrid):
                for j, day in enumerate(row):
                    if day.dayOfMonth != -1:
                        event = library.filterWords(i, j, textMap, day)
                        if len(event)>0:
                            jsonDict[f"Day {day.dayOfMonth}"] = {}
                            # [word for word in textMap[i + 1][j + 1] if (word != str(day.dayOfMonth))]



        jsonReturn = json.dumps(jsonDict)

        # print(f"The month is '{monthEstimate}'")
        # print(f"Average Error '{averageError}'")
        # for row in calendarGrid:
        #     for day in row:
        #         print(f"[{day}]", end='')
        #     print()
        if debug:
            with open(f'{debug}/log.txt', 'a', encoding="utf-8") as f:
                f.write(f"\n{jsonDict}")
        self.response = jsonReturn
        print(self.response)

    def returnResponse(self):
        return self.response

if __name__ == '__main__':
    Engine(live=False)
