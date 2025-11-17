
# get rid of warning use for production environment
# CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "sop_ui.app:app"]


# make sure to mount volumes for /config, /data, /logs and utils