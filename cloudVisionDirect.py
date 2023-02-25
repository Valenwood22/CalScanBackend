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
                             "features":[{"type":"TEXT_DETECTION","maxResults":1}]}]}

        if live:
            response = requests.post(url, data=json.dumps(body), headers={'Accept': 'application/json','Content-Type': 'application/json'})
            #### TEXT DETECTION ######
            response_text = json.loads(response.content)['responses'][0]

            path = f"{os.getcwd()}"
            filePath = path + f"{imageName}_response.pickle"
            save = open(filePath, "wb")
            pickle.dump(response_text, save)

        else:
            path = f"{os.getcwd()}"
            save = open(path + f"/{imageName}_response.pickle", "rb")
            response_text = pickle.load(save)
            image_path = f'{imageName}.jpg'
            image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)


        phrases = response_text['textAnnotations'][0]['description'].split('\n')

        if debugPath:
            with open(f'{debugPath}/log.txt', 'a', encoding="utf-8") as f:
                print(phrases)
                f.write(f"Raw phrases: {phrases}\n")

        out = []
        i = 1
        wordIndex = 0
        # while i < len(response_text['textAnnotations'])-1:
        while i < len(phrases)-1:

            words = len(phrases[wordIndex].strip().split(' '))
            for j in range(words):
                r = response_text['textAnnotations'][i]
                c1, c2, c3, c4 = [(bound['x'], bound['y']) for bound in r['boundingPoly']['vertices']]

                if debugPath: cv2.rectangle(image, c3, c1, 255, 2)
                # print(phrases[i], words)
                if j == 0:
                    out.append({"text": [r['description']],"days": [(c1, c3)]})
                else:
                    out[-1]["text"].append(r['description'])
                    out[-1]["days"].append((c1, c3))

                i += 1
            wordIndex += 1

        end = time.time()
        print(f"Time to generate Text {(end - start) * 1000:.2f}ms")
        if debugPath: cv2.imwrite(f'{debugPath}/5{imageName}B.jpg', image)
        # print(out)
        self.text = out

if __name__ == '__main__':
    OCR(live=False)
