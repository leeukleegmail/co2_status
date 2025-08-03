CONTAINER_NAME="co2_status_flask"

CO2_SOCKET=19
BRIDGE_IP="192.168.178.158"
SCRIPT_NAME="main.py"
SERVER_PORT=5002

docker stop $CONTAINER_NAME
docker rm $CONTAINER_NAME
docker build --tag $CONTAINER_NAME --build-arg container_name=$CONTAINER_NAME .
docker run -d -p 5002:$SERVER_PORT --name $CONTAINER_NAME --env CO2_SOCKET=$CO2_SOCKET --env BRIDGE_IP=$BRIDGE_IP --env SERVER_PORT=$SERVER_PORT --env SCRIPT_NAME=$SCRIPT_NAME --restart unless-stopped -v $(pwd)/:/$CONTAINER_NAME $CONTAINER_NAME

