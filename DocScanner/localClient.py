import requests
import base64

# addr = 'http://164.90.148.235:5000'
addr = 'http://127.0.0.1:5000'
url = addr + '/api/findFrame'

# prepare headers for http request
content_type = 'image/jpeg'
headers = {'content-type': content_type, 'image-name':'chess_club.JPG', 'live':'False'}

# img = cv2.imread('C4.jpg')
img_data = open('C4.jpg', 'rb')
image_read = img_data.read()
image_64_encode = base64.encodebytes(image_read)
print("sending post")
response = requests.get(url, data=image_64_encode, headers=headers)

# decode response
print(response.text)

