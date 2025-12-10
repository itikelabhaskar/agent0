#!/bin/bash
# Usage: ./deploy.sh <PROJECT_ID> <SERVICE_NAME>
PROJECT_ID=$1
SERVICE_NAME=${2:-megalodon-backend}

gcloud builds submit --config cloudbuild.yaml --project $PROJECT_ID
gcloud run deploy $SERVICE_NAME \
  --project $PROJECT_ID \
  --region us-central1 \
  --allow-unauthenticated \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME
