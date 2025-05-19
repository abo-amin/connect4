# Connect4 Docker Hub Deployment Script for Windows

# Set these variables
$DOCKERHUB_USERNAME = "sherifyani"
$IMAGE_NAME = "connect4-app"
$VERSION = "1.0.0"

# Build the Docker image
Write-Host "🔨 Building Docker image..." -ForegroundColor Cyan
docker build -t $IMAGE_NAME .

# Tag the image with version
Write-Host "🏷️ Tagging image..." -ForegroundColor Cyan
docker tag $IMAGE_NAME "${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${VERSION}"
docker tag $IMAGE_NAME "${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest"

# Log in to Docker Hub (will prompt for password)
Write-Host "🔑 Logging in to Docker Hub as $DOCKERHUB_USERNAME..." -ForegroundColor Yellow
docker login -u $DOCKERHUB_USERNAME

# Push the image to Docker Hub
Write-Host "⬆️ Pushing image to Docker Hub..." -ForegroundColor Green
docker push "${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${VERSION}"
docker push "${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest"

Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "Image available at: https://hub.docker.com/r/${DOCKERHUB_USERNAME}/${IMAGE_NAME}" -ForegroundColor Cyan
Write-Host ""
Write-Host "To run this image:" -ForegroundColor Yellow
Write-Host "docker run -d -p 5000:5000 -v ${PWD}/instance:/app/instance ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest" -ForegroundColor White
