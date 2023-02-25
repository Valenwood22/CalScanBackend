import cv2

class point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class rectangle:
    def __init__(self, top_right_X, top_right_Y, bottom_left_X, bottom_left_Y):
        self.top_left = point(top_right_X, top_right_Y)
        self.bottom_right = point(bottom_left_X, bottom_left_Y)
        self.dayOfMonth = -1
        self.prediction_error = float('inf')
        self.confidence = -1

    def __str__(self):
        return f"DoM: {self.dayOfMonth} \t Error:{self.prediction_error:.0f} \t Conf:{self.confidence} \t"


class library:

    @staticmethod
    def doOverlap(rectArray, l2x, l2y, r2x, r2y):
        if len(rectArray) == 0:
            return True
        for other in rectArray:
            # If one rectangle is on left side of other
            if not ((other.top_left.x >= r2x or l2x >= other.bottom_right.x) or
                    (-other.bottom_right.y >= -l2y or -r2y >= -other.top_left.y)):
                return False
        return True



    @staticmethod
    def printGrid(grid):
        for row in grid:
            print(row)



    @staticmethod
    def findGridPos(rowBounds, colBounds, rec):
        colIndex = -1
        for i, colBound in enumerate(colBounds):
            if colBound[0] < rec.top_left.x < colBound[1]:
                colIndex = i
                break

        rowIndex = -1
        for j, rowBound in enumerate(rowBounds):
            if rowBound[0] < rec.top_left.y < rowBound[1]:
                rowIndex = j
                break

        return rowIndex,colIndex



    @staticmethod
    def removeGridColorRow(grid, i, rowOrCol, image, h):
        if rowOrCol == "row":
            removedRow = grid.pop(i)
            for square in removedRow:
                if square:
                    cv2.putText(image, 'X', (square.top_left.x, square.top_left.y+h), cv2.FONT_HERSHEY_SIMPLEX, 4, (255, 255, 0), 2, cv2.LINE_AA)
            return grid
        if rowOrCol == "col":
            for col in grid:
                square = col.pop(i)
                if square:
                    cv2.putText(image, 'X', (square.top_left.x, square.top_left.y+h), cv2.FONT_HERSHEY_SIMPLEX, 4, (255, 255, 0), 2, cv2.LINE_AA)

            return grid



    @staticmethod
    def fillGrid(grid, rowBounds, colBounds,w,h,image):
        for i, row in enumerate(grid):
            for j, pt in enumerate(row):
                if pt is None:
                    pointX = (colBounds[j][0] + colBounds[j][1])//2
                    pointY = (rowBounds[i][0] + rowBounds[i][1])//2
                    grid[i][j] = rectangle(pointX,pointY,pointX+w, pointY+h)
                    cv2.rectangle(image, (pointX, pointY), (pointX+w, pointY+h), (0,255,0), 2)

        return grid



    @staticmethod
    def addColRowLines(image, rowBouds, colBouds):
        height, width, channel = image.shape
        for row in rowBouds:
            cv2.line(image, (0,row[0]),(width,row[0]), (0, 0, 255), 2)
            cv2.line(image, (0,row[1]),(width,row[1]), (0, 0, 255), 2)
        for col in colBouds:
            cv2.line(image, (col[0],0),(col[0],height), (0, 0, 255), 2)
            cv2.line(image, (col[1],0),(col[1],height), (0, 0, 255), 2)


    @staticmethod
    def filterWords(i, j, textMap, day):
        def hasOneLetterOrColon(s):
            for c in s:
                if c.isalpha() or c == ":":
                    return True
            return False

        events = []
        for word in textMap[i+1][j+1]:
            if word == str(day.dayOfMonth): # filter out the day of the month
                # show words thrown out here
                continue
            if not hasOneLetterOrColon(word):
                # show words thrown out here
                continue
            if not word.isascii():
                # show words thrown out here
                continue
            events.append(word)


        return events # [word for word in textMap[i + 1][j + 1] if (word != str(day.dayOfMonth))]