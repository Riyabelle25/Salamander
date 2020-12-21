<div align="center"><img src="https://github.com/Riyabelle25/Salamander/blob/master/scripts/static/static/assets/logo.png?raw=true"/></div>

# <div align="center">The Salamander Project</div>

<div align="center">The Perfect Gift is just a click way!!</div><br> 


Ever found yourself stumped- while gifting a new colleague at work or some distant family relation at a wedding)- and then end up going for Cadbury’s or that Bikaner vaali mithai hamper?
Here’s where we come in, with our Project Salamander. Salamander aims to recommend personalised gifts after analysing their social media preferences. 

The Salamander project encompasses our efforts to analyse a friend's Instagram profile, and then recommend gifts to the user for their friend.

<hr/>

### To test the code:

```bash
pip install -r requirements.txt
```

```bash
python manage.py runserver
```

Go to ```localhost:8000```

## Usage

#### INSTALL A DRIVER (LocalHost)
If you are running your code on a localhost, then you'll need to install a chromedriver from [here](https://chromedriver.chromium.org/downloads). Install and extract the chromedriver.exe file and save it in your project folder. Make sure to install the version that matches your Chrome version.
To check your chrome version, type ```chrome://version/``` in the chrome address bar.

#### SET ENVIROMENT VARIABLES (Web Server)
If you are running your code on a web server (Like Heroku), you should set the following enviroment variable:
- ```CHROMEDRIVER_PATH = /app/.chromedriver/bin/chromedriver```
- ```GOOGLE_CHROME_BIN = /app/.apt/usr/bin/google-chrome```
