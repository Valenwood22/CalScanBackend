from datetime import datetime
import math
import os

import cv2
import enchant
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
        self.debug = debug
        calendarGrid = Scan(imageName="C4", debugPath=debug).grid

        # if self.debug:
        #     image_path = f'C4.jpg'
        #     image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        #     for row in calendarGrid:
        #         for dayBlock in row:
        #             cv2.rectangle(image, (dayBlock.top_left.x, dayBlock.top_left.y), (dayBlock.bottom_right.x, dayBlock.bottom_right.y), (255, 255, 0), 2)
        #     cv2.imwrite(f'{self.debug}/C4_showBlockDays.jpg', image)

        ocr = OCR(debugPath=debug,  live=live).text
        # print(ocr)
        # print(calendarGrid)
        textMap = [[[] for i in range(len(calendarGrid[0])+1)] for j in range(len(calendarGrid)+1)]
        self.months = {'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'}
        self.monthsMap = {'january': '01', 'february': '02', 'march': '03', 'april': '04', 'may': '05', 'june': '06',
                          'july': '07', 'august': '08', 'september': '09', 'october': '10', 'november': '11',
                          'december': '12'}
        errorReadings = []

        # 1. Predict Month and year
        monthEstimate = self.predictMonth(ocr)
        yearEstimate = self.predictYear()

        for item in ocr:
            # 1. Find what rows the text spans
            startRow = -1
            endRow = -1
            for i, row in enumerate(calendarGrid):
                if item['days'][0][1] <= row[0].top_left.y and startRow == -1:
                    startRow = i
                if item['days'][1][1] <= row[0].top_left.y and endRow == -1:
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
                if item['days'][0][0] <= days.top_left.x and startCol == -1:
                    startCol = j
                if item['days'][1][0] <= days.top_left.x and endCol == -1:
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
                    textMap[i][j].append(item['text'])

            # 4. predict what day of the month it is
            pureText = re.sub(r'[^\w\s]', '', ''.join(item['text']))
            if pureText.strip().isnumeric() and len(pureText.strip()) < 3:
                localDistanceError = float('inf')
                dayAnswer = []
                for i, row in enumerate(calendarGrid):
                    for j, day in enumerate(row):
                        # get the distance from the current grid number
                        distance = math.hypot(day.top_left.x - item['days'][0][0], day.top_left.y - item['days'][0][1])
                        if distance < localDistanceError:
                            dayAnswer = [i,j]
                            localDistanceError = distance

                calendarGrid[dayAnswer[0]][dayAnswer[1]].dayOfMonth = int(pureText.strip())
                calendarGrid[dayAnswer[0]][dayAnswer[1]].prediction_error = localDistanceError
                if localDistanceError != float('inf'): errorReadings.append(localDistanceError)



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
        '''
        title: string
        start: iso string date (ex: 2023-02-26T00:11:40Z) 
        end: null | iso string date (ex: 2023-02-26T00:11:40Z) 
        attendees: null (for now) 
        location: null (for now) 
        reminders: null (for now) 
        allDay: bool
        multiDay: bool
        '''
        bookOfWords = enchant.Dict("en_US")
        jsonData = []
        if debug:
            with open(f'{debug}/log.txt', 'a', encoding="utf-8") as f:
                f.write("\n")
                for i, row in enumerate(calendarGrid):
                    for j, day in enumerate(row):
                        for word in textMap[i+1][j+1]:
                            if word.lower() != day.dayOfMonth:
                                if bookOfWords.check(word) and not word.isnumeric() and len(word) > 1:
                                    title = word
                                    start_iso_date = f'{yearEstimate}-{self.monthsMap[monthEstimate.lower()]}-{day.dayOfMonth}T00:00:00Z'
                                    end_iso_date = start_iso_date
                                    attendees = "null"
                                    location = "null"
                                    reminders = "null"
                                    allDay = "False"
                                    multiDay = "False"
                                    jsonData.append({"title": title, "start": start_iso_date, "end": end_iso_date,
                                     "attendees": attendees, "location": location, "reminders": reminders,
                                     "allDay": allDay, "multiDay": multiDay})
                                else:
                                    f.write(f"Not a word: {word}")
                        f.write(f"{day} - ")
                    f.write("\n")
        else:
            for i, row in enumerate(calendarGrid):
                for j, day in enumerate(row):
                    for word in textMap[i + 1][j + 1]:
                        if word.lower() != day.dayOfMonth:
                            if bookOfWords.check(word):
                                title = word
                                start_iso_date = f'{yearEstimate}-{self.monthsMap[monthEstimate.lower()]}-{day.dayOfMonth}T00:00:00Z'
                                end_iso_date = start_iso_date
                                attendees = "null"
                                location = "null"
                                reminders = "null"
                                allDay = "False"
                                multiDay = "False"
                                jsonData.append({"title": title, "start": start_iso_date, "end": end_iso_date,
                                                 "attendees": attendees, "location": location, "reminders": reminders,
                                                 "allDay": allDay, "multiDay": multiDay})
                                # [word for word in textMap[i + 1][j + 1] if (word != str(day.dayOfMonth))]



        jsonReturn = json.dumps(jsonData)

        # print(f"The month is '{monthEstimate}'")
        # print(f"Average Error '{averageError}'")
        # for row in calendarGrid:
        #     for day in row:
        #         print(f"[{day}]", end='')
        #     print()
        if debug:
            with open(f'{debug}/log.txt', 'a', encoding="utf-8") as f:
                f.write(f"\n{jsonData}")
        self.response = jsonReturn
        for item in jsonData:
            print(item)
        # print(self.response)

    def returnResponse(self):
        return self.response

    def predictMonth(self, ocr):
        surfaceArea = -1
        monthEstimate = "None"
        for item in ocr:
            if item['text'].lower() in self.months:
                h = item['days'][1][1] - item['days'][0][1]
                w = item['days'][1][0] - item['days'][0][0]
                if surfaceArea < h*w:
                    monthEstimate = item['text']
                    surfaceArea = h*w


                with open(f'{self.debug}/log.txt', 'a') as f:
                    f.write(f"Month SA: {surfaceArea}\n")
                    f.write(f"Month Estimate: {monthEstimate}\n")

        if monthEstimate == "None":
            with open(f'{self.debug}/log.txt', 'a') as f:
                f.write(f"No Months found\n")
            # set the month to the current month
            monthEstimate = datetime.now().month

        return monthEstimate

    def predictYear(self):
        return datetime.now().year

if __name__ == '__main__':
    Engine(live=False,  debug="C:\\Users\\jxgisi\\PycharmProjects\\CalScanBackend\\deepData")
