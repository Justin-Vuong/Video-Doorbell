import UploadVid
import Oauth
import MotionDetection

print("START")
yt_tokens = Oauth.getAuth()
#yt_tokens = {"token":"ya29.a0Adw1xeVVd3_TMZRQ4WFW5sS9HASyjUz2B7VfJSNoSSHXYKyPT0tuyFLYvNgTjq2PuSpvBtOFhAyLesXApvLAUAZfwRbUnv8j3sdtL_ns_38OEBVvV_-vUgNQUcjPFua3p0jHQ63vqQ3vGa7VYfM2h6JeOwoWf9wDxYM",
#             "refresh_token": "1//0dyhLx4SJFJMmCgYIARAAGA0SNwF-L9IrRufxw0ZCt4uUu_2Y52WWjiNx-NjO-3fQtly4FoWplJPZoiquXYH60ZT1Nw3QtPtsz1Y"}
apiData = Oauth.parseApiData()

yt = UploadVid.get_authenticated_service(yt_tokens["token"], yt_tokens["refresh_token"], apiData["client_id"], apiData["client_secret"])

MotionDetection.startCamera(yt)

print("good!")
