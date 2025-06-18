#!/bin/sh

# Initialize Ollama with required models
set -e

echo "🚀 Starting Ollama model initialization..."

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
while ! curl -s http://ollama:11434/api/tags > /dev/null 2>&1; do
    echo "   Ollama not ready yet, waiting 5 seconds..."
    sleep 5
done

echo "✅ Ollama is ready!"

# Function to check if model exists
model_exists() {
    model_name=$1
    curl -s http://ollama:11434/api/tags | grep -q "\"name\":\"$model_name\""
}

# List of models to install
MODELS="codegemma:instruct"

# Pull each model if it doesn't exist
for model in $MODELS; do
    echo "🔍 Checking if model '$model' exists..."
    if model_exists "$model"; then
        echo "✅ Model '$model' already exists, skipping..."
    else
        echo "📥 Pulling model '$model'..."
        
        # Use curl to pull the model via API
        if curl -X POST http://ollama:11434/api/pull \
            -H "Content-Type: application/json" \
            -d "{\"name\":\"$model\"}" \
            --max-time 1800; then
            echo "✅ Successfully pulled model '$model'"
        else
            echo "❌ Failed to pull model '$model'"
            exit 1
        fi
    fi
done

echo "🎉 All models are ready!"

# List available models
echo "📋 Available models:"
curl -s http://ollama:11434/api/tags | grep -o '"name":"[^"]*"' | cut -d'"' -f4

echo "✅ Ollama initialization complete!"