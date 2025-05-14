#!/bin/bash
# Connect4 Docker Hub Deployment Script

# Set these variables
DOCKERHUB_USERNAME="Sherif_Talaat"
IMAGE_NAME="connect4-app"
VERSION="1.0.0"

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t $IMAGE_NAME .

# Tag the image with version
echo "🏷️ Tagging image..."
docker tag $IMAGE_NAME $DOCKERHUB_USERNAME/$IMAGE_NAME:$VERSION
docker tag $IMAGE_NAME $DOCKERHUB_USERNAME/$IMAGE_NAME:latest

# Log in to Docker Hub (will prompt for password)
echo "🔑 Logging in to Docker Hub..."
docker login -u $DOCKERHUB_USERNAME

# Push the image to Docker Hub
echo "⬆️ Pushing image to Docker Hub..."
docker push $DOCKERHUB_USERNAME/$IMAGE_NAME:$VERSION
docker push $DOCKERHUB_USERNAME/$IMAGE_NAME:latest

echo "✅ Deployment complete!"
echo "Image available at: https://hub.docker.com/r/$DOCKERHUB_USERNAME/$IMAGE_NAME"
echo ""
echo "To run this image:"
echo "docker run -d -p 5000:5000 -v ./instance:/app/instance $DOCKERHUB_USERNAME/$IMAGE_NAME:latest"
