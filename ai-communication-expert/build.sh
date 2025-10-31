#!/bin/bash
# build.sh

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Initializing database..."
python -c "from app.models.database import init_db; init_db()"

echo "Build complete!