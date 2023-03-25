import os
import pickle
import time
import requests
import json
import base64
import cv2

class OCR:
    def __init__(self, imageName="C4", debugPath=None, live=False):
        start = time.time()


        # url = 'https://vision.googleapis.com/v1/images:annotate?key=AIzaSyASxWE3KwtTQwPtslPKrn1WwrSnTzkG0iM'
        url = 'https://vision.googleapis.com/v1/images:annotate?key=AIzaSyBxxlsGHlzhtFdMvfhAHuP0Cx9DhVoLsco'
        path = f'{imageName}.jpg'
        image = cv2.imread(path)

        # convert image to base64
        img_data = open('C4.jpg', 'rb')
        image_read = img_data.read()
        image_64_encode = base64.encodebytes(image_read)

        # prepare headers for http request
        body = {"requests":[{"image":{"content":image_64_encode.decode("utf-8")},
                             "features":[{"type":"TEXT_DETECTION", "maxResults": 1}]}]}

        if live:
            response = requests.post(url, data=json.dumps(body), headers={'Accept': 'application/json','Content-Type': 'application/json'})
            #### TEXT DETECTION ######
            response_text = json.loads(response.content)['responses'][0]

            path = f"{os.getcwd()}/CalScanBackend"
            filePath = path + f"{imageName}_response.pickle"
            print(filePath)
            with open(filePath, "wb") as f:
                pickle.dump(response_text, f)

        else:
            path = f"{os.getcwd()}"
            save = open(path + f"/{imageName}_response.pickle", "rb")
            response_text = pickle.load(save)
            image_path = f'{imageName}.jpg'
            image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)


        blocks = response_text['fullTextAnnotation']['pages'][0]['blocks']


        if debugPath:
            with open(f'{debugPath}/log.txt', 'a', encoding="utf-8") as f:
                # print(blocks)
                f.write(f"Raw phrases: {blocks}\n")

        out = []
        for block in blocks:
            c1b, c2b, c3b, c4b = [(bound['x'], bound['y']) for bound in block['boundingBox']['vertices']]
            # cv2.rectangle(image, c3b, c1b, 255, 2)
            for paragraph in block['paragraphs']:
                c1p, c2p, c3p, c4p = [(bound['x'], bound['y']) for bound in paragraph['boundingBox']['vertices']]
                # cv2.rectangle(image, c3p, c1p, (255,255,0), 2)
                for word in paragraph['words']:
                    c1w, c2w, c3w, c4w = [(bound['x'], bound['y']) for bound in word['boundingBox']['vertices']]
                    # cv2.rectangle(image, c3w, c1w, (255, 0, 255), 2)
                    out.append({"text": self.buildWord(word), "days":(c1w, c3w)})


        end = time.time()

        print(f"Time to generate Text {(end - start) * 1000:.2f}ms")
        if debugPath: cv2.imwrite(f'{debugPath}/5{imageName}B.jpg', image)
        # print(out)
        self.text = out

    def buildWord(self, word):
        strWord = ""
        for symbol in word['symbols']:
            strWord += symbol['text'].strip()
        return strWord


if __name__ == '__main__':
    OCR(live=False, debugPath="C:\\Users\\jxgisi\\PycharmProjects\\CalScanBackend\\deepData")
