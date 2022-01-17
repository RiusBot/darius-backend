# darius-backend

```
# create your python3 virtual environment anaconda for conda
MY_SERVICE=prox3_internal
conda create --name ${MY_SERVICE} python=3.7

# activate your virtual environment
conda activate ${MY_SERVICE}

# install packages
pip install -r requirements.txt

# add config file to main/config/config.yaml (ask a teammate for help)

# start the microservice (in project root folder)
python -m main.src.server.service
```

# Swagger UI
http://localhost:8080/api/v1/ui

# TASK LIST
https://www.notion.so/1aaab7908e7d47dd9a49b516b12df4e9?v=de8f485cabdc455292b3e089ed014754

# Sceduler
* clean api - every day
* clean subscription - every day
* clean limit - every hour
* clean oco - every hour
