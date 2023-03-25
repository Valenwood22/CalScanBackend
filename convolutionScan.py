
import numpy as np
import cv2
from matplotlib import pyplot as plt
import companion
import time


class Scan:
    def __init__(self, imageName="C4", debug=False, debugPath=None):
        # hy = hpy()
        start = time.time()
        path = f'{imageName}.jpg'
        image = cv2.imread(path)

        # convert the image to grayscale, blur it, and find edges in the image
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        kernel = np.ones((5, 5), np.uint8)
        gray = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
        edged = cv2.Canny(gray, 100, 200)
        cv2.imwrite(f'{imageName}B.jpg', edged)
        if debugPath: cv2.imwrite(f'{debugPath}/1{imageName}B.jpg', edged)

        # Load in template
        template_path = 'crossSectionTemplate.jpg'
        template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)[:,:,0]
        w = h = template.shape[0]
        image_path = f'{imageName}B.jpg'
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

        result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED, mask=None)

        """
        1. Remove all the overlapping boxes and remove them
        2. Create a 2d grid based on each point
        3. Find the distances between each of the squares vertical and horizontal
        4. Get a winner distance
        5. For each point create a box of that distance 
        """

        library = companion.library()
        threshold = 0.45
        loc = np.where( result >= threshold)
        rectangles = []
        for i, pt in enumerate(zip(*loc[::-1])): # 27
            if library.doOverlap(rectangles, pt[0],pt[1],pt[0] + w, pt[1] + h):
                rectangles.insert(0, companion.rectangle(pt[0],pt[1],pt[0] + w, pt[1] + h))
                cv2.rectangle(image, (pt[0], pt[1]), (pt[0] + w, pt[1] + h), 255, 2)
        if debugPath:
            with open(f'{debugPath}/log.txt', 'a') as f:
                f.write(f"Number of Intersections Found: {len(rectangles)}\n")

        if debugPath: cv2.imwrite(f'{debugPath}/2{imageName}R.jpg', image)
        # print(len(rectangles))

        # Step 2 Create Grid
        grid = []
        offset = 30
        colBounds = [(rectangles[0].top_left.x-w-offset, rectangles[0].top_left.x+w+offset)]
        rowBounds = [(rectangles[0].top_left.y-h-offset, rectangles[0].top_left.y+h+offset)]
        for rec in rectangles[1:]:
            # cols
            setColBound = True
            for colBound in colBounds:
                if colBound[0] < rec.top_left.x < colBound[1]:
                    setColBound = False
                    break
            if setColBound: colBounds.append((rec.top_left.x - h-offset, rec.top_left.x + h+offset))
            # rows
            setRowBound = True
            for rowBound in rowBounds:
                if rowBound[0] < rec.top_left.y < rowBound[1]:
                    setRowBound = False
                    break
            if setRowBound: rowBounds.append((rec.top_left.y - h-offset, rec.top_left.y + h+offset))

        colBounds.sort(key=lambda x:x[0])
        rowBounds.sort(key=lambda x:x[0])
        grid = [[None for _ in range(len(colBounds))]for _ in range(len(rowBounds))]
        for rec in rectangles:
            i,j = library.findGridPos(rowBounds,colBounds,rec)
            grid[i][j] = rec

        if debugPath:
            linedImage = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            library.addColRowLines(linedImage, rowBounds, colBounds) # DEBUG
            cv2.imwrite(f'{debugPath}/3{imageName}L.jpg', linedImage)
        # library.printGrid(grid)

        # get median row and column value
        rowValues = []
        colValues = []
        for i, row in enumerate(grid):
            for j, rec in enumerate(row):
                if rec and j+1<len(row):
                    if row[j+1]:
                        rowValues.append(row[j+1].top_left.x-rec.top_left.x)

                if rec and i+1 < len(grid):
                    if grid[i+1][j]:
                        colValues.append(grid[i+1][j].top_left.y-rec.top_left.y)

        rowValues.sort()
        colValues.sort()
        keyRowLength = rowValues[len(rowValues)//2]
        keyColLength = colValues[len(colValues)//2]

        if debugPath:
            with open(f'{debugPath}/log.txt', 'a') as f:
                f.write(f"Key Row Length (the median distance between 2 row intersections): {keyRowLength}\n")
                f.write(f"Key Col Length (the median distance between 2 col intersections): {keyColLength}\n")

        # print("key row length",keyRowLength)
        # print("key col length",keyColLength)
        # library.printGrid(grid)
        # print()
        # print()

        for i, row in enumerate(grid[:-1]):
            for j, pt in enumerate(row[:-1]):
                if pt:
                    # Find bad columns
                    poi = pt.top_left.x + keyRowLength
                    removeCol = j
                    for rng in colBounds:
                        if rng[0] <= poi <= rng[1]:
                            removeCol = -1
                            break
                    if removeCol != -1:
                        grid = library.removeGridColorRow(grid, removeCol, "col", image, w)
                        colBounds.pop(j)

                    # Find bad rows
                    poi = pt.top_left.y + keyColLength
                    removeRow = i
                    for rng in rowBounds:
                        if rng[0] <= poi <= rng[1]:
                            removeRow = -1
                            break
                    if removeRow != -1:
                        if removeRow == len(grid)-2: # special case if we are on the last row ie. what if the bottom row is out of alignment
                            grid = library.removeGridColorRow(grid, removeRow+1, "row", image, h)
                            rowBounds.pop(removeRow+1)
                        else:
                            grid = library.removeGridColorRow(grid, removeRow, "row", image, h)
                            rowBounds.pop(removeRow)
                        break


        grid = library.fillGrid(grid, rowBounds, colBounds,w,h, image)

        end = time.time()
        print(f"Time to generate Calendar Grid {(end-start)*1000:.2f}ms")

        if debugPath: cv2.imwrite(f'{debugPath}/4{imageName}F.jpg', image)

        # print(keyRowLength)
        # print(keyColLength)


        if debug:
            library.printGrid(grid)
            wn = image_path.split('.')[0]+"out.jpg"
            cv2.imwrite(wn,image)
            plt.subplot(111), plt.imshow(image, cmap='gray')
            plt.title('Step1: Detected Point'), plt.xticks([]), plt.yticks([])
            plt.show()

        self.grid = grid
        # print(hy.heap().all)

if __name__ == '__main__':
    Scan()