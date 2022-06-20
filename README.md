# darius-backend


# create your python3 virtual environment anaconda for conda
```
make init

* make init
  * make install-env  -> install pyenv, pipenv
  * make insatll      -> install packages
```
Or use conda
```
MY_SERVICE=prox3_internal
conda create --name ${MY_SERVICE} python=3.7
python -m pip install -r requirements.txt
```

# activate your virtual environment
```
make shell
```

# install gcloud
read commands in ```make install-gcloud``` need sudo to work

# add config file to main/config/config.yaml (ask a teammate for help)
```
* local reads from local config
* cloud reads from firestore config
```

# start the microservice (in project root folder)
* acquire credential file first
```
make start-local
```

# Swagger UI
http://localhost:8080/api/v1/ui


# Sceduler
* clean api - every day
* clean subscription - every day
* clean limit - every hour
* clean oco - every hour
* optimizer - every week
