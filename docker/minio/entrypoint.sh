#!/bin/sh

# Start MinIO in the background
minio server /data --console-address ":9001" &

# Wait for MinIO to be ready before running the initialization script
until curl -s http://localhost:9000/minio/health/ready; do
    echo "Waiting for MinIO to be ready..."
    sleep 5
done

# Run the bucket setup script
sh /init-script.sh

# Keep the container running
wait $!
