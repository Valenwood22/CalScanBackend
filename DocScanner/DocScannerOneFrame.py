import base64

import cv2
import numpy as np
import utlis

class findFrame:
    def __init__(self, path):
        ########################################################################
        # pathImage = "chess_club.JPG"
        self.pathImage = "DocScanner/" + path
        print(self.pathImage)
        self.img = cv2.imread(self.pathImage)
        self.widthImg = 1280 # 4032
        self.heightImg = 720 # 3024
        self.thres1 = 200
        self.thres2 = 200
        self.out_image = None
        ########################################################################

        # utlis.initializeTrackbars()
        self.count = 0
        self.foundThresh = False

    def run(self):
        while not self.foundThresh:

            img = cv2.resize(self.img, (self.widthImg, self.heightImg))  # RESIZE IMAGE
            imgBlank = np.zeros((self.heightImg, self.widthImg, 3), np.uint8)  # CREATE A BLANK IMAGE FOR TESTING DEBUGING IF REQUIRED
            imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # CONVERT IMAGE TO GRAY SCALE
            imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 1)  # ADD GAUSSIAN BLUR
            # thres = utlis.valTrackbars()  # GET TRACK BAR VALUES FOR THRESHOLDS
            imgThreshold = cv2.Canny(imgBlur, self.thres1, self.thres2)  # APPLY CANNY BLUR
            kernel = np.ones((5, 5))
            imgDial = cv2.dilate(imgThreshold, kernel, iterations=2)  # APPLY DILATION
            imgThreshold = cv2.erode(imgDial, kernel, iterations=1)  # APPLY EROSION

            ## FIND ALL COUNTOURS
            imgContours = img.copy()  # COPY IMAGE FOR DISPLAY PURPOSES
            imgBigContour = img.copy()  # COPY IMAGE FOR DISPLAY PURPOSES
            contours, hierarchy = cv2.findContours(imgThreshold, cv2.RETR_EXTERNAL,
                                                   cv2.CHAIN_APPROX_SIMPLE)  # FIND ALL CONTOURS
            cv2.drawContours(imgContours, contours, -1, (0, 255, 0), 10)  # DRAW ALL DETECTED CONTOURS

            # FIND THE BIGGEST COUNTOUR
            biggest, maxArea = utlis.biggestContour(contours)  # FIND THE BIGGEST CONTOUR
            if biggest.size != 0:
                biggest = utlis.reorder(biggest)
                cv2.drawContours(imgBigContour, biggest, -1, (0, 255, 0), 20)  # DRAW THE BIGGEST CONTOUR
                imgBigContour = utlis.drawRectangle(imgBigContour, biggest, 2)
                pts1 = np.float32(biggest)  # PREPARE POINTS FOR WARP
                pts2 = np.float32([[0, 0], [self.widthImg, 0], [0, self.heightImg], [self.widthImg, self.heightImg]])  # PREPARE POINTS FOR WARP
                matrix = cv2.getPerspectiveTransform(pts1, pts2)
                imgWarpColored = cv2.warpPerspective(img, matrix, (self.widthImg, self.heightImg))

                # REMOVE 20 PIXELS FORM EACH SIDE
                imgWarpColored = imgWarpColored[20:imgWarpColored.shape[0] - 20, 20:imgWarpColored.shape[1] - 20]
                imgWarpColored = cv2.resize(imgWarpColored, (self.widthImg, self.heightImg))

                # APPLY ADAPTIVE THRESHOLD
                imgWarpGray = cv2.cvtColor(imgWarpColored, cv2.COLOR_BGR2GRAY)
                imgAdaptiveThre = cv2.adaptiveThreshold(imgWarpGray, 255, 1, 1, 7, 2)
                imgAdaptiveThre = cv2.bitwise_not(imgAdaptiveThre)
                imgAdaptiveThre = cv2.medianBlur(imgAdaptiveThre, 3)

                # Image Array for Display
                imageArray = ([img, imgThreshold, imgContours],
                              [imgBigContour, imgWarpColored, imgAdaptiveThre])
                self.foundThresh = True
                cv2.imwrite("DocScanner/ff.jpg", imgWarpColored)

                # retval, buffer = cv2.imencode('.jpg',imgWarpColored)
                self.out_image = "DocScanner/ff.jpg"

            else:
                if not self.foundThresh:
                    if self.thres1 < self.thres2:
                        self.thres2 -= 10
                    else:
                        self.thres1 -= 10
                    if self.thres1 <= -1 and self.thres2 <= -1:
                        thres1 = 0
                        thres2 = 0
                        print("No Valid thres")
                imageArray = ([img, imgThreshold, imgContours],
                              [imgBlank, imgBlank, imgBlank])

            # stackedImage = utlis.stackImages(imageArray, 0.3)
            # cv2.imshow("Result", stackedImage)
            #
            # # SAVE IMAGE WHEN 's' key is pressed
            # if cv2.waitKey(1) and 0xFF == ord('s'):
            #     cv2.imwrite("Scanned/myImage" + str(self.count) + ".jpg", imgWarpColored)



if __name__ == '__main__':
    ff = findFrame()
    ff.run()
