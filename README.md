# ConTTudOwebProject

[![Build Status](https://travis-ci.org/ConTTudOweb/ConTTudOwebProject.svg?branch=master)](https://travis-ci.org/ConTTudOweb/ConTTudOwebProject)
[![Code Health](https://landscape.io/github/ConTTudOweb/ConTTudOwebProject/master/landscape.svg?style=flat)](https://landscape.io/github/ConTTudOweb/ConTTudOwebProject/master)
[![Coverage Status](https://coveralls.io/repos/github/ConTTudOweb/ConTTudOwebProject/badge.svg?branch=master)](https://coveralls.io/github/ConTTudOweb/ConTTudOwebProject?branch=master)


## How to develop?

1. Clone the repository;
2. Create a pipenv with Python 3.8.0;
3. Activate pipenv;
4. Install the dependencies;
5. Configure the instance with .env;
6. Run the tests;

```console
git clone https://github.com/ConTTudOweb/ConTTudOwebProject.git
cd ConTTudOwebProject
pipenv --three
pipenv shellre
pipenv install
cp contrib/env-sample .env
python manage.py test
```

```
python manage.py migrate_schemas --shared

python manage.py shell_plus
Client.objects.create(name="sandrofolk", schema_name="sandrofolk", domain_url="sandrofolk.conttudoweb.local")

python manage.py tenant_command createsuperuser --schema=sandrofolk

# Verificar pacotes desatualizados:
pipenv update --outdated
# Atualizar um pacote específico:
pipenv update PACOTE
# Atualizar todos os pacotes desatualizados:
pipenv update
```

```
# temas
python manage.py loaddata admin_interface_theme_bootstrap.json --schema=sandrofolk
python manage.py loaddata admin_interface_theme_foundation.json --schema=sandrofolk
python manage.py loaddata admin_interface_theme_uswds.json --schema=sandrofolk
```
