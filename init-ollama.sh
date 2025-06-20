#!/bin/sh

# Initialize Ollama with required models and optimizations
set -e

echo "🚀 Starting Ollama model initialization..."

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while ! curl -s http://ollama:11434/api/tags > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "❌ Ollama failed to start after $MAX_RETRIES attempts"
        exit 1
    fi
    echo "   Ollama not ready yet, waiting 5 seconds... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 5
done

echo "✅ Ollama is ready!"

# Function to check if model exists
model_exists() {
    model_name=$1
    curl -s http://ollama:11434/api/tags | grep -q "\"name\":\"$model_name\""
}

# Function to create optimized model with performance parameters
create_optimized_model() {
    model_name=$1
    base_model=$2
    
    echo "🔧 Creating optimized model '$model_name' from '$base_model'..."
    
    # Create a Modelfile with optimized parameters
    cat > /tmp/Modelfile << EOF
FROM $base_model

# Performance optimizations
PARAMETER num_ctx 2048
PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1
PARAMETER num_predict 400
PARAMETER use_mmap true
PARAMETER use_mlock true

# System message for more focused responses
SYSTEM You are a code analysis assistant. Provide concise, actionable feedback on code performance and optimization. Keep responses under 300 words and focus on practical improvements.
EOF
    
    # Create the optimized model
    if curl -X POST http://ollama:11434/api/create \
        -H "Content-Type: application/json" \
        -d "{\"name\":\"$model_name\",\"modelfile\":\"$(cat /tmp/Modelfile | sed 's/$/\\n/' | tr -d '\n')\"}" \
        --max-time 600; then
        echo "✅ Successfully created optimized model '$model_name'"
        return 0
    else
        echo "❌ Failed to create optimized model '$model_name'"
        return 1
    fi
}

# Base models to install
BASE_MODELS="codegemma:instruct"

# Pull base models first
for model in $BASE_MODELS; do
    echo "🔍 Checking if base model '$model' exists..."
    if model_exists "$model"; then
        echo "✅ Base model '$model' already exists, skipping..."
    else
        echo "📥 Pulling base model '$model'..."
        
        if curl -X POST http://ollama:11434/api/pull \
            -H "Content-Type: application/json" \
            -d "{\"name\":\"$model\"}" \
            --max-time 1800; then
            echo "✅ Successfully pulled base model '$model'"
        else
            echo "❌ Failed to pull base model '$model'"
            exit 1
        fi
    fi
done

# Create optimized models
echo "🔧 Creating performance-optimized models..."

# Create optimized codegemma model
if ! model_exists "codegemma:fast"; then
    create_optimized_model "codegemma:fast" "codegemma:instruct"
else
    echo "✅ Optimized model 'codegemma:fast' already exists"
fi

# Warm up the models by running a simple inference
echo "🔥 Warming up models..."
curl -X POST http://ollama:11434/api/generate \
    -H "Content-Type: application/json" \
    -d '{"model":"codegemma:fast","prompt":"Hello, this is a warmup.","stream":false}' \
    --max-time 120 > /dev/null 2>&1 || echo "⚠️  Warmup completed with warnings"

echo "🎉 All models are ready and warmed up!"

# List available models
echo "📋 Available models:"
curl -s http://ollama:11434/api/tags | grep -o '"name":"[^"]*"' | cut -d'"' -f4

echo "✅ Ollama initialization complete!"

# Optional: Set up model preloading for faster first request
echo "🚀 Preloading optimized model into memory..."
curl -X POST http://ollama:11434/api/generate \
    -H "Content-Type: application/json" \
    -d '{"model":"codegemma:fast","prompt":"","stream":false,"options":{"num_predict":1}}' \
    --max-time 60 > /dev/null 2>&1 || echo "⚠️  Preloading completed with warnings"

echo "🎯 Model preloaded and ready for fast responses!"