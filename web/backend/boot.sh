python user-service/main.py &
python function-service/main.py &
python workflow-service/main.py &
python deploy-service/main.py &
python deploy-service/test_service.py &
python stats-service/main.py &

tail -f /dev/null
