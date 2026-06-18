#!/bin/bash
pip install -r requirements.txt
python byte_project/manage.py collectstatic --noinput
